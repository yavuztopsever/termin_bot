import { Injectable } from '@nestjs/common';
import * as dotenv from 'dotenv';
import * as path from 'path';

interface Config {
  [key: string]: any;
}

@Injectable()
export class ConfigService {
  private config: Config = {};

  constructor() {
    // Load environment variables from .env file
    dotenv.config({
      path: path.resolve(process.cwd(), '.env')
    });

    // Initialize configuration
    this.config = {
      app: {
        name: process.env.APP_NAME || 'TerminBot',
        env: process.env.NODE_ENV || 'development',
        port: parseInt(process.env.PORT || '3000', 10),
        apiPrefix: process.env.API_PREFIX || '/api'
      },
      redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379', 10),
        password: process.env.REDIS_PASSWORD,
        db: parseInt(process.env.REDIS_DB || '0', 10)
      },
      logging: {
        level: process.env.LOG_LEVEL || 'info',
        format: process.env.LOG_FORMAT || 'json',
        file: process.env.LOG_FILE,
        maxSize: parseInt(process.env.LOG_MAX_SIZE || '5242880', 10), // 5MB
        maxFiles: parseInt(process.env.LOG_MAX_FILES || '5', 10)
      },
      monitoring: {
        enabled: process.env.MONITORING_ENABLED === 'true',
        endpoint: process.env.MONITORING_ENDPOINT,
        maxMetrics: parseInt(process.env.MONITORING_MAX_METRICS || '1000', 10),
        flushInterval: parseInt(process.env.MONITORING_FLUSH_INTERVAL || '60000', 10),
        tags: {
          app: process.env.APP_NAME || 'TerminBot',
          env: process.env.NODE_ENV || 'development'
        }
      },
      rateLimit: {
        enabled: process.env.RATE_LIMIT_ENABLED === 'true',
        windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10),
        max: parseInt(process.env.RATE_LIMIT_MAX || '100', 10)
      },
      browser: {
        headless: process.env.BROWSER_HEADLESS === 'true',
        timeout: parseInt(process.env.BROWSER_TIMEOUT || '30000', 10),
        userAgent: process.env.BROWSER_USER_AGENT
      },
      ai: {
        enabled: process.env.AI_ENABLED === 'true',
        apiKey: process.env.AI_API_KEY,
        model: process.env.AI_MODEL || 'gpt-4',
        maxTokens: parseInt(process.env.AI_MAX_TOKENS || '2000', 10),
        temperature: parseFloat(process.env.AI_TEMPERATURE || '0.7')
      },
      booking: {
        enabled: process.env.BOOKING_ENABLED === 'true',
        maxAttempts: parseInt(process.env.BOOKING_MAX_ATTEMPTS || '3', 10),
        retryDelay: parseInt(process.env.BOOKING_RETRY_DELAY || '5000', 10),
        timeout: parseInt(process.env.BOOKING_TIMEOUT || '30000', 10)
      }
    };
  }

  get<T = any>(key: string, defaultValue?: T): T {
    const value = key.split('.').reduce((obj, k) => obj?.[k], this.config);
    return value !== undefined ? value : defaultValue;
  }

  getAll(): Config {
    return { ...this.config };
  }

  set(key: string, value: any): void {
    const keys = key.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((obj, k) => obj[k] = obj[k] || {}, this.config);
    target[lastKey] = value;
  }

  // Helper methods for specific configurations
  isDevelopment(): boolean {
    return this.get('app.env') === 'development';
  }

  isProduction(): boolean {
    return this.get('app.env') === 'production';
  }

  isTest(): boolean {
    return this.get('app.env') === 'test';
  }

  getAppName(): string {
    return this.get('app.name');
  }

  getPort(): number {
    return this.get('app.port');
  }

  getRedisConfig(): Config {
    return this.get('redis');
  }

  getLoggingConfig(): Config {
    return this.get('logging');
  }

  getMonitoringConfig(): Config {
    return this.get('monitoring');
  }

  getRateLimitConfig(): Config {
    return this.get('rateLimit');
  }

  getBrowserConfig(): Config {
    return this.get('browser');
  }

  getAIConfig(): Config {
    return this.get('ai');
  }

  getBookingConfig(): Config {
    return this.get('booking');
  }
} 