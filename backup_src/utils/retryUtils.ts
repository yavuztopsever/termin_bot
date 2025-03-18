import { logger } from '../services/loggingService';

export interface RetryOptions {
  initialDelayMs: number;
  maxDelayMs: number;
  maxRetries: number;
  jitterFactor: number;
  retryableStatusCodes?: number[];
}

export const defaultRetryOptions: RetryOptions = {
  initialDelayMs: 1000,
  maxDelayMs: 30000,
  maxRetries: 3,
  jitterFactor: 0.3,
  retryableStatusCodes: [408, 429, 500, 502, 503, 504]
};

/**
 * Calculates the delay for the next retry attempt using exponential backoff with jitter
 */
export function calculateBackoffDelay(retryCount: number, options: RetryOptions): number {
  // Calculate base exponential delay: initialDelay * 2^retryCount
  const exponentialDelay = options.initialDelayMs * Math.pow(2, retryCount);
  
  // Apply jitter: random value between (1-jitterFactor) and (1+jitterFactor) of the exponential delay
  const jitterMultiplier = 1 + options.jitterFactor * (Math.random() * 2 - 1);
  const delayWithJitter = exponentialDelay * jitterMultiplier;
  
  // Ensure delay is within bounds
  return Math.min(options.maxDelayMs, Math.max(options.initialDelayMs, delayWithJitter));
}

/**
 * Executes a function with retry logic using exponential backoff with jitter
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: Partial<RetryOptions> = {},
  operationName = 'operation'
): Promise<T> {
  const retryOptions = { ...defaultRetryOptions, ...options };
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retryOptions.maxRetries; attempt++) {
    try {
      // Execute the operation
      return await operation();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Check if we've exhausted retries
      if (attempt >= retryOptions.maxRetries) {
        logger.error(`${operationName} failed after ${attempt + 1} attempts: ${lastError.message}`);
        throw lastError;
      }
      
      // Check if error is retryable (for HTTP errors)
      if ('status' in lastError && retryOptions.retryableStatusCodes) {
        const status = (lastError as any).status;
        if (!retryOptions.retryableStatusCodes.includes(status)) {
          logger.warn(`${operationName} failed with non-retryable status code ${status}`);
          throw lastError;
        }
      }
      
      // Calculate delay for next retry
      const delay = calculateBackoffDelay(attempt, retryOptions);
      logger.warn(`${operationName} attempt ${attempt + 1} failed: ${lastError.message}. Retrying in ${delay}ms...`);
      
      // Wait before next retry
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // This should never be reached due to the throw in the loop
  throw lastError || new Error(`${operationName} failed for unknown reason`);
}
