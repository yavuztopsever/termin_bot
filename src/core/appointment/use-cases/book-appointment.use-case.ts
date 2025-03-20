import { Injectable } from '@nestjs/common';
import { LoggingService } from '../../../services/common/logging.service';
import { MonitoringService } from '../../../services/monitoring/monitoring.service';
import { UseCase, UseCaseContext, UseCaseResult, UseCaseError } from '../../../types/common/use-case';
import { AppointmentRepository } from '../../../types/appointment/appointment.repository';
import { Appointment } from '../../../types/appointment/appointment';
import { EventBus } from '../../../types/common/domain-event';
import { AppointmentBookedEvent } from '../../../types/appointment/appointment.events';
import { validateBookingRequest, createBookingResult } from '../booking.utils';

export interface BookAppointmentInput {
  appointmentId: string;
  userId: string;
  context: UseCaseContext;
}

@Injectable()
export class BookAppointmentUseCase implements UseCase<BookAppointmentInput, UseCaseResult<Appointment>> {
  constructor(
    private readonly appointmentRepository: AppointmentRepository,
    private readonly eventBus: EventBus,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {}

  async execute(input: BookAppointmentInput): Promise<UseCaseResult<Appointment>> {
    try {
      const startTime = Date.now();
      const { appointmentId, userId, context } = input;

      this.loggingService.info('Booking appointment', { input });

      // Find appointment
      const appointment = await this.appointmentRepository.findById(appointmentId);
      if (!appointment) {
        return createBookingResult(false, 'Appointment not found');
      }

      // Validate appointment status
      if (appointment.status !== 'AVAILABLE') {
        return createBookingResult(false, 'Appointment is not available');
      }

      // Validate booking request
      const bookingRequest = {
        date: appointment.time.toISOString().split('T')[0],
        time: appointment.time.toISOString().split('T')[1].slice(0, 5),
        userId
      };

      if (!validateBookingRequest(bookingRequest)) {
        return createBookingResult(false, 'Invalid booking request');
      }

      // Update appointment status
      appointment.status = 'BOOKED';
      appointment.metadata = {
        ...appointment.metadata,
        bookedBy: userId,
        bookedAt: new Date().toISOString()
      };

      // Save appointment
      await this.appointmentRepository.save(appointment);

      // Publish event
      await this.eventBus.publish(new AppointmentBookedEvent(appointment));

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric({
        name: 'use_case_book_appointment_duration',
        value: duration,
        timestamp: new Date()
      });

      return createBookingResult(true, 'Appointment booked successfully', appointment);
    } catch (error) {
      this.loggingService.error('Failed to book appointment', {
        input,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric({
        name: 'use_case_book_appointment_error',
        value: 1,
        timestamp: new Date()
      });

      return {
        success: false,
        error: new UseCaseError(
          'Failed to book appointment',
          'BOOK_APPOINTMENT_ERROR',
          { input }
        )
      };
    }
  }
} 