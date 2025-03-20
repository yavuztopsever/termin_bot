import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { MonitoringService } from '../../services/monitoring/monitoring.service';
import { RateLimitService } from '../../services/rate-limit/rate-limit.service';
import { ApiConfig, ApiResponse, ApiRequest, ApiSession } from './api.types';
import { BookingRequest, BookingResult, Appointment } from '../booking/booking.types';
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

@Injectable()
export class ApiService {
  private readonly logger = new Logger(ApiService.name);
  private config: ApiConfig;
  private session: ApiSession;
  private client: AxiosInstance;

  constructor(
    private readonly configService: ConfigService,
    private readonly monitoringService: MonitoringService,
    private readonly rateLimitService: RateLimitService,
  ) {
    this.config = this.loadConfig();
    this.session = this.createSession();
    this.client = this.createClient();
  }

  private loadConfig(): ApiConfig {
    return {
      baseUrl: this.configService.get<string>('api.baseUrl'),
      timeout: this.configService.get<number>('api.timeout', 30000),
      retries: this.configService.get<number>('api.retries', 3),
      headers: this.configService.get<Record<string, string>>('api.headers', {}),
    };
  }

  private createSession(): ApiSession {
    return {
      id: Date.now().toString(),
      lastRequest: new Date(),
    };
  }

  private createClient(): AxiosInstance {
    return axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        ...this.config.headers,
        'Content-Type': 'application/json',
      },
    });
  }

  async bookAppointment(request: BookingRequest): Promise<BookingResult> {
    try {
      await this.rateLimitService.checkLimit('api');
      const response = await this.makeRequest({
        method: 'POST',
        path: '/appointments',
        body: request,
      });
      
      if (response.success) {
        return {
          success: true,
          appointment: response.data,
        };
      }

      return {
        success: false,
        error: response.error,
      };
    } catch (error) {
      await this.monitoringService.recordError('api_booking_error', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  async getAvailableAppointments(request: BookingRequest): Promise<Appointment[]> {
    try {
      await this.rateLimitService.checkLimit('api');
      const response = await this.makeRequest({
        method: 'GET',
        path: '/appointments/available',
        params: request,
      });

      return response.success ? response.data : [];
    } catch (error) {
      await this.monitoringService.recordError('api_availability_error', error);
      return [];
    }
  }

  private async makeRequest<T>(request: ApiRequest): Promise<ApiResponse<T>> {
    try {
      const config: AxiosRequestConfig = {
        method: request.method,
        url: request.path,
        params: request.params,
        data: request.body,
        headers: {
          ...this.config.headers,
          ...request.headers,
        },
      };

      const response = await this.client.request(config);
      this.session.lastRequest = new Date();

      return {
        success: true,
        data: response.data,
        statusCode: response.status,
      };
    } catch (error) {
      await this.monitoringService.recordError('api_request_error', error);
      
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        statusCode: error.response?.status,
      };
    }
  }

  async refreshSession(): Promise<void> {
    try {
      const response = await this.makeRequest({
        method: 'POST',
        path: '/auth/refresh',
      });

      if (response.success && response.data) {
        this.session = {
          ...this.session,
          token: response.data.token,
          expiresAt: new Date(Date.now() + response.data.expiresIn * 1000),
        };
      }
    } catch (error) {
      await this.monitoringService.recordError('api_session_refresh_error', error);
      throw error;
    }
  }
} 