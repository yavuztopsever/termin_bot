import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../../services/common/logging.service';
import { MonitoringService } from '../../services/monitoring/monitoring.service';
import { BookingRequest } from '../../types/appointment/booking-request';
import { BookingResult } from '../../types/appointment/booking-result';
import { validateBookingRequest, createBookingResult, isBookingAvailable } from './booking.utils';

@Injectable()
export class BookingService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
  ) {}

  async bookAppointment(request: BookingRequest): Promise<BookingResult> {
    try {
      this.loggingService.info('Starting appointment booking', { request });
      
      // Validate request
      if (!validateBookingRequest(request)) {
        return createBookingResult(false, 'Invalid booking request');
      }

      // Check availability
      if (!isBookingAvailable(request.date, request.time)) {
        return createBookingResult(false, 'Requested time slot is not available');
      }

      // TODO: Implement actual booking logic
      const result = createBookingResult(true, 'Appointment booked successfully');
      
      this.monitoringService.recordMetric({
        name: 'appointment_booking_completed',
        value: 1,
        timestamp: new Date(),
        tags: { success: 'true' }
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to book appointment', { request, error });
      this.monitoringService.recordError('appointment_booking_failed', error);
      return createBookingResult(false, 'Failed to book appointment');
    }
  }

  async checkAvailability(request: BookingRequest): Promise<BookingResult> {
    try {
      this.loggingService.info('Checking appointment availability', { request });
      
      // Validate request
      if (!validateBookingRequest(request)) {
        return createBookingResult(false, 'Invalid booking request');
      }

      // TODO: Implement actual availability check logic
      const result = {
        success: true,
        availableSlots: [
          {
            date: request.date,
            time: request.time,
            available: isBookingAvailable(request.date, request.time)
          }
        ]
      };
      
      this.monitoringService.recordMetric({
        name: 'appointment_availability_check_completed',
        value: 1,
        timestamp: new Date(),
        tags: { available: result.availableSlots[0].available.toString() }
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to check appointment availability', { request, error });
      this.monitoringService.recordError('appointment_availability_check_failed', error);
      return createBookingResult(false, 'Failed to check appointment availability');
    }
  }
} 