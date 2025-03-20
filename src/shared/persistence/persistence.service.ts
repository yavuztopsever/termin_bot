import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { RedisService } from '../redis/redis.service';
import { BaseService } from '../base/base.service';
import { LoggingService } from '../logging/logging.service';
import { ErrorService } from '../error/error.service';

export interface PersistenceOptions {
  ttl?: number;
  prefix?: string;
  serialize?: boolean;
}

@Injectable()
export class PersistenceService extends BaseService {
  private readonly defaultPrefix: string;
  private readonly defaultTTL: number;

  constructor(
    configService: ConfigService,
    loggingService: LoggingService,
    errorService: ErrorService,
    private readonly redisService: RedisService
  ) {
    super(configService, loggingService, errorService, 'PersistenceService');
    this.defaultPrefix = this.getConfig('REDIS_KEY_PREFIX', 'app:');
    this.defaultTTL = this.getConfig('REDIS_DEFAULT_TTL', 3600);
  }

  private getKey(key: string, prefix?: string): string {
    return `${prefix || this.defaultPrefix}${key}`;
  }

  async save<T>(
    key: string,
    data: T,
    options: PersistenceOptions = {}
  ): Promise<void> {
    try {
      const fullKey = this.getKey(key, options.prefix);
      const serializedData = options.serialize !== false ? JSON.stringify(data) : data;
      
      await this.redisService.set(
        fullKey,
        serializedData,
        options.ttl || this.defaultTTL
      );

      this.logInfo(`Saved data for key: ${fullKey}`);
    } catch (error) {
      this.handleServiceError(error as Error, 'save');
    }
  }

  async get<T>(
    key: string,
    options: PersistenceOptions = {}
  ): Promise<T | null> {
    try {
      const fullKey = this.getKey(key, options.prefix);
      const data = await this.redisService.get(fullKey);
      
      if (!data) {
        return null;
      }

      return options.serialize !== false ? JSON.parse(data) : data;
    } catch (error) {
      this.handleServiceError(error as Error, 'get');
    }
  }

  async delete(key: string, prefix?: string): Promise<void> {
    try {
      const fullKey = this.getKey(key, prefix);
      await this.redisService.del(fullKey);
      this.logInfo(`Deleted data for key: ${fullKey}`);
    } catch (error) {
      this.handleServiceError(error as Error, 'delete');
    }
  }

  async exists(key: string, prefix?: string): Promise<boolean> {
    try {
      const fullKey = this.getKey(key, prefix);
      return this.redisService.exists(fullKey);
    } catch (error) {
      this.handleServiceError(error as Error, 'exists');
    }
  }

  async increment(key: string, prefix?: string): Promise<number> {
    try {
      const fullKey = this.getKey(key, prefix);
      return this.redisService.incr(fullKey);
    } catch (error) {
      this.handleServiceError(error as Error, 'increment');
    }
  }

  async setExpiry(key: string, seconds: number, prefix?: string): Promise<void> {
    try {
      const fullKey = this.getKey(key, prefix);
      await this.redisService.expire(fullKey, seconds);
      this.logInfo(`Set expiry for key: ${fullKey} to ${seconds} seconds`);
    } catch (error) {
      this.handleServiceError(error as Error, 'setExpiry');
    }
  }

  async getTTL(key: string, prefix?: string): Promise<number> {
    try {
      const fullKey = this.getKey(key, prefix);
      return this.redisService.ttl(fullKey);
    } catch (error) {
      this.handleServiceError(error as Error, 'getTTL');
    }
  }

  async clearByPrefix(prefix: string): Promise<void> {
    try {
      const keys = await this.redisService.keys(`${prefix}*`);
      if (keys.length > 0) {
        await this.redisService.del(...keys);
        this.logInfo(`Cleared ${keys.length} keys with prefix: ${prefix}`);
      }
    } catch (error) {
      this.handleServiceError(error as Error, 'clearByPrefix');
    }
  }
} 