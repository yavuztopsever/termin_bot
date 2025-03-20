import { Injectable, HttpException, HttpStatus } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { LoggingService } from '../logging/logging.service';

export interface ErrorResponse {
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
  path?: string;
  details?: Record<string, any>;
}

@Injectable()
export class ErrorService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService
  ) {}

  createHttpException(
    message: string,
    status: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR,
    details?: Record<string, any>
  ): HttpException {
    const errorResponse: ErrorResponse = {
      statusCode: status,
      message,
      error: HttpStatus[status],
      timestamp: new Date().toISOString(),
      details
    };

    this.loggingService.error(
      `HTTP Exception: ${message}`,
      undefined,
      'ErrorService'
    );

    return new HttpException(errorResponse, status);
  }

  handleError(error: Error, context?: string): never {
    this.loggingService.error(
      error.message,
      error.stack,
      context || 'ErrorService'
    );

    if (error instanceof HttpException) {
      throw error;
    }

    throw this.createHttpException(
      error.message,
      HttpStatus.INTERNAL_SERVER_ERROR,
      { originalError: error.name }
    );
  }

  isHttpException(error: any): error is HttpException {
    return error instanceof HttpException;
  }

  getErrorResponse(error: HttpException): ErrorResponse {
    return error.getResponse() as ErrorResponse;
  }
} 