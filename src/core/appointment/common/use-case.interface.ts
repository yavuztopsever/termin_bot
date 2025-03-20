export interface UseCase<TInput = void, TOutput = void> {
  execute(input: TInput): Promise<TOutput>;
}

export interface UseCaseContext {
  userId: string;
  sessionId: string;
  timestamp: Date;
}

export interface UseCaseResult<T> {
  success: boolean;
  data?: T;
  error?: Error;
} 