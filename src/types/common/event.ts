import { z } from 'zod';
import { BaseMetadata } from './base';

export const EventSchema = z.object({
  id: z.string(),
  type: z.string(),
  timestamp: z.number(),
  data: z.unknown(),
  metadata: z.object({
    timestamp: z.number(),
    source: z.string(),
    correlationId: z.string().optional(),
    userId: z.string().optional(),
    metadata: z.record(z.unknown()).optional(),
  }),
});

export type Event<T = unknown> = z.infer<typeof EventSchema> & {
  data: T;
};

export type EventHandler<T = unknown> = (event: Event<T>) => Promise<void>;

export interface EventBus {
  publish<T>(event: Event<T>): Promise<void>;
  subscribe<T>(eventType: string, handler: EventHandler<T>): void;
  unsubscribe(eventType: string, handler: EventHandler<unknown>): void;
  clear(): Promise<void>;
}

export interface EventStore {
  save(event: Event<unknown>): Promise<void>;
  getByType(type: string): Promise<Event<unknown>[]>;
  getByDateRange(startDate: Date, endDate: Date): Promise<Event<unknown>[]>;
  clear(): Promise<void>;
}

export interface EventPublisher {
  publish<T>(event: Event<T>): Promise<void>;
}

export interface EventSubscriber {
  subscribe<T>(eventType: string, handler: EventHandler<T>): void;
  unsubscribe(eventType: string, handler: EventHandler<unknown>): void;
}

export interface EventConfig {
  enabled: boolean;
  persistenceEnabled: boolean;
  maxEvents: number;
  retentionDays: number;
}

export enum EventType {
  APPOINTMENT_BOOKED = 'APPOINTMENT_BOOKED',
  APPOINTMENT_CANCELLED = 'APPOINTMENT_CANCELLED',
  APPOINTMENT_AVAILABLE = 'APPOINTMENT_AVAILABLE',
  ERROR_OCCURRED = 'ERROR_OCCURRED',
  ALERT_CREATED = 'ALERT_CREATED',
  METRIC_RECORDED = 'METRIC_RECORDED',
  STATE_CHANGED = 'STATE_CHANGED',
  VALIDATION_FAILED = 'VALIDATION_FAILED',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  COORDINATION_STARTED = 'COORDINATION_STARTED',
  COORDINATION_COMPLETED = 'COORDINATION_COMPLETED',
  COORDINATION_FAILED = 'COORDINATION_FAILED',
} 