import { Module } from '@nestjs/common';
import { RateLimitService } from './rate-limit.service';
import { ConfigModule } from '../../config/config.module';
import { MonitoringModule } from '../monitoring/monitoring.module';

@Module({
  imports: [
    ConfigModule,
    MonitoringModule
  ],
  providers: [RateLimitService],
  exports: [RateLimitService]
})
export class RateLimitModule {} 