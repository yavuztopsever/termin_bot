import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsDateString, IsOptional, IsEnum } from 'class-validator';

export enum AppointmentType {
  PASSPORT = 'PASSPORT',
  VISA = 'VISA',
  RESIDENCE_PERMIT = 'RESIDENCE_PERMIT',
  OTHER = 'OTHER'
}

export class SearchAppointmentDto {
  @ApiProperty({ enum: AppointmentType, description: 'Type of appointment' })
  @IsEnum(AppointmentType)
  type: AppointmentType;

  @ApiProperty({ description: 'Preferred date for the appointment' })
  @IsDateString()
  preferredDate: string;

  @ApiProperty({ description: 'Preferred location for the appointment', required: false })
  @IsString()
  @IsOptional()
  location?: string;

  @ApiProperty({ description: 'Additional notes or requirements', required: false })
  @IsString()
  @IsOptional()
  notes?: string;
} 