import { IsString, IsDate, IsNumber, IsOptional, IsEnum } from 'class-validator';

export enum AppointmentStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  CANCELLED = 'CANCELLED',
  FAILED = 'FAILED'
}

export class CreateAppointmentDto {
  @IsString()
  officeId: string;

  @IsString()
  serviceId: string;

  @IsDate()
  date: Date;

  @IsString()
  time: string;

  @IsNumber()
  @IsOptional()
  partySize?: number;

  @IsString()
  @IsOptional()
  notes?: string;
}

export class BookAppointmentDto extends CreateAppointmentDto {
  @IsString()
  fullName: string;

  @IsString()
  email: string;

  @IsString()
  phoneNumber: string;
}

export class CancelAppointmentDto {
  @IsString()
  appointmentId: string;

  @IsString()
  @IsOptional()
  reason?: string;
}

export class FindAvailableAppointmentsDto {
  @IsString()
  officeId: string;

  @IsString()
  serviceId: string;

  @IsDate()
  startDate: Date;

  @IsDate()
  endDate: Date;

  @IsNumber()
  @IsOptional()
  partySize?: number;
}

export class AppointmentResponseDto {
  @IsString()
  id: string;

  @IsEnum(AppointmentStatus)
  status: AppointmentStatus;

  @IsDate()
  createdAt: Date;

  @IsDate()
  updatedAt: Date;

  @IsString()
  officeId: string;

  @IsString()
  serviceId: string;

  @IsDate()
  date: Date;

  @IsString()
  time: string;

  @IsNumber()
  @IsOptional()
  partySize?: number;

  @IsString()
  @IsOptional()
  notes?: string;

  @IsString()
  @IsOptional()
  fullName?: string;

  @IsString()
  @IsOptional()
  email?: string;

  @IsString()
  @IsOptional()
  phoneNumber?: string;
} 