import { z } from 'zod';

export enum ServiceType {
  PASSPORT = 'PASSPORT',
  ID_CARD = 'ID_CARD',
  RESIDENCE_PERMIT = 'RESIDENCE_PERMIT',
  REGISTRATION = 'REGISTRATION',
  OTHER = 'OTHER'
}

export enum Location {
  BURGERAMT_NORD = '10187259',
  BURGERAMT_SUD = '10187261',
  BURGERAMT_WEST = '10187262',
  BURGERAMT_OST = '10187263'
}

export const BookingRequestSchema = z.object({
  serviceType: z.nativeEnum(ServiceType),
  location: z.nativeEnum(Location),
  fullName: z.string(),
  email: z.string().email(),
  serviceCount: z.number().min(1)
});

export type BookingRequest = z.infer<typeof BookingRequestSchema>;

export interface BookingResult {
  success: boolean;
  appointments?: Array<{
    id: string;
    date: string;
    time: string;
    status: string;
  }>;
  error?: string;
}

export interface Appointment {
  id: string;
  date: string;
  time: string;
  location: string;
  serviceType: ServiceType;
  available: boolean;
}

export enum AppointmentStatus {
  AVAILABLE = 'AVAILABLE',
  BOOKED = 'BOOKED',
  CANCELLED = 'CANCELLED',
  PENDING = 'PENDING'
}

export interface BookingStrategy {
  type: 'API' | 'BROWSER';
  priority: number;
} 