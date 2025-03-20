import { Appointment } from './appointment';

export interface BookingResult {
  success: boolean;
  message: string;
  appointment?: Appointment;
  availableSlots?: Array<{
    date: string;
    time: string;
    available: boolean;
  }>;
} 