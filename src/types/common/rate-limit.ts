import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const RateLimitConfigSchema = BaseConfig.extend({
  enabled: z.boolean(),
  maxRequests: z.number(),
  windowMs: z.number(),
  keyGenerator: z.function().args(z.string()).returns(z.string()),
  handler: z.function().args(z.string()).returns(z.void()),
});

export type RateLimitConfig = z.infer<typeof RateLimitConfigSchema>;

export interface RateLimitService extends BaseService {
  isRateLimited(key: string): Promise<boolean>;
  increment(key: string): Promise<void>;
  reset(key: string): Promise<void>;
  getRemainingRequests(key: string): Promise<number>;
  getResetTime(key: string): Promise<Date>;
}

export interface RateLimitInfo {
  remaining: number;
  reset: Date;
  total: number;
  used: number;
}

export interface RateLimitStore {
  get(key: string): Promise<RateLimitInfo | null>;
  set(key: string, info: RateLimitInfo): Promise<void>;
  delete(key: string): Promise<void>;
  increment(key: string): Promise<RateLimitInfo>;
}

export interface RateLimitRule {
  key: string;
  maxRequests: number;
  windowMs: number;
  handler?: (key: string) => void;
}

export interface RateLimitStrategy {
  isRateLimited(key: string): Promise<boolean>;
  increment(key: string): Promise<void>;
  reset(key: string): Promise<void>;
  getRemainingRequests(key: string): Promise<number>;
  getResetTime(key: string): Promise<Date>;
}

export interface RateLimitContext {
  key: string;
  maxRequests: number;
  windowMs: number;
  currentRequests: number;
  resetTime: Date;
}

export interface RateLimitOptions {
  maxRequests: number;
  windowMs: number;
  handler?: (key: string) => void;
  keyGenerator?: (key: string) => string;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  reset: Date;
  total: number;
  used: number;
}

export interface RateLimitStats {
  totalRequests: number;
  blockedRequests: number;
  averageResponseTime: number;
  peakRequestsPerSecond: number;
  currentRequestsPerSecond: number;
} 