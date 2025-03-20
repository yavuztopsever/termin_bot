import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

export const DomainEventSchema = z.object({
  id: z.string().uuid(),
  type: z.string(),
  timestamp: z.number(),
  data: z.record(z.unknown()),
  metadata: z.record(z.unknown()).optional(),
  version: z.number().default(1),
  source: z.string().optional(),
  correlationId: z.string().uuid().optional(),
  causationId: z.string().uuid().optional(),
});

export type DomainEventType<T = unknown> = z.infer<typeof DomainEventSchema> & {
  data: T;
};

export abstract class DomainEvent<T = unknown> implements DomainEventType<T> {
  public readonly id: string;
  public readonly timestamp: number;
  public readonly version: number;
  public readonly correlationId?: string;
  public readonly causationId?: string;
  public readonly source?: string;
  public readonly metadata?: Record<string, unknown>;

  constructor(
    public readonly type: string,
    public readonly data: T,
    metadata?: Record<string, unknown>
  ) {
    this.id = uuidv4();
    this.timestamp = Date.now();
    this.version = 1;
    this.metadata = metadata;
  }
}

export interface DomainEventPublisher {
  publish<T>(event: DomainEventType<T>): Promise<void>;
  publishBatch<T>(events: DomainEventType<T>[]): Promise<void>;
}

export interface DomainEventSubscriber {
  subscribe<T>(eventType: string, handler: (event: DomainEventType<T>) => Promise<void>): void;
  unsubscribe(eventType: string, handler: (event: DomainEventType) => Promise<void>): void;
}

export interface DomainEventBus extends DomainEventPublisher, DomainEventSubscriber {
  start(): Promise<void>;
  stop(): Promise<void>;
}

export interface DomainEventStore {
  save<T>(event: DomainEventType<T>): Promise<void>;
  saveBatch<T>(events: DomainEventType<T>[]): Promise<void>;
  get<T>(eventId: string): Promise<DomainEventType<T> | null>;
  getByType<T>(eventType: string, options?: { limit?: number; offset?: number }): Promise<DomainEventType<T>[]>;
  getByAggregateId(aggregateId: string, options?: { limit?: number; offset?: number }): Promise<DomainEventType[]>;
} 