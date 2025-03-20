import { z } from 'zod';
import { BaseConfig, BaseService } from './base';

export const ErrorConfigSchema = BaseConfig.extend({
  logErrors: z.boolean(),
  notifyErrors: z.boolean(),
  retryEnabled: z.boolean(),
  maxRetries: z.number(),
  retryDelay: z.number(),
});

export type ErrorConfig = z.infer<typeof ErrorConfigSchema>;

export interface ErrorService extends BaseService {
  handleError(error: Error): Promise<void>;
  handleValidationError(error: ValidationError): Promise<void>;
  handleNetworkError(error: NetworkError): Promise<void>;
  handleDatabaseError(error: DatabaseError): Promise<void>;
  handleAuthenticationError(error: AuthenticationError): Promise<void>;
  handleAuthorizationError(error: AuthorizationError): Promise<void>;
  handleNotFoundError(error: NotFoundError): Promise<void>;
  handleConflictError(error: ConflictError): Promise<void>;
  handleRateLimitError(error: RateLimitError): Promise<void>;
  handleTimeoutError(error: TimeoutError): Promise<void>;
  handleServiceUnavailableError(error: ServiceUnavailableError): Promise<void>;
  handleBadRequestError(error: BadRequestError): Promise<void>;
  handleInternalServerError(error: InternalServerError): Promise<void>;
  handleUnsupportedMediaTypeError(error: UnsupportedMediaTypeError): Promise<void>;
  handleTooManyRequestsError(error: TooManyRequestsError): Promise<void>;
  handleGatewayTimeoutError(error: GatewayTimeoutError): Promise<void>;
  handleBadGatewayError(error: BadGatewayError): Promise<void>;
  handleNotImplementedError(error: NotImplementedError): Promise<void>;
  handleMethodNotAllowedError(error: MethodNotAllowedError): Promise<void>;
  handleUnprocessableEntityError(error: UnprocessableEntityError): Promise<void>;
  handleForbiddenError(error: ForbiddenError): Promise<void>;
  handleUnauthorizedError(error: UnauthorizedError): Promise<void>;
  handlePaymentRequiredError(error: PaymentRequiredError): Promise<void>;
  handleGoneError(error: GoneError): Promise<void>;
  handleLengthRequiredError(error: LengthRequiredError): Promise<void>;
  handlePreconditionFailedError(error: PreconditionFailedError): Promise<void>;
  handlePayloadTooLargeError(error: PayloadTooLargeError): Promise<void>;
  handleUriTooLongError(error: UriTooLongError): Promise<void>;
  handleUnsupportedMediaTypeError(error: UnsupportedMediaTypeError): Promise<void>;
  handleRangeNotSatisfiableError(error: RangeNotSatisfiableError): Promise<void>;
  handleExpectationFailedError(error: ExpectationFailedError): Promise<void>;
  handleIAmATeapotError(error: IAmATeapotError): Promise<void>;
  handleMisdirectedRequestError(error: MisdirectedRequestError): Promise<void>;
  handleLockedError(error: LockedError): Promise<void>;
  handleFailedDependencyError(error: FailedDependencyError): Promise<void>;
  handleTooEarlyError(error: TooEarlyError): Promise<void>;
  handleUpgradeRequiredError(error: UpgradeRequiredError): Promise<void>;
  handlePreconditionRequiredError(error: PreconditionRequiredError): Promise<void>;
  handleTooManyRequestsError(error: TooManyRequestsError): Promise<void>;
  handleRequestHeaderFieldsTooLargeError(error: RequestHeaderFieldsTooLargeError): Promise<void>;
  handleUnavailableForLegalReasonsError(error: UnavailableForLegalReasonsError): Promise<void>;
  handleInternalServerError(error: InternalServerError): Promise<void>;
  handleNotImplementedError(error: NotImplementedError): Promise<void>;
  handleBadGatewayError(error: BadGatewayError): Promise<void>;
  handleServiceUnavailableError(error: ServiceUnavailableError): Promise<void>;
  handleGatewayTimeoutError(error: GatewayTimeoutError): Promise<void>;
  handleHttpVersionNotSupportedError(error: HttpVersionNotSupportedError): Promise<void>;
  handleVariantAlsoNegotiatesError(error: VariantAlsoNegotiatesError): Promise<void>;
  handleInsufficientStorageError(error: InsufficientStorageError): Promise<void>;
  handleLoopDetectedError(error: LoopDetectedError): Promise<void>;
  handleNotExtendedError(error: NotExtendedError): Promise<void>;
  handleNetworkAuthenticationRequiredError(error: NetworkAuthenticationRequiredError): Promise<void>;
}

