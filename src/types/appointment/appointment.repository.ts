import { Appointment } from './appointment';

export interface AppointmentRepository {
  save(appointment: Appointment): Promise<Appointment>;
  findById(id: string): Promise<Appointment | null>;
  findByDateRange(startDate: Date, endDate: Date): Promise<Appointment[]>;
  findByUserId(userId: string): Promise<Appointment[]>;
  delete(id: string): Promise<void>;
} 