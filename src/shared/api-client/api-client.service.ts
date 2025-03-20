import { Injectable, HttpException, HttpStatus } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { AxiosInstance } from 'axios';
import { BookingRequest, ServiceType, Location, Appointment } from '../../core/booking/booking.types';
import { BookingResult } from '../../core/booking/booking.types';
import { Logger } from '@nestjs/common';

@Injectable()
export class ApiClientService {
  private readonly client: AxiosInstance;
  private readonly baseUrl: string;
  private readonly logger: Logger;

  constructor(private readonly configService: ConfigService) {
    // Base URL for Munich's Bürgeramt API
    this.baseUrl = 'https://stadt.muenchen.de/buergerservice/api';
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; TerminBot/1.0;)'
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          throw new HttpException(
            error.response.data.message || 'API request failed',
            error.response.status
          );
        }
        throw new HttpException(
          'Failed to connect to Bürgeramt API',
          HttpStatus.INTERNAL_SERVER_ERROR
        );
      }
    );

    this.logger = new Logger(ApiClientService.name);
  }

  async searchAppointments(serviceType: ServiceType, location: Location): Promise<Appointment[]> {
    const response = await this.client.get(
      `/appointments/available/${serviceType}/${location}`
    );
    return response.data.appointments;
  }

  async checkAppointmentAvailability(date: string, serviceType: ServiceType, location: Location): Promise<boolean> {
    const response = await this.client.get(
      `/appointments/availability/${serviceType}/${location}/${date}`
    );
    return response.data.available;
  }

  async bookAppointment(bookingRequest: {
    appointmentId: string;
    personalInfo: {
      fullName: string;
      email: string;
    };
  }): Promise<BookingResult> {
    try {
      const response = await this.client.post('/appointments/book', {
        appointmentId: bookingRequest.appointmentId,
        personalInfo: bookingRequest.personalInfo
      });

      return {
        success: true,
        appointments: [response.data]
      };
    } catch (error) {
      this.logger.error('Failed to book appointment', error);
      throw error;
    }
  }

  async getAppointmentStatus(id: string) {
    const response = await this.client.get(`/appointments/${id}/status`);
    return response.data;
  }
} 