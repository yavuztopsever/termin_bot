import { z } from 'zod';

const EnvironmentSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('3000'),
  API_VERSION: z.string().default('v1'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  
  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_POOL_MIN: z.string().transform(Number).default('2'),
  DATABASE_POOL_MAX: z.string().transform(Number).default('10'),
  
  // Redis
  REDIS_URL: z.string().url(),
  REDIS_PASSWORD: z.string().optional(),
  
  // JWT
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('1h'),
  
  // Rate Limiting
  RATE_LIMIT_WINDOW: z.string().transform(Number).default('900000'), // 15 minutes
  RATE_LIMIT_MAX_REQUESTS: z.string().transform(Number).default('100'),
  
  // External Services
  EXTERNAL_API_URL: z.string().url(),
  EXTERNAL_API_KEY: z.string(),
  EXTERNAL_API_TIMEOUT: z.string().transform(Number).default('5000'),
  
  // Monitoring
  SENTRY_DSN: z.string().url().optional(),
  NEW_RELIC_LICENSE_KEY: z.string().optional(),
  
  // Feature Flags
  ENABLE_SWAGGER: z.string().transform(val => val === 'true').default('false'),
  ENABLE_METRICS: z.string().transform(val => val === 'true').default('false'),
  ENABLE_TRACING: z.string().transform(val => val === 'true').default('false'),
});

export type Environment = z.infer<typeof EnvironmentSchema>;

export function validateEnvironment(): Environment {
  try {
    return EnvironmentSchema.parse(process.env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const missingVars = error.errors
        .map(err => err.path.join('.'))
        .join(', ');
      throw new Error(`Missing or invalid environment variables: ${missingVars}`);
    }
    throw error;
  }
}

export const env = validateEnvironment(); 