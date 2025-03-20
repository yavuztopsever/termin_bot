export interface RateLimit {
  key: string;
  limit: number;
  window: number; // in milliseconds
  current: number;
  resetTime: number;
}

export interface RateLimitConfig {
  enabled: boolean;
  defaultLimit: number;
  defaultWindow: number;
  limits: Record<string, { limit: number; window: number }>;
}

export interface RateLimitStats {
  total: number;
  byKey: Record<string, {
    current: number;
    limit: number;
    window: number;
    resetTime: number;
  }>;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetTime: number;
} 