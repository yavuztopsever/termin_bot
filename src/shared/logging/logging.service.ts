import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class LoggingService {
  private readonly logger = new Logger(LoggingService.name);

  constructor(private readonly configService: ConfigService) {}

  log(message: string, context?: string): void {
    this.logger.log(`${context ? `[${context}] ` : ''}${message}`);
  }

  error(message: string, trace?: string, context?: string): void {
    this.logger.error(`${context ? `[${context}] ` : ''}${message}`, trace);
  }

  warn(message: string, context?: string): void {
    this.logger.warn(`${context ? `[${context}] ` : ''}${message}`);
  }

  debug(message: string, context?: string): void {
    this.logger.debug(`${context ? `[${context}] ` : ''}${message}`);
  }

  verbose(message: string, context?: string): void {
    this.logger.verbose(`${context ? `[${context}] ` : ''}${message}`);
  }
} 