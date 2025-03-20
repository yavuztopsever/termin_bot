import { z } from 'zod';

export const AppointmentMetadataSchema = z.object({
  userId: z.string().uuid().optional(),
  bookedBy: z.string().uuid().optional(),
  bookedAt: z.string().datetime().optional(),
  cancelledBy: z.string().uuid().optional(),
  cancelledAt: z.string().datetime().optional(),
  cancellationReason: z.string().optional(),
  notes: z.string().optional(),
  tags: z.array(z.string()).optional(),
  priority: z.enum(['low', 'medium', 'high']).optional(),
  status: z.enum(['pending', 'confirmed', 'cancelled', 'completed']).optional(),
  customFields: z.record(z.unknown()).optional(),
});

export type AppointmentMetadata = z.infer<typeof AppointmentMetadataSchema>;

export const AppointmentSchema = z.object({
  id: z.string().uuid(),
  type: z.string(),
  startTime: z.string().datetime(),
  endTime: z.string().datetime(),
  duration: z.number().positive(),
  location: z.string().optional(),
  description: z.string().optional(),
  metadata: AppointmentMetadataSchema,
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  version: z.number().positive(),
});

export type Appointment = z.infer<typeof AppointmentSchema>;

export interface AppointmentRepository {
  save(appointment: Appointment): Promise<void>;
  findById(id: string): Promise<Appointment | null>;
  findByUserId(userId: string): Promise<Appointment[]>;
  findByDateRange(startTime: Date, endTime: Date): Promise<Appointment[]>;
  delete(id: string): Promise<void>;
  update(id: string, appointment: Partial<Appointment>): Promise<void>;
}

export interface AppointmentService {
  createAppointment(data: Omit<Appointment, 'id' | 'createdAt' | 'updatedAt' | 'version'>): Promise<Appointment>;
  getAppointment(id: string): Promise<Appointment>;
  updateAppointment(id: string, data: Partial<Appointment>): Promise<Appointment>;
  deleteAppointment(id: string): Promise<void>;
  getAppointmentsByUser(userId: string): Promise<Appointment[]>;
  getAppointmentsByDateRange(startTime: Date, endTime: Date): Promise<Appointment[]>;
  cancelAppointment(id: string, reason?: string): Promise<Appointment>;
  confirmAppointment(id: string): Promise<Appointment>;
  rescheduleAppointment(id: string, newStartTime: Date, newEndTime: Date): Promise<Appointment>;
}

export interface AppointmentValidator {
  validateAppointment(appointment: Appointment): Promise<boolean>;
  validateAppointmentCreation(data: Omit<Appointment, 'id' | 'createdAt' | 'updatedAt' | 'version'>): Promise<boolean>;
  validateAppointmentUpdate(id: string, data: Partial<Appointment>): Promise<boolean>;
  validateAppointmentDeletion(id: string): Promise<boolean>;
  validateAppointmentCancellation(id: string, reason?: string): Promise<boolean>;
  validateAppointmentConfirmation(id: string): Promise<boolean>;
  validateAppointmentRescheduling(id: string, newStartTime: Date, newEndTime: Date): Promise<boolean>;
} 