import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const PersistenceConfigSchema = BaseConfig.extend({
  type: z.enum(['memory', 'redis', 'database']),
  connectionString: z.string(),
  maxConnections: z.number(),
});

export type PersistenceConfig = z.infer<typeof PersistenceConfigSchema>;

export interface PersistenceService extends BaseService {
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

export interface PersistenceTransaction {
  begin(): Promise<void>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
  isActive(): boolean;
}

export interface PersistenceQuery<T> {
  where(condition: Record<string, unknown>): PersistenceQuery<T>;
  orderBy(field: string, direction: 'asc' | 'desc'): PersistenceQuery<T>;
  limit(count: number): PersistenceQuery<T>;
  offset(count: number): PersistenceQuery<T>;
  execute(): Promise<T[]>;
}

export interface PersistenceRepository<T> {
  findById(id: string): Promise<T | null>;
  findOne(condition: Record<string, unknown>): Promise<T | null>;
  find(condition: Record<string, unknown>): Promise<T[]>;
  create(data: T): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
  count(condition: Record<string, unknown>): Promise<number>;
  exists(condition: Record<string, unknown>): Promise<boolean>;
}

export interface PersistenceMigration {
  version: number;
  up(): Promise<void>;
  down(): Promise<void>;
}

export interface PersistenceSeeder {
  seed(): Promise<void>;
  clear(): Promise<void>;
}

export interface PersistenceIndex {
  name: string;
  fields: string[];
  unique?: boolean;
  sparse?: boolean;
}

export interface PersistenceSchema<T> {
  name: string;
  fields: Record<string, unknown>;
  indexes?: PersistenceIndex[];
  timestamps?: boolean;
  versioning?: boolean;
} 