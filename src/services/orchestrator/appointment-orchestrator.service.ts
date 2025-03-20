import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../common/logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { AIAgentService } from '../ai/ai-agent.service';
import { TelegramService } from '../notification/telegram.service';
import { FindAvailableAppointmentsUseCase } from '../../core/appointment/use-cases/find-available-appointments.use-case';
import { BookAppointmentUseCase } from '../../core/appointment/use-cases/book-appointment.use-case';
import { AppointmentConfig } from '../../types/appointment/appointment-config';

@Injectable()
export class AppointmentOrchestratorService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
    private readonly aiAgentService: AIAgentService,
    private readonly telegramService: TelegramService,
    private readonly findAvailableAppointmentsUseCase: FindAvailableAppointmentsUseCase,
    private readonly bookAppointmentUseCase: BookAppointmentUseCase
  ) {}

  async startMonitoring(config: AppointmentConfig): Promise<void> {
    try {
      const startTime = Date.now();
      this.loggingService.info('Starting appointment monitoring', { config });

      // Analyze and update configuration using AI agent
      await this.aiAgentService.analyzeAndUpdateConfig(config.url);

      // Find available appointments
      const result = await this.findAvailableAppointmentsUseCase.execute({
        startDate: new Date(),
        endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
        type: config.type,
        context: {
          userId: config.id,
          metadata: {
            url: config.url,
            ...config.metadata
          }
        }
      });

      if (result.success && result.data) {
        // Send notifications for available appointments
        for (const appointment of result.data) {
          await this.telegramService.sendAppointmentNotification(
            config.id,
            appointment
          );
        }

        // Attempt to book the first available appointment
        if (result.data.length > 0) {
          const bookingResult = await this.bookAppointmentUseCase.execute({
            appointmentId: result.data[0].id,
            userId: config.id,
            context: {
              userId: config.id,
              metadata: {
                url: config.url,
                ...config.metadata
              }
            }
          });

          if (bookingResult.success) {
            await this.telegramService.sendMessage(
              config.id,
              `✅ Successfully booked appointment for ${new Date(bookingResult.data.time).toLocaleString()}`
            );
          }
        }
      }

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric(
        'appointment_monitoring_duration',
        duration,
        { configId: config.id }
      );
    } catch (error) {
      this.loggingService.error('Appointment monitoring failed', {
        config,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric(
        'appointment_monitoring_error',
        1,
        { configId: config.id }
      );

      throw error;
    }
  }
} 