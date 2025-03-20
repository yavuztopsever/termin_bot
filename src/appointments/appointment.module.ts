import { Module } from '@nestjs/common';
import { AppointmentController } from './appointment.controller';
import { AppointmentService } from './appointment.service';
import { BookingService } from './booking.service';
import { BookingUtils } from './booking.utils';
import { ApiClientModule } from '../shared/api-client/api-client.module';
import { CacheModule } from '../shared/cache/cache.module';
import { LoggerModule } from '../shared/logger/logger.module';

@Module({
  imports: [
    ApiClientModule,
    CacheModule,
    LoggerModule
  ],
  controllers: [AppointmentController],
  providers: [AppointmentService, BookingService, BookingUtils],
  exports: [AppointmentService, BookingService, BookingUtils]
})
export class AppointmentModule {} 