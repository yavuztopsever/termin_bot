import { Injectable } from '@nestjs/common';
import { DomainError, NotFoundError, ValidationError, BusinessRuleError, TechnicalError, ExternalServiceError } from '../../types/common/errors/domain-error';
import { LoggingService } from './logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';

@Injectable()
export class ErrorService {
  constructor(
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
  ) {}

  handleError(error: Error): void {
    if (error instanceof DomainError) {
      this.handleDomainError(error);
    } else {
      this.handleUnexpectedError(error);
    }
  }

  private handleDomainError(error: DomainError): void {
    this.loggingService.error(error.message, {
      code: error.code,
      context: error.context,
    });

    this.monitoringService.recordError(error.code, error);

    switch (error.constructor) {
      case NotFoundError:
        this.handleNotFoundError(error as NotFoundError);
        break;
      case ValidationError:
        this.handleValidationError(error as ValidationError);
        break;
      case BusinessRuleError:
        this.handleBusinessRuleError(error as BusinessRuleError);
        break;
      case TechnicalError:
        this.handleTechnicalError(error as TechnicalError);
        break;
      case ExternalServiceError:
        this.handleExternalServiceError(error as ExternalServiceError);
        break;
      default:
        this.handleUnexpectedError(error);
    }
  }

  private handleNotFoundError(error: NotFoundError): void {
    // Handle not found errors (e.g., retry with different parameters)
    this.loggingService.warn('Resource not found', {
      context: error.context,
    });
  }

  private handleValidationError(error: ValidationError): void {
    // Handle validation errors (e.g., notify user)
    this.loggingService.warn('Validation failed', {
      context: error.context,
    });
  }

  private handleBusinessRuleError(error: BusinessRuleError): void {
    // Handle business rule violations (e.g., notify business stakeholders)
    this.loggingService.error('Business rule violation', {
      context: error.context,
    });
  }

  private handleTechnicalError(error: TechnicalError): void {
    // Handle technical errors (e.g., retry with backoff)
    this.loggingService.error('Technical error occurred', {
      context: error.context,
    });
  }

  private handleExternalServiceError(error: ExternalServiceError): void {
    // Handle external service errors (e.g., circuit breaker)
    this.loggingService.error('External service error', {
      context: error.context,
    });
  }

  private handleUnexpectedError(error: Error): void {
    // Handle unexpected errors (e.g., alert on-call engineer)
    this.loggingService.error('Unexpected error occurred', {
      error: error.message,
      stack: error.stack,
    });

    this.monitoringService.recordError('UNEXPECTED_ERROR', error);
  }

  isRetryable(error: Error): boolean {
    if (error instanceof DomainError) {
      switch (error.constructor) {
        case NotFoundError:
          return false;
        case ValidationError:
          return false;
        case BusinessRuleError:
          return false;
        case TechnicalError:
          return true;
        case ExternalServiceError:
          return true;
        default:
          return false;
      }
    }
    return false;
  }

  getRetryDelay(error: Error): number {
    if (error instanceof TechnicalError || error instanceof ExternalServiceError) {
      // Implement exponential backoff
      return Math.min(1000 * Math.pow(2, this.getRetryCount(error)), 30000);
    }
    return 0;
  }

  private getRetryCount(error: Error): number {
    // In a real implementation, you would track retry counts in a persistent store
    return 0;
  }
} 