export interface BaseError extends Error {
  code: string;
  statusCode: number;
  details?: Record<string, unknown>;
  timestamp: Date;
  stack?: string;
}

export interface ValidationError extends BaseError {
  code: 'VALIDATION_ERROR';
  statusCode: 400;
  field?: string;
  value?: unknown;
  constraints?: string[];
}

export interface NetworkError extends BaseError {
  code: 'NETWORK_ERROR';
  statusCode: 503;
  url?: string;
  method?: string;
  response?: unknown;
}

export interface DatabaseError extends BaseError {
  code: 'DATABASE_ERROR';
  statusCode: 500;
  query?: string;
  params?: unknown[];
}

export interface AuthenticationError extends BaseError {
  code: 'AUTHENTICATION_ERROR';
  statusCode: 401;
  credentials?: unknown;
}

export interface AuthorizationError extends BaseError {
  code: 'AUTHORIZATION_ERROR';
  statusCode: 403;
  permissions?: string[];
  roles?: string[];
}

export interface NotFoundError extends BaseError {
  code: 'NOT_FOUND_ERROR';
  statusCode: 404;
  resource?: string;
  id?: string | number;
}

export interface ConflictError extends BaseError {
  code: 'CONFLICT_ERROR';
  statusCode: 409;
  resource?: string;
  id?: string | number;
}

export interface RateLimitError extends BaseError {
  code: 'RATE_LIMIT_ERROR';
  statusCode: 429;
  limit?: number;
  remaining?: number;
  reset?: Date;
}

export interface TimeoutError extends BaseError {
  code: 'TIMEOUT_ERROR';
  statusCode: 504;
  timeout?: number;
}

export interface ServiceUnavailableError extends BaseError {
  code: 'SERVICE_UNAVAILABLE_ERROR';
  statusCode: 503;
  service?: string;
}

export interface BadRequestError extends BaseError {
  code: 'BAD_REQUEST_ERROR';
  statusCode: 400;
  message: string;
}

export interface InternalServerError extends BaseError {
  code: 'INTERNAL_SERVER_ERROR';
  statusCode: 500;
  message: string;
}

export interface UnsupportedMediaTypeError extends BaseError {
  code: 'UNSUPPORTED_MEDIA_TYPE_ERROR';
  statusCode: 415;
  contentType?: string;
}

export interface TooManyRequestsError extends BaseError {
  code: 'TOO_MANY_REQUESTS_ERROR';
  statusCode: 429;
  limit?: number;
  remaining?: number;
  reset?: Date;
}

export interface GatewayTimeoutError extends BaseError {
  code: 'GATEWAY_TIMEOUT_ERROR';
  statusCode: 504;
  timeout?: number;
}

export interface BadGatewayError extends BaseError {
  code: 'BAD_GATEWAY_ERROR';
  statusCode: 502;
  service?: string;
}

export interface NotImplementedError extends BaseError {
  code: 'NOT_IMPLEMENTED_ERROR';
  statusCode: 501;
  feature?: string;
}

export interface MethodNotAllowedError extends BaseError {
  code: 'METHOD_NOT_ALLOWED_ERROR';
  statusCode: 405;
  method?: string;
  allowedMethods?: string[];
}

export interface UnprocessableEntityError extends BaseError {
  code: 'UNPROCESSABLE_ENTITY_ERROR';
  statusCode: 422;
  errors?: ValidationError[];
}

export interface ForbiddenError extends BaseError {
  code: 'FORBIDDEN_ERROR';
  statusCode: 403;
  message: string;
}

export interface UnauthorizedError extends BaseError {
  code: 'UNAUTHORIZED_ERROR';
  statusCode: 401;
  message: string;
}

export interface PaymentRequiredError extends BaseError {
  code: 'PAYMENT_REQUIRED_ERROR';
  statusCode: 402;
  message: string;
}

