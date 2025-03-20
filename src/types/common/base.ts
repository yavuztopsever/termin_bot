import { z } from 'zod';

export const BaseConfigSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().optional(),
  version: z.string(),
  environment: z.enum(['development', 'production', 'test']),
  debug: z.boolean().default(false),
  logLevel: z.enum(['debug', 'info', 'warn', 'error', 'fatal']).default('info'),
  timeout: z.number().positive().default(30000),
  retry: z.object({
    maxRetries: z.number().nonnegative().default(3),
    retryDelay: z.number().positive().default(1000),
  }).default({}),
  cache: z.object({
    enabled: z.boolean().default(false),
    ttl: z.number().positive().default(3600),
    maxSize: z.number().positive().default(1000),
  }).default({}),
  security: z.object({
    enabled: z.boolean().default(true),
    cors: z.boolean().default(true),
    rateLimit: z.boolean().default(true),
    rateLimitWindow: z.number().positive().default(900000),
    rateLimitMax: z.number().positive().default(100),
  }).default({}),
  monitoring: z.object({
    enabled: z.boolean().default(false),
    metrics: z.boolean().default(false),
    tracing: z.boolean().default(false),
    profiling: z.boolean().default(false),
  }).default({}),
  metadata: z.record(z.unknown()).optional(),
});

export type BaseConfig = z.infer<typeof BaseConfigSchema>;

export interface BaseService {
  id: string;
  name: string;
  version: string;
  config: BaseConfig;
  start(): Promise<void>;
  stop(): Promise<void>;
  health(): Promise<{
    status: 'healthy' | 'unhealthy';
    details?: Record<string, unknown>;
  }>;
  metrics(): Promise<Record<string, unknown>>;
}

export interface BaseRepository<T> {
  findById(id: string): Promise<T | null>;
  findAll(options?: {
    limit?: number;
    offset?: number;
    sort?: Record<string, 'asc' | 'desc'>;
    filter?: Record<string, unknown>;
  }): Promise<T[]>;
  create(data: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
  count(filter?: Record<string, unknown>): Promise<number>;
  exists(id: string): Promise<boolean>;
}

export interface BaseCache<T> {
  get(key: string): Promise<T | null>;
  set(key: string, value: T, ttl?: number): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
  keys(): Promise<string[]>;
  size(): Promise<number>;
}

export interface BaseValidator<T> {
  validate(data: unknown): Promise<T>;
  validatePartial(data: unknown): Promise<Partial<T>>;
  validateArray(data: unknown[]): Promise<T[]>;
  validateObject(data: Record<string, unknown>): Promise<T>;
  isValid(data: unknown): Promise<boolean>;
  getErrors(data: unknown): Promise<Array<{
    path: string[];
    message: string;
    code: string;
  }>>;
}

export interface BaseEventEmitter {
  on(event: string, listener: (...args: unknown[]) => void): void;
  off(event: string, listener: (...args: unknown[]) => void): void;
  once(event: string, listener: (...args: unknown[]) => void): void;
  emit(event: string, ...args: unknown[]): void;
  removeAllListeners(event?: string): void;
  listenerCount(event: string): number;
  listeners(event: string): Array<(...args: unknown[]) => void>;
  eventNames(): string[];
}

export interface BaseError extends Error {
  code: string;
  retryable: boolean;
  context?: Record<string, unknown>;
}

export interface BaseMetadata {
  timestamp: number;
  source: string;
  correlationId?: string;
  userId?: string;
  metadata?: Record<string, unknown>;
}

export interface BaseResult<T> {
  success: boolean;
  data?: T;
  error?: BaseError;
  metadata?: BaseMetadata;
} 