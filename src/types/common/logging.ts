import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const LoggingConfigSchema = BaseConfig.extend({
  level: z.enum(['debug', 'info', 'warn', 'error']),
  format: z.enum(['json', 'text']),
  destination: z.enum(['console', 'file', 'remote']),
  filePath: z.string().optional(),
  remoteUrl: z.string().url().optional(),
  maxSize: z.number().optional(),
  maxFiles: z.number().optional(),
  retentionDays: z.number().optional(),
});

export type LoggingConfig = z.infer<typeof LoggingConfigSchema>;

export interface LoggingService extends BaseService {
  debug(message: string, context?: Record<string, unknown>): void;
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, error?: Error, context?: Record<string, unknown>): void;
  setLevel(level: LogLevel): void;
  clear(): Promise<void>;
}

export const LogLevelSchema = z.enum(['debug', 'info', 'warn', 'error', 'fatal']);

export type LogLevel = z.infer<typeof LogLevelSchema>;

export const LogContextSchema = z.object({
  timestamp: z.string().datetime(),
  level: LogLevelSchema,
  message: z.string(),
  context: z.record(z.unknown()).optional(),
  error: z.object({
    name: z.string(),
    message: z.string(),
    stack: z.string().optional(),
    cause: z.unknown().optional(),
  }).optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type LogContext = z.infer<typeof LogContextSchema>;

export interface Logger {
  debug(message: string, context?: Record<string, unknown>): void;
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, error?: Error, context?: Record<string, unknown>): void;
  fatal(message: string, error?: Error, context?: Record<string, unknown>): void;
  
  child(context: Record<string, unknown>): Logger;
  
  setLevel(level: LogLevel): void;
  getLevel(): LogLevel;
  
  isDebugEnabled(): boolean;
  isInfoEnabled(): boolean;
  isWarnEnabled(): boolean;
  isErrorEnabled(): boolean;
  isFatalEnabled(): boolean;
}

export interface LogHandler {
  handle(log: LogContext): Promise<void>;
  setLevel(level: LogLevel): void;
  getLevel(): LogLevel;
  isEnabled(level: LogLevel): boolean;
}

export interface LogFormatter {
  format(log: LogContext): string;
}

export interface LogTransport {
  write(log: LogContext): Promise<void>;
  close(): Promise<void>;
}

export interface LogConfig {
  level: LogLevel;
  format: 'json' | 'text';
  transports: Array<{
    type: 'console' | 'file' | 'http' | 'elasticsearch';
    options: Record<string, unknown>;
  }>;
  context: Record<string, unknown>;
  errorStack: boolean;
  timestamp: boolean;
  pretty: boolean;
  maxSize: number;
  maxFiles: number;
  rotation: boolean;
  compression: boolean;
  retry: {
    maxRetries: number;
    retryDelay: number;
  };
}

export interface LogEntry {
  timestamp: number;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: Error;
}

export interface LogDestination {
  write(entry: LogEntry): Promise<void>;
  clear(): Promise<void>;
}

export interface LogRotator {
  rotate(): Promise<void>;
  cleanup(): Promise<void>;
}

export interface LogStore {
  save(entry: LogEntry): Promise<void>;
  getByLevel(level: LogLevel): Promise<LogEntry[]>;
  getByDateRange(startDate: Date, endDate: Date): Promise<LogEntry[]>;
  clear(): Promise<void>;
}

export interface LogMetadata {
  timestamp: number;
  level: LogLevel;
  context: LogContext;
}

export interface LogOptions {
  level?: LogLevel;
  context?: LogContext;
  error?: Error;
  metadata?: Record<string, unknown>;
} 