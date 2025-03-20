import { Module } from '@nestjs/common';
import { ApiService } from './api.service';
import { ConfigModule } from '../../config/config.module';
import { MonitoringModule } from '../../services/monitoring/monitoring.module';
import { RateLimitModule } from '../../services/rate-limit/rate-limit.module';

@Module({
  imports: [
    ConfigModule,
    MonitoringModule,
    RateLimitModule
  ],
  providers: [ApiService],
  exports: [ApiService]
})
export class ApiModule {} 