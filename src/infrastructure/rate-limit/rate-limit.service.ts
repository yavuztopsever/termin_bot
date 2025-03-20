import { Injectable } from '@nestjs/common';
import { Redis } from 'ioredis';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class RateLimitService {
  private readonly redis: Redis;
  private readonly defaultLimit: number = 100;
  private readonly defaultWindow: number = 60; // 1 minute in seconds

  constructor(private readonly configService: ConfigService) {
    this.redis = new Redis({
      host: this.configService.get('REDIS_HOST'),
      port: this.configService.get('REDIS_PORT'),
    });
  }

  async isRateLimited(key: string, limit?: number, window?: number): Promise<boolean> {
    const current = await this.redis.incr(key);
    if (current === 1) {
      await this.redis.expire(key, window || this.defaultWindow);
    }
    return current > (limit || this.defaultLimit);
  }

  async resetRateLimit(key: string): Promise<void> {
    await this.redis.del(key);
  }

  async getRateLimitCount(key: string): Promise<number> {
    const count = await this.redis.get(key);
    return count ? parseInt(count, 10) : 0;
  }
} 