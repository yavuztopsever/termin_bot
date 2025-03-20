import { Module } from '@nestjs/common';
import { BookingService } from './booking.service';
import { ApiClientModule } from '../../shared/api-client/api-client.module';
import { MonitoringModule } from '../monitoring/monitoring.module';

@Module({
  imports: [
    ApiClientModule,
    MonitoringModule
  ],
  providers: [BookingService],
  exports: [BookingService]
})
export class BookingModule {} 