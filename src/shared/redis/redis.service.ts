import { Injectable } from '@nestjs/common';
import { Redis } from 'ioredis';
import { ConfigService } from '@nestjs/config';
import { BaseService } from '../base/base.service';
import { LoggingService } from '../logging/logging.service';
import { ErrorService } from '../error/error.service';

@Injectable()
export class RedisService extends BaseService {
  private readonly redis: Redis;

  constructor(
    configService: ConfigService,
    loggingService: LoggingService,
    errorService: ErrorService
  ) {
    super(configService, loggingService, errorService, 'RedisService');
    
    this.redis = new Redis({
      host: this.getConfig('REDIS_HOST', 'localhost'),
      port: this.getConfig('REDIS_PORT', 6379),
      password: this.getConfig('REDIS_PASSWORD'),
      db: this.getConfig('REDIS_DB', 0),
      retryStrategy: (times: number) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      }
    });

    this.redis.on('error', (error) => {
      this.logError('Redis connection error', error);
    });

    this.redis.on('connect', () => {
      this.logInfo('Redis connected successfully');
    });
  }

  async get(key: string): Promise<string | null> {
    try {
      return await this.redis.get(key);
    } catch (error) {
      this.handleServiceError(error as Error, 'get');
    }
  }

  async set(key: string, value: string, ttl?: number): Promise<void> {
    try {
      if (ttl) {
        await this.redis.set(key, value, 'EX', ttl);
      } else {
        await this.redis.set(key, value);
      }
    } catch (error) {
      this.handleServiceError(error as Error, 'set');
    }
  }

  async del(key: string): Promise<void> {
    try {
      await this.redis.del(key);
    } catch (error) {
      this.handleServiceError(error as Error, 'del');
    }
  }

  async delMultiple(...keys: string[]): Promise<void> {
    try {
      await this.redis.del(...keys);
    } catch (error) {
      this.handleServiceError(error as Error, 'delMultiple');
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      return (await this.redis.exists(key)) === 1;
    } catch (error) {
      this.handleServiceError(error as Error, 'exists');
    }
  }

  async incr(key: string): Promise<number> {
    try {
      return await this.redis.incr(key);
    } catch (error) {
      this.handleServiceError(error as Error, 'incr');
    }
  }

  async expire(key: string, seconds: number): Promise<void> {
    try {
      await this.redis.expire(key, seconds);
    } catch (error) {
      this.handleServiceError(error as Error, 'expire');
    }
  }

  async ttl(key: string): Promise<number> {
    try {
      return await this.redis.ttl(key);
    } catch (error) {
      this.handleServiceError(error as Error, 'ttl');
    }
  }

  async keys(pattern: string): Promise<string[]> {
    try {
      return await this.redis.keys(pattern);
    } catch (error) {
      this.handleServiceError(error as Error, 'keys');
    }
  }

  async flushdb(): Promise<void> {
    try {
      await this.redis.flushdb();
      this.logInfo('Redis database flushed');
    } catch (error) {
      this.handleServiceError(error as Error, 'flushdb');
    }
  }

  async ping(): Promise<string> {
    try {
      return await this.redis.ping();
    } catch (error) {
      this.handleServiceError(error as Error, 'ping');
    }
  }

  async quit(): Promise<void> {
    try {
      await this.redis.quit();
      this.logInfo('Redis connection closed');
    } catch (error) {
      this.handleServiceError(error as Error, 'quit');
    }
  }
} 