import { Injectable, ConflictException } from '@nestjs/common';
import { ApiClientService } from '../../shared/api-client/api-client.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { BookingRequest, BookingResult, Appointment, ServiceType, Location } from './booking.types';

@Injectable()
export class BookingService {
  constructor(
    private readonly apiClient: ApiClientService,
    private readonly monitoringService: MonitoringService
  ) {}

  async findAvailableAppointments(serviceType: ServiceType, location: Location): Promise<Appointment[]> {
    try {
      const appointments = await this.apiClient.searchAppointments(serviceType, location);
      await this.monitoringService.recordSuccess('appointment_search');
      return appointments.filter(appointment => appointment.available);
    } catch (error) {
      await this.monitoringService.recordError('appointment_search_failed', error);
      throw error;
    }
  }

  async bookAppointment(request: BookingRequest): Promise<BookingResult> {
    try {
      // Find available appointments
      const availableAppointments = await this.findAvailableAppointments(
        request.serviceType,
        request.location
      );

      if (availableAppointments.length < request.serviceCount) {
        throw new ConflictException('Not enough available appointments');
      }

      // Book the requested number of appointments
      const bookingPromises = availableAppointments
        .slice(0, request.serviceCount)
        .map(appointment => 
          this.apiClient.bookAppointment({
            appointmentId: appointment.id,
            personalInfo: {
              fullName: request.fullName,
              email: request.email
            }
          })
        );

      const results = await Promise.all(bookingPromises);
      
      return {
        success: true,
        appointments: results
      };
    } catch (error) {
      await this.monitoringService.recordError('appointment_booking_failed', error);
      throw error;
    }
  }

  async getAppointmentStatus(id: string): Promise<BookingResult> {
    try {
      const status = await this.apiClient.getAppointmentStatus(id);
      return {
        success: true,
        ...status
      };
    } catch (error) {
      await this.monitoringService.recordError('appointment_status_check_failed', error);
      return {
        success: false,
        error: 'Failed to get appointment status'
      };
    }
  }
} 