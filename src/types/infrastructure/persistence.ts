import { z } from 'zod';

export const PersistenceConfigSchema = z.object({
  type: z.enum(['memory', 'redis', 'database']),
  connectionString: z.string(),
  maxConnections: z.number(),
  timeout: z.number(),
  retries: z.number(),
});

export type PersistenceConfig = z.infer<typeof PersistenceConfigSchema>;

export interface PersistenceService {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
}

export interface PersistenceStore {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
}

export interface PersistenceConnection {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;
}

export interface PersistenceError extends Error {
  code: 'PERSISTENCE_ERROR';
  retryable: boolean;
  context?: Record<string, unknown>;
}

export interface PersistenceTransaction {
  begin(): Promise<void>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
  isActive(): boolean;
} 