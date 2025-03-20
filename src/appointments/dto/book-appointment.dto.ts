import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsNotEmpty, IsEmail, IsNumber, Min } from 'class-validator';

export class BookAppointmentDto {
  @ApiProperty({ description: 'Full name of the person booking the appointment' })
  @IsString()
  @IsNotEmpty()
  fullName: string;

  @ApiProperty({ description: 'Email address for appointment confirmation' })
  @IsEmail()
  email: string;

  @ApiProperty({ description: 'Number of appointments to book' })
  @IsNumber()
  @Min(1)
  count: number;
} 