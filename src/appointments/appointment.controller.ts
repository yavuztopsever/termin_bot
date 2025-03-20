import { Controller, Post, Body, Get, Param, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { AppointmentService } from './appointment.service';
import { SearchAppointmentDto } from './dto/search-appointment.dto';
import { BookAppointmentDto } from './dto/book-appointment.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('appointments')
@Controller('appointments')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class AppointmentController {
  constructor(private readonly appointmentService: AppointmentService) {}

  @Post('search')
  @ApiOperation({ summary: 'Search for available appointments' })
  @ApiResponse({ status: 200, description: 'Returns list of available appointments' })
  @ApiResponse({ status: 400, description: 'Invalid search criteria' })
  async searchAppointments(@Body() searchDto: SearchAppointmentDto) {
    return this.appointmentService.searchAppointments(searchDto);
  }

  @Post('book')
  @ApiOperation({ summary: 'Book an appointment' })
  @ApiResponse({ status: 201, description: 'Appointment booked successfully' })
  @ApiResponse({ status: 400, description: 'Invalid booking request' })
  @ApiResponse({ status: 409, description: 'Appointment no longer available' })
  async bookAppointment(@Body() bookingDto: BookAppointmentDto) {
    return this.appointmentService.bookAppointment(bookingDto);
  }

  @Get('status/:id')
  @ApiOperation({ summary: 'Get appointment status' })
  @ApiResponse({ status: 200, description: 'Returns appointment status' })
  @ApiResponse({ status: 404, description: 'Appointment not found' })
  async getAppointmentStatus(@Param('id') id: string) {
    return this.appointmentService.getAppointmentStatus(id);
  }
} 