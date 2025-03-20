import { Injectable, NotFoundException, BadRequestException, ConflictException } from '@nestjs/common';
import { ApiClientService } from '../shared/api-client/api-client.service';
import { CacheService } from '../shared/cache/cache.service';
import { LoggerService } from '../shared/logger/logger.service';
import { SearchAppointmentDto } from './dto/search-appointment.dto';
import { BookAppointmentDto } from './dto/book-appointment.dto';

@Injectable()
export class AppointmentService {
  constructor(
    private readonly apiClient: ApiClientService,
    private readonly cacheService: CacheService,
    private readonly logger: LoggerService
  ) {}

  async searchAppointments(searchDto: SearchAppointmentDto) {
    try {
      // Check cache first
      const cacheKey = `appointments:${JSON.stringify(searchDto)}`;
      const cachedResults = await this.cacheService.get(cacheKey);
      
      if (cachedResults) {
        this.logger.debug('Returning cached appointment results');
        return cachedResults;
      }

      // Call external API to search appointments
      const appointments = await this.apiClient.searchAppointments(searchDto);
      
      // Cache results for 5 minutes
      await this.cacheService.set(cacheKey, appointments, 300);
      
      return appointments;
    } catch (error) {
      this.logger.error('Error searching appointments', error);
      throw new BadRequestException('Failed to search appointments');
    }
  }

  async bookAppointment(bookingDto: BookAppointmentDto) {
    try {
      // Check if appointment is still available
      const isAvailable = await this.apiClient.checkAppointmentAvailability(
        bookingDto.appointmentDateTime
      );

      if (!isAvailable) {
        throw new ConflictException('Appointment is no longer available');
      }

      // Book the appointment
      const bookingResult = await this.apiClient.bookAppointment(bookingDto);
      
      // Invalidate relevant caches
      await this.cacheService.deletePattern('appointments:*');
      
      return bookingResult;
    } catch (error) {
      this.logger.error('Error booking appointment', error);
      if (error instanceof ConflictException) {
        throw error;
      }
      throw new BadRequestException('Failed to book appointment');
    }
  }

  async getAppointmentStatus(id: string) {
    try {
      const status = await this.apiClient.getAppointmentStatus(id);
      
      if (!status) {
        throw new NotFoundException('Appointment not found');
      }
      
      return status;
    } catch (error) {
      this.logger.error('Error getting appointment status', error);
      if (error instanceof NotFoundException) {
        throw error;
      }
      throw new BadRequestException('Failed to get appointment status');
    }
  }
} 