import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { LoggingService } from '../logging/logging.service';
import { EventBus } from '../events/event-bus';

export interface Notification {
  type: 'email' | 'sms' | 'push';
  recipient: string;
  subject: string;
  message: string;
  metadata?: Record<string, any>;
}

@Injectable()
export class NotificationService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly eventBus: EventBus
  ) {}

  async send(notification: Notification): Promise<void> {
    try {
      // Log the notification attempt
      this.loggingService.log(
        `Sending ${notification.type} notification to ${notification.recipient}`,
        'NotificationService'
      );

      // Publish notification event
      this.eventBus.publish({
        type: 'notification.sent',
        data: notification,
        timestamp: new Date()
      });

      // Here you would implement the actual notification sending logic
      // For example, using a third-party service like SendGrid, Twilio, etc.
      
      this.loggingService.log(
        `Successfully sent ${notification.type} notification to ${notification.recipient}`,
        'NotificationService'
      );
    } catch (error) {
      this.loggingService.error(
        `Failed to send ${notification.type} notification to ${notification.recipient}`,
        error instanceof Error ? error.stack : undefined,
        'NotificationService'
      );
      throw error;
    }
  }

  async sendBatch(notifications: Notification[]): Promise<void> {
    await Promise.all(notifications.map(notification => this.send(notification)));
  }
} 