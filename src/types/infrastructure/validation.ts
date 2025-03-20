import { z } from 'zod';

export const ValidationConfigSchema = z.object({
  enabled: z.boolean(),
  strict: z.boolean(),
  transform: z.boolean(),
  abortEarly: z.boolean(),
});

export type ValidationConfig = z.infer<typeof ValidationConfigSchema>;

export interface ValidationService {
  validate<T>(schema: z.ZodSchema<T>, data: unknown): Promise<ValidationResult<T>>;
  validateAsync<T>(schema: z.ZodSchema<T>, data: unknown): Promise<ValidationResult<T>>;
  clear(): Promise<void>;
}

export interface ValidationResult<T> {
  success: boolean;
  data?: T;
  errors?: ValidationError[];
}

export interface ValidationError {
  path: string[];
  message: string;
  code: string;
  params?: Record<string, unknown>;
}

export interface ValidationSchema<T> {
  schema: z.ZodSchema<T>;
  options?: ValidationOptions;
}

export interface ValidationOptions {
  strict?: boolean;
  transform?: boolean;
  abortEarly?: boolean;
}

export interface ValidationRule<T> {
  validate(value: T): boolean;
  message: string;
}

export interface ValidationContext {
  path: string[];
  value: unknown;
  parent: unknown;
  options: ValidationOptions;
} 