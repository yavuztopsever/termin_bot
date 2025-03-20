import { z } from 'zod';

export const ErrorContextSchema = z.record(z.unknown());

export type ErrorContext = z.infer<typeof ErrorContextSchema>;

export abstract class DomainError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly context: ErrorContext = {}
  ) {
    super(message);
    this.name = this.constructor.name;
  }

  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      context: this.context,
      stack: this.stack,
    };
  }
}

export class ValidationError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'VALIDATION_ERROR', context);
  }
}

export class NotFoundError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'NOT_FOUND', context);
  }
}

export class ConflictError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'CONFLICT', context);
  }
}

export class UnauthorizedError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'UNAUTHORIZED', context);
  }
}

export class ForbiddenError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'FORBIDDEN', context);
  }
}

export class BusinessRuleViolationError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'BUSINESS_RULE_VIOLATION', context);
  }
}

export class ExternalServiceError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'EXTERNAL_SERVICE_ERROR', context);
  }
}

export class InfrastructureError extends DomainError {
  constructor(message: string, context: ErrorContext = {}) {
    super(message, 'INFRASTRUCTURE_ERROR', context);
  }
}

export type DomainErrorType =
  | ValidationError
  | NotFoundError
  | ConflictError
  | UnauthorizedError
  | ForbiddenError
  | BusinessRuleViolationError
  | ExternalServiceError
  | InfrastructureError; 