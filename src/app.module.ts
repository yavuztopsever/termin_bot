import { Module } from '@nestjs/common';
import { ConfigModule } from './config/config.module';
import { CoreModule } from './core/core.module';
import { AppointmentModule } from './appointments/appointment.module';

@Module({
  imports: [
    ConfigModule,
    CoreModule,
    AppointmentModule
  ],
  exports: [
    ConfigModule,
    CoreModule,
    AppointmentModule
  ]
})
export class AppModule {} 