export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  headers: Record<string, string>;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
}

export interface ApiRequest {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  params?: Record<string, any>;
  body?: any;
  headers?: Record<string, string>;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface ApiSession {
  id: string;
  token?: string;
  expiresAt?: Date;
  lastRequest?: Date;
} 