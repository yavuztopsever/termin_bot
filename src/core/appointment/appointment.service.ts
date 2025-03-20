import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../../services/common/logging.service';
import { MonitoringService } from '../../services/monitoring/monitoring.service';
import { BrowserService } from '../browser/browser.service';
import { PageAnalyzerService } from '../page-analyzer/page-analyzer.service';
import { NotificationService } from '../../services/common/notification.service';
import { AppointmentConfig } from '../../types/appointment/appointment-config';
import { AppointmentType } from '../../types/appointment/appointment-type';
import { AppointmentStatus } from '../../types/appointment/appointment-status';
import { PageAnalysisResult } from '../../types/page-analyzer/page-analysis-result';

@Injectable()
export class AppointmentService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
    private readonly browserService: BrowserService,
    private readonly pageAnalyzerService: PageAnalyzerService,
    private readonly notificationService: NotificationService,
  ) {}

  async processAppointment(config: AppointmentConfig): Promise<void> {
    try {
      this.loggingService.info('Starting appointment processing', { config });
      
      await this.browserService.initialize();
      const page = await this.browserService.navigate(config.url);
      
      const analysis = await this.pageAnalyzerService.analyzeAppointmentPage(page);
      
      if (analysis.available) {
        await this.updateAppointmentStatus(config.id, AppointmentStatus.BOOKED);
        
        await this.notificationService.sendNotification({
          type: 'appointment_processed',
          message: 'Appointment successfully booked',
          data: {
            appointmentId: config.id,
            date: analysis.nextAvailableDate
          }
        });
      } else {
        await this.updateAppointmentStatus(config.id, AppointmentStatus.PENDING, config.retryCount + 1);
      }
    } catch (error) {
      this.loggingService.error('Failed to process appointment', { config, error });
      await this.updateAppointmentStatus(config.id, AppointmentStatus.FAILED, config.retryCount + 1, error.message);
      throw error;
    } finally {
      await this.browserService.close();
    }
  }

  async scheduleAppointment(config: AppointmentConfig): Promise<PageAnalysisResult> {
    try {
      this.loggingService.info('Starting appointment scheduling', { config });
      
      const result = await this.pageAnalyzerService.findAvailableSlots(config);
      
      this.monitoringService.recordMetric({
        name: 'appointment_scheduling_completed',
        value: 1,
        timestamp: new Date(),
        tags: { success: result.success.toString() }
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to schedule appointment', { config, error });
      this.monitoringService.recordError('appointment_scheduling_failed', error);
      throw error;
    }
  }

  async checkAvailability(config: AppointmentConfig): Promise<PageAnalysisResult> {
    try {
      this.loggingService.info('Checking appointment availability', { config });
      
      const result = await this.pageAnalyzerService.checkAvailability(config);
      
      this.monitoringService.recordMetric({
        name: 'appointment_availability_check_completed',
        value: 1,
        timestamp: new Date(),
        tags: { available: result.available.toString() }
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to check appointment availability', { config, error });
      this.monitoringService.recordError('appointment_availability_check_failed', error);
      throw error;
    }
  }

  private async updateAppointmentStatus(
    id: string,
    status: AppointmentStatus,
    retryCount?: number,
    error?: string
  ): Promise<void> {
    // Implementation will be added when we create the appointment repository
    this.loggingService.info('Updating appointment status', { id, status, retryCount, error });
  }
} 