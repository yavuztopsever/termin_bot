import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const NotificationConfigSchema = BaseConfig.extend({
  smsEnabled: z.boolean(),
  emailEnabled: z.boolean(),
  pushEnabled: z.boolean(),
  smsApiKey: z.string().optional(),
  emailApiKey: z.string().optional(),
  pushApiKey: z.string().optional(),
});

export type NotificationConfig = z.infer<typeof NotificationConfigSchema>;

export interface NotificationService extends BaseService {
  notifyAppointmentBooked(appointment: unknown): Promise<void>;
  notifyAppointmentCancelled(appointment: unknown): Promise<void>;
  notifyError(error: Error, context?: Record<string, unknown>): Promise<void>;
  notifyAlert(alert: unknown): Promise<void>;
}

export interface NotificationChannel {
  send(message: string, recipient: string): Promise<void>;
}

export interface SMSChannel extends NotificationChannel {
  sendSMS(phoneNumber: string, message: string): Promise<void>;
}

export interface EmailChannel extends NotificationChannel {
  sendEmail(email: string, subject: string, body: string): Promise<void>;
}

export interface PushChannel extends NotificationChannel {
  sendPush(deviceToken: string, title: string, body: string): Promise<void>;
}

export interface NotificationTemplate {
  id: string;
  type: NotificationType;
  subject?: string;
  body: string;
  variables: string[];
}

export interface NotificationRecipient {
  id: string;
  type: NotificationChannelType;
  value: string;
  preferences?: NotificationPreferences;
}

export interface NotificationPreferences {
  sms: boolean;
  email: boolean;
  push: boolean;
  quietHours?: {
    start: string;
    end: string;
    timezone: string;
  };
}

export enum NotificationType {
  APPOINTMENT_BOOKED = 'APPOINTMENT_BOOKED',
  APPOINTMENT_CANCELLED = 'APPOINTMENT_CANCELLED',
  APPOINTMENT_REMINDER = 'APPOINTMENT_REMINDER',
  ERROR_NOTIFICATION = 'ERROR_NOTIFICATION',
  ALERT_NOTIFICATION = 'ALERT_NOTIFICATION',
  SYSTEM_NOTIFICATION = 'SYSTEM_NOTIFICATION',
}

export enum NotificationChannelType {
  SMS = 'SMS',
  EMAIL = 'EMAIL',
  PUSH = 'PUSH',
}

export interface NotificationStore {
  save(notification: Notification): Promise<void>;
  getByType(type: NotificationType): Promise<Notification[]>;
  getByDateRange(startDate: Date, endDate: Date): Promise<Notification[]>;
  clear(): Promise<void>;
}

export interface Notification {
  id: string;
  type: NotificationType;
  recipient: NotificationRecipient;
  template: NotificationTemplate;
  data: Record<string, unknown>;
  status: NotificationStatus;
  sentAt?: Date;
  error?: Error;
  metadata?: Record<string, unknown>;
}

export enum NotificationStatus {
  PENDING = 'PENDING',
  SENT = 'SENT',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
} 