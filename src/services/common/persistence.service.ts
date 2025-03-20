import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from './logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { RedisService } from './redis.service';

@Injectable()
export class PersistenceService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
    private readonly redisService: RedisService,
  ) {}

  async save<T>(key: string, value: T, ttl?: number): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      await this.redisService.set(key, serialized, ttl);
      
      this.loggingService.debug('Data saved successfully', { key });
      this.monitoringService.recordMetric({
        name: 'persistence_save',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });
    } catch (error) {
      this.loggingService.error('Failed to save data', {
        error,
        key,
        value,
      });
      throw error;
    }
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const serialized = await this.redisService.get(key);
      if (!serialized) {
        return null;
      }

      const value = JSON.parse(serialized);
      
      this.loggingService.debug('Data retrieved successfully', { key });
      this.monitoringService.recordMetric({
        name: 'persistence_get',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });

      return value as T;
    } catch (error) {
      this.loggingService.error('Failed to retrieve data', {
        error,
        key,
      });
      throw error;
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.redisService.del(key);
      
      this.loggingService.debug('Data deleted successfully', { key });
      this.monitoringService.recordMetric({
        name: 'persistence_delete',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });
    } catch (error) {
      this.loggingService.error('Failed to delete data', {
        error,
        key,
      });
      throw error;
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      const exists = await this.redisService.exists(key);
      
      this.loggingService.debug('Checked data existence', { key, exists });
      this.monitoringService.recordMetric({
        name: 'persistence_exists',
        value: exists ? 1 : 0,
        timestamp: new Date(),
        tags: { key },
      });

      return exists;
    } catch (error) {
      this.loggingService.error('Failed to check data existence', {
        error,
        key,
      });
      throw error;
    }
  }

  async increment(key: string): Promise<number> {
    try {
      const value = await this.redisService.incr(key);
      
      this.loggingService.debug('Counter incremented successfully', { key, value });
      this.monitoringService.recordMetric({
        name: 'persistence_increment',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });

      return value;
    } catch (error) {
      this.loggingService.error('Failed to increment counter', {
        error,
        key,
      });
      throw error;
    }
  }

  async decrement(key: string): Promise<number> {
    try {
      const value = await this.redisService.decr(key);
      
      this.loggingService.debug('Counter decremented successfully', { key, value });
      this.monitoringService.recordMetric({
        name: 'persistence_decrement',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });

      return value;
    } catch (error) {
      this.loggingService.error('Failed to decrement counter', {
        error,
        key,
      });
      throw error;
    }
  }

  async setExpiry(key: string, seconds: number): Promise<void> {
    try {
      await this.redisService.expire(key, seconds);
      
      this.loggingService.debug('Expiry set successfully', { key, seconds });
      this.monitoringService.recordMetric({
        name: 'persistence_set_expiry',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });
    } catch (error) {
      this.loggingService.error('Failed to set expiry', {
        error,
        key,
        seconds,
      });
      throw error;
    }
  }

  async getExpiry(key: string): Promise<number> {
    try {
      const ttl = await this.redisService.ttl(key);
      
      this.loggingService.debug('Expiry retrieved successfully', { key, ttl });
      this.monitoringService.recordMetric({
        name: 'persistence_get_expiry',
        value: 1,
        timestamp: new Date(),
        tags: { key },
      });

      return ttl;
    } catch (error) {
      this.loggingService.error('Failed to get expiry', {
        error,
        key,
      });
      throw error;
    }
  }
} 