export interface GoneError extends BaseError {
  code: 'GONE_ERROR';
  statusCode: 410;
  message: string;
}

export interface LengthRequiredError extends BaseError {
  code: 'LENGTH_REQUIRED_ERROR';
  statusCode: 411;
  message: string;
}

export interface PreconditionFailedError extends BaseError {
  code: 'PRECONDITION_FAILED_ERROR';
  statusCode: 412;
  message: string;
}

export interface PayloadTooLargeError extends BaseError {
  code: 'PAYLOAD_TOO_LARGE_ERROR';
  statusCode: 413;
  maxSize?: number;
}

export interface UriTooLongError extends BaseError {
  code: 'URI_TOO_LONG_ERROR';
  statusCode: 414;
  maxLength?: number;
}

export interface RangeNotSatisfiableError extends BaseError {
  code: 'RANGE_NOT_SATISFIABLE_ERROR';
  statusCode: 416;
  range?: string;
}

export interface ExpectationFailedError extends BaseError {
  code: 'EXPECTATION_FAILED_ERROR';
  statusCode: 417;
  message: string;
}

export interface IAmATeapotError extends BaseError {
  code: 'I_AM_A_TEAPOT_ERROR';
  statusCode: 418;
  message: string;
}

export interface MisdirectedRequestError extends BaseError {
  code: 'MISDIRECTED_REQUEST_ERROR';
  statusCode: 421;
  message: string;
}

export interface LockedError extends BaseError {
  code: 'LOCKED_ERROR';
  statusCode: 423;
  message: string;
}

export interface FailedDependencyError extends BaseError {
  code: 'FAILED_DEPENDENCY_ERROR';
  statusCode: 424;
  message: string;
}

export interface TooEarlyError extends BaseError {
  code: 'TOO_EARLY_ERROR';
  statusCode: 425;
  message: string;
}

export interface UpgradeRequiredError extends BaseError {
  code: 'UPGRADE_REQUIRED_ERROR';
  statusCode: 426;
  message: string;
}

export interface PreconditionRequiredError extends BaseError {
  code: 'PRECONDITION_REQUIRED_ERROR';
  statusCode: 428;
  message: string;
}

export interface RequestHeaderFieldsTooLargeError extends BaseError {
  code: 'REQUEST_HEADER_FIELDS_TOO_LARGE_ERROR';
  statusCode: 431;
  message: string;
}

export interface UnavailableForLegalReasonsError extends BaseError {
  code: 'UNAVAILABLE_FOR_LEGAL_REASONS_ERROR';
  statusCode: 451;
  message: string;
}

export interface HttpVersionNotSupportedError extends BaseError {
  code: 'HTTP_VERSION_NOT_SUPPORTED_ERROR';
  statusCode: 505;
  version?: string;
}

export interface VariantAlsoNegotiatesError extends BaseError {
  code: 'VARIANT_ALSO_NEGOTIATES_ERROR';
  statusCode: 506;
  message: string;
}

export interface InsufficientStorageError extends BaseError {
  code: 'INSUFFICIENT_STORAGE_ERROR';
  statusCode: 507;
  message: string;
}

export interface LoopDetectedError extends BaseError {
  code: 'LOOP_DETECTED_ERROR';
  statusCode: 508;
  message: string;
}

export interface NotExtendedError extends BaseError {
  code: 'NOT_EXTENDED_ERROR';
  statusCode: 510;
  message: string;
}

export interface NetworkAuthenticationRequiredError extends BaseError {
  code: 'NETWORK_AUTHENTICATION_REQUIRED_ERROR';
  statusCode: 511;
  message: string;
}

export interface ErrorHandler {
  handle(error: BaseError): Promise<void>;
}

export interface ErrorLogger {
  log(error: BaseError): Promise<void>;
}

export interface ErrorNotifier {
  notify(error: BaseError): Promise<void>;
}

export interface ErrorRetryStrategy {
  shouldRetry(error: BaseError): boolean;
  getRetryDelay(error: BaseError): number;
}

export interface ErrorContext {
  requestId?: string;
  userId?: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

export interface ErrorOptions {
  log?: boolean;
  notify?: boolean;
  retry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  context?: ErrorContext;
} 