import { z } from 'zod';

export const LoggingConfigSchema = z.object({
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

export interface LoggingService {
  debug(message: string, context?: Record<string, unknown>): void;
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, error?: Error, context?: Record<string, unknown>): void;
  setLevel(level: LogLevel): void;
  clear(): Promise<void>;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: number;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: Error;
}

export interface LogFormatter {
  format(entry: LogEntry): string;
}

export interface LogDestination {
  write(entry: LogEntry): Promise<void>;
  clear(): Promise<void>;
}

export interface LogRotator {
  rotate(): Promise<void>;
  cleanup(): Promise<void>;
} 