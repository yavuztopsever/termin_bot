import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../../config/config.service';
import { LoggingService } from '../../../services/common/logging.service';
import { MonitoringService } from '../../../services/monitoring/monitoring.service';
import { UseCase, UseCaseContext, UseCaseResult, UseCaseError } from '../../../types/common/use-case';
import { AppointmentRepository } from '../../../types/appointment/appointment.repository';
import { Appointment } from '../../../types/appointment/appointment';
import { EventBus } from '../../../types/common/domain-event';
import { AppointmentCreatedEvent } from '../../../types/appointment/appointment.events';

export interface CreateAppointmentInput {
  type: string;
  time: Date;
  context: UseCaseContext;
}

@Injectable()
export class CreateAppointmentUseCase implements UseCase<CreateAppointmentInput, UseCaseResult<Appointment>> {
  constructor(
    private readonly appointmentRepository: AppointmentRepository,
    private readonly eventBus: EventBus,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {}

  async execute(input: CreateAppointmentInput): Promise<UseCaseResult<Appointment>> {
    try {
      const startTime = Date.now();
      const { type, time, context } = input;

      this.loggingService.info('Creating appointment', { input });

      // Create appointment
      const appointment = new Appointment(
        crypto.randomUUID(),
        type,
        time,
        'AVAILABLE',
        {
          userId: context.userId,
          ...context.metadata
        }
      );

      // Save appointment
      await this.appointmentRepository.save(appointment);

      // Publish event
      await this.eventBus.publish(new AppointmentCreatedEvent(appointment));

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric({
        name: 'use_case_create_appointment_duration',
        value: duration,
        timestamp: new Date()
      });

      return {
        success: true,
        data: appointment
      };
    } catch (error) {
      this.loggingService.error('Failed to create appointment', {
        input,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric({
        name: 'use_case_create_appointment_error',
        value: 1,
        timestamp: new Date()
      });

      return {
        success: false,
        error: new UseCaseError(
          'Failed to create appointment',
          'CREATE_APPOINTMENT_ERROR',
          { input }
        )
      };
    }
  }
} 