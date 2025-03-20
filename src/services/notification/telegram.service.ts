import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../common/logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';

@Injectable()
export class TelegramService {
  private readonly botToken: string;
  private readonly apiUrl: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {
    this.botToken = this.configService.get('TELEGRAM_BOT_TOKEN');
    this.apiUrl = `https://api.telegram.org/bot${this.botToken}`;
  }

  async sendMessage(chatId: string, message: string): Promise<void> {
    try {
      const startTime = Date.now();
      const response = await fetch(`${this.apiUrl}/sendMessage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chat_id: chatId,
          text: message,
          parse_mode: 'HTML'
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric(
        'telegram_message_sent_duration',
        duration,
        { chatId }
      );
    } catch (error) {
      this.loggingService.error('Failed to send Telegram message', {
        chatId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric(
        'telegram_message_error',
        1,
        { chatId }
      );

      throw error;
    }
  }

  async sendAppointmentNotification(chatId: string, appointment: any): Promise<void> {
    const message = this.formatAppointmentMessage(appointment);
    await this.sendMessage(chatId, message);
  }

  private formatAppointmentMessage(appointment: any): string {
    return `
<b>🎉 Appointment Available!</b>

📅 Date: ${new Date(appointment.time).toLocaleDateString()}
🕒 Time: ${new Date(appointment.time).toLocaleTimeString()}
📋 Type: ${appointment.type}
🏢 Office: ${appointment.metadata.officeId || 'N/A'}

<a href="${appointment.metadata.bookingUrl}">Click here to book</a>
    `.trim();
  }
} 