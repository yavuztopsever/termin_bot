import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { RateLimit, RateLimitConfig, RateLimitStats, RateLimitResult } from './rate-limit.types';

@Injectable()
export class RateLimitService {
  private config: RateLimitConfig;
  private limits: Map<string, RateLimit> = new Map();

  constructor(
    private readonly configService: ConfigService,
    private readonly monitoringService: MonitoringService,
  ) {
    this.config = this.loadConfig();
  }

  private loadConfig(): RateLimitConfig {
    return {
      enabled: this.configService.get<boolean>('rateLimit.enabled', true),
      defaultLimit: this.configService.get<number>('rateLimit.defaultLimit', 100),
      defaultWindow: this.configService.get<number>('rateLimit.defaultWindow', 60000), // 1 minute
      limits: this.configService.get<Record<string, { limit: number; window: number }>>('rateLimit.limits', {}),
    };
  }

  async checkLimit(key: string): Promise<RateLimitResult> {
    if (!this.config.enabled) {
      return { allowed: true, remaining: 1, resetTime: 0 };
    }

    try {
      const limit = this.getOrCreateLimit(key);
      const now = Date.now();

      // Reset if window has passed
      if (now >= limit.resetTime) {
        limit.current = 0;
        limit.resetTime = now + limit.window;
      }

      // Check if limit is exceeded
      if (limit.current >= limit.limit) {
        await this.monitoringService.recordMetric('rate_limit_exceeded', 1, { key });
        return {
          allowed: false,
          remaining: 0,
          resetTime: limit.resetTime,
        };
      }

      // Increment counter
      limit.current++;
      await this.monitoringService.recordMetric('rate_limit_check', 1, { key });

      return {
        allowed: true,
        remaining: limit.limit - limit.current,
        resetTime: limit.resetTime,
      };
    } catch (error) {
      await this.monitoringService.recordError('rate_limit_error', error);
      // Allow request on error
      return { allowed: true, remaining: 1, resetTime: 0 };
    }
  }

  private getOrCreateLimit(key: string): RateLimit {
    let limit = this.limits.get(key);
    if (!limit) {
      const config = this.config.limits[key] || {
        limit: this.config.defaultLimit,
        window: this.config.defaultWindow,
      };

      limit = {
        key,
        limit: config.limit,
        window: config.window,
        current: 0,
        resetTime: Date.now() + config.window,
      };

      this.limits.set(key, limit);
    }
    return limit;
  }

  async getStats(): Promise<RateLimitStats> {
    const stats: RateLimitStats = {
      total: this.limits.size,
      byKey: {},
    };

    for (const [key, limit] of this.limits.entries()) {
      stats.byKey[key] = {
        current: limit.current,
        limit: limit.limit,
        window: limit.window,
        resetTime: limit.resetTime,
      };
    }

    return stats;
  }

  async reset(key: string): Promise<void> {
    const limit = this.limits.get(key);
    if (limit) {
      limit.current = 0;
      limit.resetTime = Date.now() + limit.window;
      await this.monitoringService.recordMetric('rate_limit_reset', 1, { key });
    }
  }

  async clear(): Promise<void> {
    this.limits.clear();
    await this.monitoringService.recordMetric('rate_limit_clear', 1);
  }
} 