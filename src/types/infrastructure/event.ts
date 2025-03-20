import { z } from 'zod';

export const EventConfigSchema = z.object({
  enabled: z.boolean(),
  persistenceEnabled: z.boolean(),
  maxEvents: z.number(),
  retentionDays: z.number(),
});

export type EventConfig = z.infer<typeof EventConfigSchema>;

export interface EventBus {
  publish<T>(event: Event<T>): Promise<void>;
  subscribe<T>(eventType: string, handler: EventHandler<T>): void;
  unsubscribe(eventType: string, handler: EventHandler<unknown>): void;
  clear(): Promise<void>;
}

export interface Event<T = unknown> {
  id: string;
  type: string;
  timestamp: number;
  data: T;
  metadata?: Record<string, unknown>;
}

export type EventHandler<T = unknown> = (event: Event<T>) => Promise<void>;

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