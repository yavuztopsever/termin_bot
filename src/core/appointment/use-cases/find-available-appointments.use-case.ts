import { Injectable } from '@nestjs/common';
import type { LoggingService } from '../../../services/common/logging.service';
import type { MonitoringService } from '../../../services/monitoring/monitoring.service';
import { UseCase, UseCaseContext, UseCaseResult } from '../../../types/common/use-case';
import type { AppointmentRepository } from '../../../types/appointment/appointment.repository';
import { Appointment } from '../../../types/appointment/appointment';
import { isBookingAvailable } from '../booking.utils';

export interface FindAvailableAppointmentsInput {
  startDate: Date;
  endDate: Date;
  type?: string;
  context: UseCaseContext;
}

export class UseCaseError {
  constructor(
    public readonly message: string,
    public readonly code: string,
    public readonly details?: Record<string, any>
  ) {}
}

@Injectable()
export class FindAvailableAppointmentsUseCase implements UseCase<FindAvailableAppointmentsInput, UseCaseResult<Appointment[]>> {
  constructor(
    private readonly appointmentRepository: AppointmentRepository,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {}

  async execute(input: FindAvailableAppointmentsInput): Promise<UseCaseResult<Appointment[]>> {
    try {
      const startTime = Date.now();
      const { startDate, endDate, type, context } = input;

      this.loggingService.info('Finding available appointments', { input });

      // Find appointments in date range
      const appointments = await this.appointmentRepository.findByDateRange(startDate, endDate);

      // Filter available appointments
      const availableAppointments = appointments.filter(appointment => {
        // Check if appointment is available
        if (appointment.status !== 'AVAILABLE') {
          return false;
        }

        // Check appointment type if specified
        if (type && appointment.type !== type) {
          return false;
        }

        // Check if booking is available
        const date = appointment.time.toISOString().split('T')[0];
        const time = appointment.time.toISOString().split('T')[1].slice(0, 5);
        return isBookingAvailable(date, time);
      });

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric(
        'use_case_find_available_appointments_duration',
        duration,
        { timestamp: new Date() }
      );

      return {
        success: true,
        data: availableAppointments
      };
    } catch (error) {
      this.loggingService.error('Failed to find available appointments', {
        input,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric(
        'use_case_find_available_appointments_error',
        1,
        { timestamp: new Date() }
      );

      return {
        success: false,
        error: new UseCaseError(
          'Failed to find available appointments',
          'FIND_AVAILABLE_APPOINTMENTS_ERROR',
          { input }
        )
      };
    }
  }
} 