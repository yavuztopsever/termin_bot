import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from './config.service';
import { MonitoringService } from '../../infrastructure/monitoring/monitoring.service';
import { z } from 'zod';

@Injectable()
export class ConfigValidationService {
  private readonly logger = new Logger(ConfigValidationService.name);

  // Define configuration schemas
  private readonly appointmentConfigSchema = z.object({
    url: z.string().url(),
    type: z.string(),
    id: z.string(),
    metadata: z.record(z.unknown()).optional(),
    maxRetries: z.number().int().min(1).max(10),
    timeout: z.number().int().min(1000).max(30000),
    rateLimit: z.object({
      maxRequests: z.number().int().min(1),
      windowMs: z.number().int().min(1000)
    })
  });

  private readonly rateLimitConfigSchema = z.object({
    appointment: z.object({
      maxRequests: z.number().int().min(1),
      windowMs: z.number().int().min(1000)
    }),
    api: z.object({
      maxRequests: z.number().int().min(1),
      windowMs: z.number().int().min(1000)
    })
  });

  private readonly securityConfigSchema = z.object({
    allowedOrigins: z.array(z.string()),
    maxRequestSize: z.number().int().min(1024).max(10485760), // 1KB to 10MB
    sessionTimeout: z.number().int().min(300).max(3600), // 5min to 1hour
    passwordMinLength: z.number().int().min(8).max(32),
    requireSecureConnection: z.boolean()
  });

  constructor(
    private readonly configService: ConfigService,
    private readonly monitoringService: MonitoringService
  ) {}

  /**
   * Validates appointment configuration
   */
  validateAppointmentConfig(config: unknown): boolean {
    try {
      const validatedConfig = this.appointmentConfigSchema.parse(config);
      
      // Additional security checks
      if (!this.isSecureUrl(validatedConfig.url)) {
        this.logger.error('Invalid URL in appointment config', {
          url: this.sanitizeUrl(validatedConfig.url)
        });
        return false;
      }

      // Validate metadata for sensitive information
      if (validatedConfig.metadata) {
        if (!this.validateMetadata(validatedConfig.metadata)) {
          return false;
        }
      }

      return true;
    } catch (error) {
      this.logger.error('Appointment config validation failed', {
        error: this.sanitizeError(error)
      });
      this.monitoringService.recordMetric(
        'config_validation_error',
        1,
        { type: 'appointment' }
      );
      return false;
    }
  }

  /**
   * Validates rate limit configuration
   */
  validateRateLimitConfig(config: unknown): boolean {
    try {
      this.rateLimitConfigSchema.parse(config);
      return true;
    } catch (error) {
      this.logger.error('Rate limit config validation failed', {
        error: this.sanitizeError(error)
      });
      this.monitoringService.recordMetric(
        'config_validation_error',
        1,
        { type: 'rate_limit' }
      );
      return false;
    }
  }

  /**
   * Validates security configuration
   */
  validateSecurityConfig(config: unknown): boolean {
    try {
      const validatedConfig = this.securityConfigSchema.parse(config);
      
      // Validate allowed origins
      if (!this.validateAllowedOrigins(validatedConfig.allowedOrigins)) {
        return false;
      }

      return true;
    } catch (error) {
      this.logger.error('Security config validation failed', {
        error: this.sanitizeError(error)
      });
      this.monitoringService.recordMetric(
        'config_validation_error',
        1,
        { type: 'security' }
      );
      return false;
    }
  }

  /**
   * Validates all configurations
   */
  validateAllConfigs(): boolean {
    const config = this.configService.getAll();
    
    const results = {
      appointment: this.validateAppointmentConfig(config.appointment),
      rateLimit: this.validateRateLimitConfig(config.rateLimit),
      security: this.validateSecurityConfig(config.security)
    };

    const allValid = Object.values(results).every(Boolean);
    if (!allValid) {
      this.logger.error('Configuration validation failed', {
        results: this.sanitizeResults(results)
      });
    }

    return allValid;
  }

  private isSecureUrl(url: string): boolean {
    try {
      const parsedUrl = new URL(url);
      return parsedUrl.protocol === 'https:';
    } catch {
      return false;
    }
  }

  private validateMetadata(metadata: Record<string, unknown>): boolean {
    const sensitiveKeys = ['password', 'token', 'key', 'secret', 'credential'];
    
    for (const [key, value] of Object.entries(metadata)) {
      // Check for sensitive keys
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
        this.logger.error('Sensitive information found in metadata', {
          key: this.sanitizeKey(key)
        });
        return false;
      }

      // Validate value types
      if (typeof value === 'string' && this.containsSensitiveData(value)) {
        this.logger.error('Sensitive data found in metadata value', {
          key: this.sanitizeKey(key)
        });
        return false;
      }
    }

    return true;
  }

  private validateAllowedOrigins(origins: string[]): boolean {
    for (const origin of origins) {
      try {
        new URL(origin);
      } catch {
        this.logger.error('Invalid allowed origin', {
          origin: this.sanitizeUrl(origin)
        });
        return false;
      }
    }
    return true;
  }

  private containsSensitiveData(value: string): boolean {
    // Check for common sensitive data patterns
    const patterns = [
      /^[A-Za-z0-9+/=]+$/, // Base64
      /^[0-9a-fA-F]{32,}$/, // MD5/SHA hashes
      /^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$/, // JWT
      /^[0-9]{16}$/, // Credit card numbers
      /^[0-9]{10}$/ // Phone numbers
    ];

    return patterns.some(pattern => pattern.test(value));
  }

  private sanitizeUrl(url: string): string {
    try {
      const parsedUrl = new URL(url);
      return `${parsedUrl.protocol}//${parsedUrl.hostname}`;
    } catch {
      return '[INVALID_URL]';
    }
  }

  private sanitizeKey(key: string): string {
    return key.replace(/[a-zA-Z0-9]{32,}/g, '[REDACTED]');
  }

  private sanitizeError(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }

  private sanitizeResults(results: Record<string, boolean>): Record<string, boolean> {
    return Object.fromEntries(
      Object.entries(results).map(([key, value]) => [
        this.sanitizeKey(key),
        value
      ])
    );
  }
} 