import { AppointmentResponseDto, AppointmentStatus } from '../dtos/appointment.dto';

export interface AppointmentRepository {
  create(appointment: Omit<AppointmentResponseDto, 'id' | 'status' | 'createdAt' | 'updatedAt'>): Promise<AppointmentResponseDto>;
  findById(id: string): Promise<AppointmentResponseDto | null>;
  findByOfficeAndService(officeId: string, serviceId: string): Promise<AppointmentResponseDto[]>;
  updateStatus(id: string, status: AppointmentStatus): Promise<AppointmentResponseDto>;
  delete(id: string): Promise<void>;
  findAvailable(officeId: string, serviceId: string, startDate: Date, endDate: Date): Promise<AppointmentResponseDto[]>;
} 