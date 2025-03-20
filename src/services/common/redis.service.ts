import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from './logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import Redis from 'ioredis';

@Injectable()
export class RedisService implements OnModuleInit, OnModuleDestroy {
  private client: Redis;

  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
  ) {}

  async onModuleInit() {
    try {
      const redisConfig = this.configService.get('redis');
      this.client = new Redis({
        host: redisConfig.host,
        port: redisConfig.port,
        password: redisConfig.password,
        db: redisConfig.db,
        retryStrategy: (times: number) => {
          const delay = Math.min(times * 50, 2000);
          return delay;
        },
      });

      this.client.on('connect', () => {
        this.loggingService.info('Redis client connected');
        this.monitoringService.recordMetric({
          name: 'redis_connection_status',
          value: 1,
          timestamp: new Date(),
        });
      });

      this.client.on('error', (error) => {
        this.loggingService.error('Redis client error', { error });
        this.monitoringService.recordMetric({
          name: 'redis_connection_status',
          value: 0,
          timestamp: new Date(),
        });
      });

      await this.client.ping();
    } catch (error) {
      this.loggingService.error('Failed to initialize Redis client', { error });
      throw error;
    }
  }

  async onModuleDestroy() {
    try {
      await this.client.quit();
      this.loggingService.info('Redis client disconnected');
    } catch (error) {
      this.loggingService.error('Failed to disconnect Redis client', { error });
    }
  }

  async set(key: string, value: string, ttl?: number): Promise<void> {
    try {
      if (ttl) {
        await this.client.setex(key, ttl, value);
      } else {
        await this.client.set(key, value);
      }
    } catch (error) {
      this.loggingService.error('Failed to set Redis key', { error, key });
      throw error;
    }
  }

  async get(key: string): Promise<string | null> {
    try {
      return await this.client.get(key);
    } catch (error) {
      this.loggingService.error('Failed to get Redis key', { error, key });
      throw error;
    }
  }

  async del(key: string): Promise<void> {
    try {
      await this.client.del(key);
    } catch (error) {
      this.loggingService.error('Failed to delete Redis key', { error, key });
      throw error;
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      const result = await this.client.exists(key);
      return result === 1;
    } catch (error) {
      this.loggingService.error('Failed to check Redis key existence', { error, key });
      throw error;
    }
  }

  async incr(key: string): Promise<number> {
    try {
      return await this.client.incr(key);
    } catch (error) {
      this.loggingService.error('Failed to increment Redis key', { error, key });
      throw error;
    }
  }

  async decr(key: string): Promise<number> {
    try {
      return await this.client.decr(key);
    } catch (error) {
      this.loggingService.error('Failed to decrement Redis key', { error, key });
      throw error;
    }
  }

  async expire(key: string, seconds: number): Promise<void> {
    try {
      await this.client.expire(key, seconds);
    } catch (error) {
      this.loggingService.error('Failed to set Redis key expiry', { error, key, seconds });
      throw error;
    }
  }

  async ttl(key: string): Promise<number> {
    try {
      return await this.client.ttl(key);
    } catch (error) {
      this.loggingService.error('Failed to get Redis key TTL', { error, key });
      throw error;
    }
  }
} 