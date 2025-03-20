import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { LoggingService } from '../logging/logging.service';

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

@Injectable()
export class ValidationService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService
  ) {}

  validateEmail(email: string): ValidationError | null {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return {
        field: 'email',
        message: 'Invalid email format',
        code: 'INVALID_EMAIL'
      };
    }
    return null;
  }

  validatePhoneNumber(phone: string): ValidationError | null {
    const phoneRegex = /^\+?[\d\s-()]{10,}$/;
    if (!phoneRegex.test(phone)) {
      return {
        field: 'phone',
        message: 'Invalid phone number format',
        code: 'INVALID_PHONE'
      };
    }
    return null;
  }

  validateRequired(value: any, field: string): ValidationError | null {
    if (value === undefined || value === null || value === '') {
      return {
        field,
        message: `${field} is required`,
        code: 'REQUIRED_FIELD'
      };
    }
    return null;
  }

  validateMinLength(value: string, field: string, minLength: number): ValidationError | null {
    if (value.length < minLength) {
      return {
        field,
        message: `${field} must be at least ${minLength} characters long`,
        code: 'MIN_LENGTH'
      };
    }
    return null;
  }

  validateMaxLength(value: string, field: string, maxLength: number): ValidationError | null {
    if (value.length > maxLength) {
      return {
        field,
        message: `${field} must not exceed ${maxLength} characters`,
        code: 'MAX_LENGTH'
      };
    }
    return null;
  }

  validateNumeric(value: any, field: string): ValidationError | null {
    if (isNaN(Number(value))) {
      return {
        field,
        message: `${field} must be a number`,
        code: 'INVALID_NUMBER'
      };
    }
    return null;
  }

  validateDate(date: Date, field: string): ValidationError | null {
    if (isNaN(date.getTime())) {
      return {
        field,
        message: `${field} must be a valid date`,
        code: 'INVALID_DATE'
      };
    }
    return null;
  }
} 