import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from './logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';

@Injectable()
export class NotificationService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
  ) {}

  async notifySuccess(message: string, context?: Record<string, any>): Promise<void> {
    try {
      this.loggingService.info(message, context);
      this.monitoringService.recordMetric({
        name: 'notification_sent',
        value: 1,
        timestamp: new Date(),
        tags: { type: 'success' },
      });
    } catch (error) {
      this.loggingService.error('Failed to send success notification', {
        error,
        message,
        context,
      });
    }
  }

  async notifyWarning(message: string, context?: Record<string, any>): Promise<void> {
    try {
      this.loggingService.warn(message, context);
      this.monitoringService.recordMetric({
        name: 'notification_sent',
        value: 1,
        timestamp: new Date(),
        tags: { type: 'warning' },
      });
    } catch (error) {
      this.loggingService.error('Failed to send warning notification', {
        error,
        message,
        context,
      });
    }
  }

  async notifyError(message: string, context?: Record<string, any>): Promise<void> {
    try {
      this.loggingService.error(message, context);
      this.monitoringService.recordMetric({
        name: 'notification_sent',
        value: 1,
        timestamp: new Date(),
        tags: { type: 'error' },
      });
    } catch (error) {
      this.loggingService.error('Failed to send error notification', {
        error,
        message,
        context,
      });
    }
  }

  async notifyBookingSuccess(bookingDetails: Record<string, any>): Promise<void> {
    try {
      const message = `Booking successful: ${JSON.stringify(bookingDetails)}`;
      await this.notifySuccess(message, bookingDetails);
    } catch (error) {
      this.loggingService.error('Failed to send booking success notification', {
        error,
        bookingDetails,
      });
    }
  }

  async notifyBookingFailure(error: Error, context?: Record<string, any>): Promise<void> {
    try {
      const message = `Booking failed: ${error.message}`;
      await this.notifyError(message, {
        error: error.message,
        stack: error.stack,
        ...context,
      });
    } catch (notifyError) {
      this.loggingService.error('Failed to send booking failure notification', {
        error: notifyError,
        originalError: error,
        context,
      });
    }
  }

  async notifyAvailabilityFound(availability: Record<string, any>): Promise<void> {
    try {
      const message = `Availability found: ${JSON.stringify(availability)}`;
      await this.notifySuccess(message, availability);
    } catch (error) {
      this.loggingService.error('Failed to send availability notification', {
        error,
        availability,
      });
    }
  }

  async notifyRateLimitExceeded(context?: Record<string, any>): Promise<void> {
    try {
      const message = 'Rate limit exceeded';
      await this.notifyWarning(message, context);
    } catch (error) {
      this.loggingService.error('Failed to send rate limit notification', {
        error,
        context,
      });
    }
  }

  async notifyServiceHealth(health: Record<string, any>): Promise<void> {
    try {
      const message = `Service health status: ${JSON.stringify(health)}`;
      await this.notifySuccess(message, health);
    } catch (error) {
      this.loggingService.error('Failed to send health notification', {
        error,
        health,
      });
    }
  }
} 