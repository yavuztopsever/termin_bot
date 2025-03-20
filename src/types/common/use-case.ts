import { z } from 'zod';

export const UseCaseContextSchema = z.object({
  userId: z.string().uuid(),
  metadata: z.record(z.unknown()).optional(),
  correlationId: z.string().uuid().optional(),
  requestId: z.string().uuid().optional(),
  sessionId: z.string().uuid().optional(),
  timestamp: z.string().datetime().optional(),
  ipAddress: z.string().ip().optional(),
  userAgent: z.string().optional(),
  language: z.string().optional(),
  timezone: z.string().optional(),
  customFields: z.record(z.unknown()).optional(),
});

export type UseCaseContext = z.infer<typeof UseCaseContextSchema>;

export interface UseCaseError {
  message: string;
  code: string;
  details?: Record<string, any>;
}

export interface UseCaseResult<T> {
  success: boolean;
  data?: T;
  error?: UseCaseError;
}

export interface UseCase<TInput = unknown, TOutput = unknown> {
  execute(input: TInput, context: UseCaseContext): Promise<TOutput>;
  validate(input: TInput, context: UseCaseContext): Promise<boolean>;
  authorize(input: TInput, context: UseCaseContext): Promise<boolean>;
  audit(input: TInput, context: UseCaseContext): Promise<void>;
}

export interface UseCaseHandler<TInput = unknown, TOutput = unknown> {
  handle(input: TInput, context: UseCaseContext): Promise<TOutput>;
  validate(input: TInput, context: UseCaseContext): Promise<boolean>;
  authorize(input: TInput, context: UseCaseContext): Promise<boolean>;
  audit(input: TInput, context: UseCaseContext): Promise<void>;
  rollback(input: TInput, context: UseCaseContext): Promise<void>;
}

export interface UseCaseFactory {
  create<TInput = unknown, TOutput = unknown>(useCase: string): UseCase<TInput, TOutput>;
  register<TInput = unknown, TOutput = unknown>(useCase: string, handler: UseCaseHandler<TInput, TOutput>): void;
  unregister(useCase: string): void;
  has(useCase: string): boolean;
  list(): string[];
}

export interface UseCaseRegistry {
  register<TInput = unknown, TOutput = unknown>(useCase: string, handler: UseCaseHandler<TInput, TOutput>): void;
  unregister(useCase: string): void;
  get<TInput = unknown, TOutput = unknown>(useCase: string): UseCaseHandler<TInput, TOutput> | null;
  has(useCase: string): boolean;
  list(): string[];
  clear(): void;
}

export interface UseCaseExecutor {
  execute<TInput = unknown, TOutput = unknown>(
    useCase: string,
    input: TInput,
    context: UseCaseContext
  ): Promise<TOutput>;
  
  validate<TInput = unknown>(
    useCase: string,
    input: TInput,
    context: UseCaseContext
  ): Promise<boolean>;
  
  authorize<TInput = unknown>(
    useCase: string,
    input: TInput,
    context: UseCaseContext
  ): Promise<boolean>;
  
  audit<TInput = unknown>(
    useCase: string,
    input: TInput,
    context: UseCaseContext
  ): Promise<void>;
  
  rollback<TInput = unknown>(
    useCase: string,
    input: TInput,
    context: UseCaseContext
  ): Promise<void>;
} 