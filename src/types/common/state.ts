import { z } from 'zod';
import { BaseConfig, BaseService } from './base';
import { Alert } from './monitoring';

export const StateConfigSchema = BaseConfig.extend({
  persistenceEnabled: z.boolean(),
  storageType: z.enum(['memory', 'redis', 'database']),
  ttl: z.number(),
  maxSize: z.number(),
});

export type StateConfig = z.infer<typeof StateConfigSchema>;

export interface StateService extends BaseService {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
  addAlert(alert: Alert): void;
  getAlerts(): Alert[];
  clearAlerts(): void;
}

export interface StateStore {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
}

export interface StatePersistence {
  save(): Promise<void>;
  load(): Promise<void>;
  clear(): Promise<void>;
}

export interface StateSnapshot {
  timestamp: number;
  data: Record<string, unknown>;
  alerts: Alert[];
}

export interface StateChange<T = unknown> {
  key: string;
  oldValue: T | null;
  newValue: T | null;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface StateObserver<T = unknown> {
  onStateChange(change: StateChange<T>): void;
}

export interface StateSubscription {
  unsubscribe(): void;
}

export interface StateManager {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
  subscribe<T>(key: string, observer: StateObserver<T>): StateSubscription;
  unsubscribe(subscription: StateSubscription): void;
}

export interface StateValidator<T> {
  validate(value: T): boolean;
  message?: string;
}

export interface StateTransformer<T> {
  transform(value: T): T;
}

export interface StateOptions {
  ttl?: number;
  maxSize?: number;
  validate?: boolean;
  transform?: boolean;
  persist?: boolean;
  metadata?: Record<string, unknown>;
}

export const StateDataSchema = z.object({
  id: z.string().uuid(),
  type: z.string(),
  data: z.record(z.unknown()),
  timestamp: z.number(),
  metadata: z.record(z.unknown()).optional(),
  version: z.number().default(1),
});

export type StateData<T = unknown> = z.infer<typeof StateDataSchema> & {
  data: T;
};

export interface StateOperation<T = unknown> {
  type: 'set' | 'get' | 'delete' | 'update';
  key: string;
  data?: T;
  options?: StateOptions;
}

export interface StateObserver<T = unknown> {
  onStateChange: (key: string, newValue: T | null, oldValue: T | null) => Promise<void>;
}

export interface StateSubscription {
  unsubscribe: () => void;
}

export interface StateManager {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, options?: StateOptions): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
  subscribe<T>(key: string, observer: StateObserver<T>): StateSubscription;
  unsubscribe(subscription: StateSubscription): void;
  getKeys(): Promise<string[]>;
  getSize(): Promise<number>;
  getMetadata<T>(key: string): Promise<Record<string, unknown> | null>;
  setMetadata<T>(key: string, metadata: Record<string, unknown>): Promise<void>;
  getVersion(key: string): Promise<number>;
  incrementVersion(key: string): Promise<number>;
}

export interface StateStore {
  save<T>(key: string, data: StateData<T>): Promise<void>;
  load<T>(key: string): Promise<StateData<T> | null>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  getKeys(): Promise<string[]>;
  getSize(): Promise<number>;
}

export interface StateCache {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
} 