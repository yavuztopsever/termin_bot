import { Injectable } from '@nestjs/common';
import { ValidationError as ClassValidationError } from 'class-validator';
import { ValidationError } from '../../types/common/errors/domain-error';

@Injectable()
export class ValidationService {
  validate<T extends object>(dto: T): void {
    const errors = this.validateObject(dto);
    if (errors.length > 0) {
      throw new ValidationError('Validation failed', { errors });
    }
  }

  private validateObject<T extends object>(dto: T): ClassValidationError[] {
    const errors: ClassValidationError[] = [];
    
    // Validate required fields
    Object.keys(dto).forEach(key => {
      const value = dto[key];
      if (value === undefined || value === null) {
        errors.push({
          property: key,
          constraints: {
            required: `${key} is required`,
          },
        });
      }
    });

    // Validate field types
    Object.keys(dto).forEach(key => {
      const value = dto[key];
      if (value !== undefined && value !== null) {
        const type = typeof value;
        const expectedType = this.getExpectedType(dto, key);
        
        if (type !== expectedType) {
          errors.push({
            property: key,
            constraints: {
              type: `${key} must be of type ${expectedType}`,
            },
          });
        }
      }
    });

    return errors;
  }

  private getExpectedType<T extends object>(dto: T, key: string): string {
    // This is a simplified version. In a real implementation,
    // you would use reflection or a schema to get the expected type.
    const value = dto[key];
    if (Array.isArray(value)) {
      return 'array';
    }
    return typeof value;
  }

  validateString(value: string, rules: {
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    required?: boolean;
  }): void {
    const errors: string[] = [];

    if (rules.required && (!value || value.trim().length === 0)) {
      errors.push('Value is required');
    }

    if (value && rules.minLength && value.length < rules.minLength) {
      errors.push(`Value must be at least ${rules.minLength} characters long`);
    }

    if (value && rules.maxLength && value.length > rules.maxLength) {
      errors.push(`Value must not exceed ${rules.maxLength} characters`);
    }

    if (value && rules.pattern && !rules.pattern.test(value)) {
      errors.push('Value does not match the required pattern');
    }

    if (errors.length > 0) {
      throw new ValidationError('String validation failed', { errors });
    }
  }

  validateNumber(value: number, rules: {
    min?: number;
    max?: number;
    required?: boolean;
  }): void {
    const errors: string[] = [];

    if (rules.required && value === undefined) {
      errors.push('Value is required');
    }

    if (value !== undefined) {
      if (rules.min !== undefined && value < rules.min) {
        errors.push(`Value must be greater than or equal to ${rules.min}`);
      }

      if (rules.max !== undefined && value > rules.max) {
        errors.push(`Value must be less than or equal to ${rules.max}`);
      }
    }

    if (errors.length > 0) {
      throw new ValidationError('Number validation failed', { errors });
    }
  }

  validateDate(value: Date, rules: {
    min?: Date;
    max?: Date;
    required?: boolean;
  }): void {
    const errors: string[] = [];

    if (rules.required && !value) {
      errors.push('Value is required');
    }

    if (value) {
      if (rules.min && value < rules.min) {
        errors.push(`Date must be after ${rules.min}`);
      }

      if (rules.max && value > rules.max) {
        errors.push(`Date must be before ${rules.max}`);
      }
    }

    if (errors.length > 0) {
      throw new ValidationError('Date validation failed', { errors });
    }
  }
} 