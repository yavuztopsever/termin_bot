import { z } from 'zod';

export const AppointmentConfigSchema = z.object({
  id: z.string().uuid(),
  url: z.string().url(),
  type: z.string(),
  retryCount: z.number().nonnegative().default(3),
  maxRetries: z.number().positive().default(5),
  retryDelay: z.number().positive().default(1000),
  timeout: z.number().positive().default(30000),
  interval: z.number().positive().default(60000),
  startTime: z.string().datetime().optional(),
  endTime: z.string().datetime().optional(),
  daysOfWeek: z.array(z.number().min(0).max(6)).optional(),
  timezone: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  notifications: z.object({
    email: z.boolean().default(false),
    sms: z.boolean().default(false),
    push: z.boolean().default(false),
    webhook: z.boolean().default(false),
    webhookUrl: z.string().url().optional(),
  }).default({}),
  validation: z.object({
    requiredFields: z.array(z.string()).default([]),
    customValidation: z.boolean().default(false),
    validationRules: z.record(z.unknown()).optional(),
  }).default({}),
  automation: z.object({
    enabled: z.boolean().default(false),
    autoBook: z.boolean().default(false),
    autoCancel: z.boolean().default(false),
    autoReschedule: z.boolean().default(false),
    rules: z.array(z.record(z.unknown())).optional(),
  }).default({}),
  metadata: z.record(z.unknown()).optional(),
});

export type AppointmentConfig = z.infer<typeof AppointmentConfigSchema>;

export interface AppointmentConfigRepository {
  save(config: AppointmentConfig): Promise<void>;
  findById(id: string): Promise<AppointmentConfig | null>;
  findByType(type: string): Promise<AppointmentConfig[]>;
  findByUrl(url: string): Promise<AppointmentConfig[]>;
  delete(id: string): Promise<void>;
  update(id: string, config: Partial<AppointmentConfig>): Promise<void>;
  list(options?: {
    limit?: number;
    offset?: number;
    sort?: Record<string, 'asc' | 'desc'>;
    filter?: Record<string, unknown>;
  }): Promise<AppointmentConfig[]>;
}

export interface AppointmentConfigService {
  createConfig(data: Omit<AppointmentConfig, 'id'>): Promise<AppointmentConfig>;
  getConfig(id: string): Promise<AppointmentConfig>;
  updateConfig(id: string, data: Partial<AppointmentConfig>): Promise<AppointmentConfig>;
  deleteConfig(id: string): Promise<void>;
  listConfigs(options?: {
    limit?: number;
    offset?: number;
    sort?: Record<string, 'asc' | 'desc'>;
    filter?: Record<string, unknown>;
  }): Promise<AppointmentConfig[]>;
  validateConfig(config: AppointmentConfig): Promise<boolean>;
  testConfig(config: AppointmentConfig): Promise<{
    success: boolean;
    error?: string;
    details?: Record<string, unknown>;
  }>;
}

export interface AppointmentConfigValidator {
  validate(config: AppointmentConfig): Promise<boolean>;
  validateCreation(data: Omit<AppointmentConfig, 'id'>): Promise<boolean>;
  validateUpdate(id: string, data: Partial<AppointmentConfig>): Promise<boolean>;
  validateDeletion(id: string): Promise<boolean>;
  getErrors(config: AppointmentConfig): Promise<Array<{
    path: string[];
    message: string;
    code: string;
  }>>;
} 