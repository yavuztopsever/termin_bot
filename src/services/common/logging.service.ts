import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import * as winston from 'winston';

export type LogLevel = 'error' | 'warn' | 'info' | 'debug';

@Injectable()
export class LoggingService {
  private logger: winston.Logger;

  constructor(private readonly configService: ConfigService) {
    const logConfig = this.configService.get('logging');
    const level = logConfig.level || 'info';
    const format = logConfig.format || 'json';

    this.logger = winston.createLogger({
      level,
      format: format === 'json' 
        ? winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        : winston.format.combine(
            winston.format.timestamp(),
            winston.format.colorize(),
            winston.format.simple()
          ),
      transports: [
        new winston.transports.Console(),
        ...(logConfig.file ? [
          new winston.transports.File({
            filename: logConfig.file,
            maxsize: logConfig.maxSize || 5242880, // 5MB
            maxFiles: logConfig.maxFiles || 5,
          })
        ] : []),
      ],
    });
  }

  error(message: string, meta?: Record<string, any>): void {
    this.logger.error(message, meta);
  }

  warn(message: string, meta?: Record<string, any>): void {
    this.logger.warn(message, meta);
  }

  info(message: string, meta?: Record<string, any>): void {
    this.logger.info(message, meta);
  }

  debug(message: string, meta?: Record<string, any>): void {
    this.logger.debug(message, meta);
  }

  log(level: LogLevel, message: string, meta?: Record<string, any>): void {
    this.logger.log(level, message, meta);
  }

  // Helper methods for common logging patterns
  logError(error: Error, context?: Record<string, any>): void {
    this.error(error.message, {
      ...context,
      stack: error.stack,
      name: error.name,
    });
  }

  logWarning(message: string, context?: Record<string, any>): void {
    this.warn(message, context);
  }

  logInfo(message: string, context?: Record<string, any>): void {
    this.info(message, context);
  }

  logDebug(message: string, context?: Record<string, any>): void {
    this.debug(message, context);
  }

  // Performance logging
  logPerformance(operation: string, durationMs: number, context?: Record<string, any>): void {
    this.info(`Performance: ${operation} took ${durationMs}ms`, {
      ...context,
      operation,
      durationMs,
    });
  }

  // Request/Response logging
  logRequest(request: Record<string, any>, context?: Record<string, any>): void {
    this.debug('Incoming request', {
      ...context,
      request,
    });
  }

  logResponse(response: Record<string, any>, context?: Record<string, any>): void {
    this.debug('Outgoing response', {
      ...context,
      response,
    });
  }

  // State change logging
  logStateChange(from: string, to: string, context?: Record<string, any>): void {
    this.info(`State changed from ${from} to ${to}`, {
      ...context,
      from,
      to,
    });
  }

  // Metric logging
  logMetric(name: string, value: number, context?: Record<string, any>): void {
    this.debug(`Metric: ${name} = ${value}`, {
      ...context,
      name,
      value,
    });
  }
} 