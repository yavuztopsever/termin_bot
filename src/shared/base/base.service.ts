import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { LoggingService } from '../logging/logging.service';
import { ErrorService } from '../error/error.service';

@Injectable()
export abstract class BaseService {
  protected readonly logger: LoggingService;
  protected readonly errorService: ErrorService;

  constructor(
    protected readonly configService: ConfigService,
    loggingService: LoggingService,
    errorService: ErrorService,
    protected readonly serviceName: string
  ) {
    this.logger = loggingService;
    this.errorService = errorService;
  }

  protected logInfo(message: string, context?: string): void {
    this.logger.log(message, context || this.serviceName);
  }

  protected logError(message: string, error?: Error, context?: string): void {
    this.logger.error(message, error?.stack, context || this.serviceName);
  }

  protected logWarning(message: string, context?: string): void {
    this.logger.warn(message, context || this.serviceName);
  }

  protected handleServiceError(error: Error, context?: string): never {
    return this.errorService.handleError(error, context || this.serviceName);
  }

  protected getConfig<T>(key: string, defaultValue?: T): T {
    return this.configService.get<T>(key, defaultValue);
  }
} 