import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const ValidationConfigSchema = BaseConfig.extend({
  strictMode: z.boolean(),
  abortEarly: z.boolean(),
  stripUnknown: z.boolean(),
  cacheEnabled: z.boolean(),
  maxErrors: z.number(),
  errorMap: z.function(),
  customErrorMessages: z.record(z.string(), z.string()),
});

export type ValidationConfig = z.infer<typeof ValidationConfigSchema>;

export interface ValidationService extends BaseService {
  validate<T>(schema: z.ZodSchema<T>, data: unknown): Promise<T>;
  validatePartial<T>(schema: z.ZodSchema<T>, data: unknown): Promise<Partial<T>>;
  validateArray<T>(schema: z.ZodSchema<T>, data: unknown[]): Promise<T[]>;
  validateObject<T>(schema: z.ZodSchema<T>, data: Record<string, unknown>): Promise<T>;
  validateString(schema: z.ZodString, data: string): Promise<string>;
  validateNumber(schema: z.ZodNumber, data: number): Promise<number>;
  validateBoolean(schema: z.ZodBoolean, data: boolean): Promise<boolean>;
  validateDate(schema: z.ZodDate, data: Date): Promise<Date>;
  validateEnum<T extends [string, ...string[]]>(schema: z.ZodEnum<T>, data: T[number]): Promise<T[number]>;
  validateUnion<T extends [z.ZodTypeAny, ...z.ZodTypeAny[]]>(schema: z.ZodUnion<T>, data: z.infer<z.ZodUnion<T>>): Promise<z.infer<z.ZodUnion<T>>>;
  validateIntersection<T extends [z.ZodTypeAny, ...z.ZodTypeAny[]]>(schema: z.ZodIntersection<T>, data: z.infer<z.ZodIntersection<T>>): Promise<z.infer<z.ZodIntersection<T>>>;
  validateTuple<T extends [z.ZodTypeAny, ...z.ZodTypeAny[]]>(schema: z.ZodTuple<T>, data: z.infer<z.ZodTuple<T>>): Promise<z.infer<z.ZodTuple<T>>>;
  validateRecord<K extends string, V extends z.ZodTypeAny>(schema: z.ZodRecord<K, V>, data: Record<K, z.infer<V>>): Promise<Record<K, z.infer<V>>>;
  validateMap<K extends z.ZodTypeAny, V extends z.ZodTypeAny>(schema: z.ZodMap<K, V>, data: Map<z.infer<K>, z.infer<V>>): Promise<Map<z.infer<K>, z.infer<V>>>;
  validateSet<T extends z.ZodTypeAny>(schema: z.ZodSet<T>, data: Set<z.infer<T>>): Promise<Set<z.infer<T>>>;
  validatePromise<T extends z.ZodTypeAny>(schema: z.ZodPromise<T>, data: Promise<z.infer<T>>): Promise<z.infer<T>>;
  validateOptional<T extends z.ZodTypeAny>(schema: z.ZodOptional<T>, data: z.infer<T> | undefined): Promise<z.infer<T> | undefined>;
  validateNullable<T extends z.ZodTypeAny>(schema: z.ZodNullable<T>, data: z.infer<T> | null): Promise<z.infer<T> | null>;
  validateDefault<T extends z.ZodTypeAny>(schema: z.ZodDefault<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateLazy<T extends z.ZodTypeAny>(schema: z.ZodLazy<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateRefinement<T extends z.ZodTypeAny>(schema: z.ZodRefinement<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateCatch<T extends z.ZodTypeAny>(schema: z.ZodCatch<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validatePipeline<T extends z.ZodTypeAny>(schema: z.ZodPipeline<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateBrand<T extends z.ZodTypeAny>(schema: z.ZodBrand<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateEffects<T extends z.ZodTypeAny>(schema: z.ZodEffects<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validatePreprocess<T extends z.ZodTypeAny>(schema: z.ZodPreprocess<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateCustom<T extends z.ZodTypeAny>(schema: z.ZodCustom<T>, data: z.infer<T>): Promise<z.infer<T>>;
  validateAny(schema: z.ZodAny, data: unknown): Promise<unknown>;
  validateUnknown(schema: z.ZodUnknown, data: unknown): Promise<unknown>;
  validateNever(schema: z.ZodNever, data: never): Promise<never>;
  validateVoid(schema: z.ZodVoid, data: void): Promise<void>;
  validateUndefined(schema: z.ZodUndefined, data: undefined): Promise<undefined>;
  validateNull(schema: z.ZodNull, data: null): Promise<null>;
  validateNaN(schema: z.ZodNaN, data: number): Promise<number>;
  validateBigInt(schema: z.ZodBigInt, data: bigint): Promise<bigint>;
  validateSymbol(schema: z.ZodSymbol, data: symbol): Promise<symbol>;
  validateFunction<T extends z.ZodTuple<any, any>, R extends z.ZodTypeAny>(schema: z.ZodFunction<T, R>, data: (...args: z.infer<T>) => z.infer<R>): Promise<(...args: z.infer<T>) => z.infer<R>>;
  validateLiteral<T extends z.ZodLiteral<any>>(schema: T, data: z.infer<T>): Promise<z.infer<T>>;
  validateObject<T extends z.ZodObject<any>>(schema: T, data: z.infer<T>): Promise<z.infer<T>>;
  validateArray<T extends z.ZodArray<any>>(schema: T, data: z.infer<T>): Promise<z.infer<T>>;
}

export interface ValidationError {
  code: string;
  message: string;
  path: string[];
  params: Record<string, unknown>;
}

export interface ValidationResult<T> {
  success: boolean;
  data?: T;
  error?: z.ZodError;
  warnings?: string[];
  metadata?: Record<string, unknown>;
}

export interface ValidationOptions {
  abortEarly?: boolean;
  stripUnknown?: boolean;
  cacheEnabled?: boolean;
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

export enum ValidationErrorCode {
  INVALID_TYPE = 'INVALID_TYPE',
  INVALID_FORMAT = 'INVALID_FORMAT',
  INVALID_RANGE = 'INVALID_RANGE',
  INVALID_LENGTH = 'INVALID_LENGTH',
  INVALID_PATTERN = 'INVALID_PATTERN',
  INVALID_ENUM = 'INVALID_ENUM',
  INVALID_DATE = 'INVALID_DATE',
  INVALID_EMAIL = 'INVALID_EMAIL',
  INVALID_URL = 'INVALID_URL',
  INVALID_PHONE = 'INVALID_PHONE',
  INVALID_IP = 'INVALID_IP',
  INVALID_UUID = 'INVALID_UUID',
  INVALID_JSON = 'INVALID_JSON',
  INVALID_BASE64 = 'INVALID_BASE64',
  INVALID_HEX = 'INVALID_HEX',
  INVALID_BINARY = 'INVALID_BINARY',
  INVALID_ARRAY = 'INVALID_ARRAY',
  INVALID_OBJECT = 'INVALID_OBJECT',
  INVALID_NULL = 'INVALID_NULL',
  INVALID_UNDEFINED = 'INVALID_UNDEFINED',
  INVALID_NAN = 'INVALID_NAN',
  INVALID_INFINITY = 'INVALID_INFINITY',
  INVALID_NUMBER = 'INVALID_NUMBER',
  INVALID_INTEGER = 'INVALID_INTEGER',
  INVALID_FLOAT = 'INVALID_FLOAT',
  INVALID_BOOLEAN = 'INVALID_BOOLEAN',
  INVALID_STRING = 'INVALID_STRING',
  INVALID_REGEX = 'INVALID_REGEX',
  INVALID_FUNCTION = 'INVALID_FUNCTION',
  INVALID_SYMBOL = 'INVALID_SYMBOL',
  INVALID_MAP = 'INVALID_MAP',
  INVALID_SET = 'INVALID_SET',
  INVALID_WEAKMAP = 'INVALID_WEAKMAP',
  INVALID_WEAKSET = 'INVALID_WEAKSET',
  INVALID_PROMISE = 'INVALID_PROMISE',
  INVALID_GENERATOR = 'INVALID_GENERATOR',
  INVALID_ASYNC_GENERATOR = 'INVALID_ASYNC_GENERATOR',
  INVALID_ITERATOR = 'INVALID_ITERATOR',
  INVALID_ASYNC_ITERATOR = 'INVALID_ASYNC_ITERATOR',
  INVALID_BUFFER = 'INVALID_BUFFER',
  INVALID_ARRAY_BUFFER = 'INVALID_ARRAY_BUFFER',
  INVALID_SHARED_ARRAY_BUFFER = 'INVALID_SHARED_ARRAY_BUFFER',
  INVALID_DATA_VIEW = 'INVALID_DATA_VIEW',
  INVALID_TYPED_ARRAY = 'INVALID_TYPED_ARRAY',
  INVALID_BIGINT = 'INVALID_BIGINT',
  INVALID_BIGINT64_ARRAY = 'INVALID_BIGINT64_ARRAY',
  INVALID_BIGUINT64_ARRAY = 'INVALID_BIGUINT64_ARRAY',
  INVALID_FLOAT32_ARRAY = 'INVALID_FLOAT32_ARRAY',
  INVALID_FLOAT64_ARRAY = 'INVALID_FLOAT64_ARRAY',
  INVALID_INT8_ARRAY = 'INVALID_INT8_ARRAY',
  INVALID_INT16_ARRAY = 'INVALID_INT16_ARRAY',
  INVALID_INT32_ARRAY = 'INVALID_INT32_ARRAY',
  INVALID_UINT8_ARRAY = 'INVALID_UINT8_ARRAY',
  INVALID_UINT8_CLAMPED_ARRAY = 'INVALID_UINT8_CLAMPED_ARRAY',
  INVALID_UINT16_ARRAY = 'INVALID_UINT16_ARRAY',
  INVALID_UINT32_ARRAY = 'INVALID_UINT32_ARRAY',
}

export interface ValidationWarning {
  code: string;
  message: string;
  path: string[];
  params: Record<string, unknown>;
} 