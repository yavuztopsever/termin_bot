import { Injectable } from '@nestjs/common';
import { LoggingService } from '../../../services/common/logging.service';
import { MonitoringService } from '../../../services/monitoring/monitoring.service';
import { UseCase, UseCaseContext, UseCaseResult, UseCaseError } from '../../../types/common/use-case';
import { AppointmentRepository } from '../../../types/appointment/appointment.repository';
import { Appointment } from '../../../types/appointment/appointment';
import { EventBus } from '../../../types/common/domain-event';
import { AppointmentCancelledEvent } from '../../../types/appointment/appointment.events';

export interface CancelAppointmentInput {
  appointmentId: string;
  userId: string;
  reason?: string;
  context: UseCaseContext;
}

@Injectable()
export class CancelAppointmentUseCase implements UseCase<CancelAppointmentInput, UseCaseResult<Appointment>> {
  constructor(
    private readonly appointmentRepository: AppointmentRepository,
    private readonly eventBus: EventBus,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {}

  async execute(input: CancelAppointmentInput): Promise<UseCaseResult<Appointment>> {
    try {
      const startTime = Date.now();
      const { appointmentId, userId, reason, context } = input;

      this.loggingService.info('Cancelling appointment', { input });

      // Find appointment
      const appointment = await this.appointmentRepository.findById(appointmentId);
      if (!appointment) {
        return {
          success: false,
          error: new UseCaseError(
            'Appointment not found',
            'APPOINTMENT_NOT_FOUND',
            { appointmentId }
          )
        };
      }

      // Validate appointment status
      if (appointment.status !== 'BOOKED') {
        return {
          success: false,
          error: new UseCaseError(
            'Appointment is not booked',
            'INVALID_APPOINTMENT_STATUS',
            { appointmentId, status: appointment.status }
          )
        };
      }

      // Validate user ownership
      if (appointment.metadata.bookedBy !== userId) {
        return {
          success: false,
          error: new UseCaseError(
            'User is not authorized to cancel this appointment',
            'UNAUTHORIZED_CANCELLATION',
            { appointmentId, userId }
          )
        };
      }

      // Update appointment status
      appointment.status = 'CANCELLED';
      appointment.metadata = {
        ...appointment.metadata,
        cancelledBy: userId,
        cancelledAt: new Date().toISOString(),
        cancellationReason: reason
      };

      // Save appointment
      await this.appointmentRepository.save(appointment);

      // Publish event
      await this.eventBus.publish(new AppointmentCancelledEvent(appointment));

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric({
        name: 'use_case_cancel_appointment_duration',
        value: duration,
        timestamp: new Date()
      });

      return {
        success: true,
        data: appointment
      };
    } catch (error) {
      this.loggingService.error('Failed to cancel appointment', {
        input,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric({
        name: 'use_case_cancel_appointment_error',
        value: 1,
        timestamp: new Date()
      });

      return {
        success: false,
        error: new UseCaseError(
          'Failed to cancel appointment',
          'CANCEL_APPOINTMENT_ERROR',
          { input }
        )
      };
    }
  }
} 