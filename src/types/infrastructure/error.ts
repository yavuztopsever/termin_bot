import { z } from 'zod';

export const ErrorConfigSchema = z.object({
  enabled: z.boolean(),
  reportingEnabled: z.boolean(),
  maxErrors: z.number(),
  retentionDays: z.number(),
});

export type ErrorConfig = z.infer<typeof ErrorConfigSchema>;

export interface ErrorService {
  handle(error: Error, context?: Record<string, unknown>): Promise<void>;
  report(error: Error, context?: Record<string, unknown>): Promise<void>;
  clear(): Promise<void>;
}

export interface ErrorHandler {
  handle(error: Error, context?: Record<string, unknown>): Promise<void>;
}

export interface ErrorReporter {
  report(error: Error, context?: Record<string, unknown>): Promise<void>;
}

export interface ErrorEntry {
  id: string;
  timestamp: number;
  error: Error;
  context?: Record<string, unknown>;
  stack?: string;
}

export interface ErrorFilter {
  shouldHandle(error: Error): boolean;
}

export interface ErrorTransformer {
  transform(error: Error): Error;
}

export interface ErrorStorage {
  save(entry: ErrorEntry): Promise<void>;
  getById(id: string): Promise<ErrorEntry | null>;
  getByDateRange(startDate: Date, endDate: Date): Promise<ErrorEntry[]>;
  clear(): Promise<void>;
} 