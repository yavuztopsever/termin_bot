import { z } from 'zod';
import { BaseConfig, BaseService } from './base';
import { ErrorSeverity } from './error';

export const MonitoringConfigSchema = BaseConfig.extend({
  metricsEnabled: z.boolean(),
  loggingEnabled: z.boolean(),
  alertingEnabled: z.boolean(),
  retentionDays: z.number(),
  samplingRate: z.number(),
});

export type MonitoringConfig = z.infer<typeof MonitoringConfigSchema>;

export interface MonitoringService extends BaseService {
  recordMetric(name: string, value: number, tags?: Record<string, string>): void;
  recordEvent(name: string, data?: Record<string, unknown>): void;
  recordError(error: Error, context?: Record<string, unknown>): void;
  recordAlert(alert: Alert): void;
}

export interface Alert {
  id: string;
  name: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
  severity: ErrorSeverity;
  metadata?: Record<string, unknown>;
}

export interface Metric {
  name: string;
  value: number;
  timestamp: number;
  tags?: Record<string, string>;
}

export interface Event {
  name: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

export interface ErrorEvent {
  error: Error;
  timestamp: number;
  context?: Record<string, unknown>;
}

export enum MetricType {
  COUNTER = 'COUNTER',
  GAUGE = 'GAUGE',
  HISTOGRAM = 'HISTOGRAM',
  SUMMARY = 'SUMMARY',
}

export interface MetricDefinition {
  name: string;
  type: MetricType;
  description: string;
  labels?: string[];
  buckets?: number[];
  quantiles?: number[];
}

export interface AlertDefinition {
  name: string;
  description: string;
  severity: ErrorSeverity;
  condition: string;
  duration: string;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

export interface MonitoringStore {
  saveMetric(metric: Metric): Promise<void>;
  saveEvent(event: Event): Promise<void>;
  saveError(error: ErrorEvent): Promise<void>;
  saveAlert(alert: Alert): Promise<void>;
  getMetricsByDateRange(startDate: Date, endDate: Date): Promise<Metric[]>;
  getEventsByDateRange(startDate: Date, endDate: Date): Promise<Event[]>;
  getErrorsByDateRange(startDate: Date, endDate: Date): Promise<ErrorEvent[]>;
  getAlertsByDateRange(startDate: Date, endDate: Date): Promise<Alert[]>;
  clear(): Promise<void>;
} 