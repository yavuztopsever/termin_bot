import { Injectable } from '@nestjs/common';
import { DateTime } from 'luxon';

@Injectable()
export class BookingUtils {
  isValidTimeSlot(startTime: Date, endTime: Date): boolean {
    return startTime < endTime;
  }

  isWorkingHours(time: Date): boolean {
    const hour = time.getHours();
    return hour >= 9 && hour < 17; // Assuming working hours are 9 AM to 5 PM
  }

  isWeekend(time: Date): boolean {
    const day = time.getDay();
    return day === 0 || day === 6;
  }

  getAvailableTimeSlots(
    startTime: Date,
    endTime: Date,
    duration: number
  ): Array<{ start: Date; end: Date }> {
    const slots: Array<{ start: Date; end: Date }> = [];
    let currentTime = DateTime.fromJSDate(startTime);

    while (currentTime < DateTime.fromJSDate(endTime)) {
      const slotEnd = currentTime.plus({ minutes: duration });
      if (slotEnd <= DateTime.fromJSDate(endTime)) {
        slots.push({
          start: currentTime.toJSDate(),
          end: slotEnd.toJSDate()
        });
      }
      currentTime = currentTime.plus({ minutes: 30 });
    }

    return slots;
  }

  formatTimeSlot(startTime: Date, endTime: Date): string {
    return `${DateTime.fromJSDate(startTime).toFormat('HH:mm')} - ${DateTime.fromJSDate(endTime).toFormat('HH:mm')}`;
  }
} 