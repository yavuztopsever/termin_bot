export interface BookingRequest {
  date: string;
  time: string;
  userId: string;
  serviceId?: string;
  officeId?: string;
  serviceCount?: number;
  metadata?: Record<string, any>;
} 