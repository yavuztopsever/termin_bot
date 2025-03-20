import { Injectable, NotFoundException } from '@nestjs/common';
import { BookingUtils } from './booking.utils';
import { MonitoringService } from '../infrastructure/monitoring/monitoring.service';

@Injectable()
export class BookingService {
  constructor(
    private readonly bookingUtils: BookingUtils,
    private readonly monitoringService: MonitoringService
  ) {}

  async findAvailableSlots(
    date: Date,
    duration: number
  ): Promise<Array<{ start: Date; end: Date }>> {
    if (this.bookingUtils.isWeekend(date)) {
      throw new Error('Cannot book appointments on weekends');
    }

    const startTime = new Date(date);
    startTime.setHours(9, 0, 0, 0); // Start at 9 AM

    const endTime = new Date(date);
    endTime.setHours(17, 0, 0, 0); // End at 5 PM

    const slots = this.bookingUtils.getAvailableTimeSlots(startTime, endTime, duration);
    
    // Filter out invalid slots
    const validSlots = slots.filter(slot => 
      this.bookingUtils.isValidTimeSlot(slot.start, slot.end) &&
      this.bookingUtils.isWorkingHours(slot.start)
    );

    this.monitoringService.incrementMetric('available_slots_found', validSlots.length);
    return validSlots;
  }

  async bookAppointment(
    date: Date,
    duration: number,
    userId: string
  ): Promise<{ start: Date; end: Date }> {
    const availableSlots = await this.findAvailableSlots(date, duration);
    
    if (availableSlots.length === 0) {
      this.monitoringService.logWarning('No available slots found', 'BookingService');
      throw new NotFoundException('No available slots found for the specified date and duration');
    }

    // For now, just take the first available slot
    const bookedSlot = availableSlots[0];
    
    this.monitoringService.incrementMetric('appointments_booked');
    this.monitoringService.logInfo(
      `Appointment booked for user ${userId} at ${this.bookingUtils.formatTimeSlot(bookedSlot.start, bookedSlot.end)}`,
      'BookingService'
    );

    return bookedSlot;
  }
} 