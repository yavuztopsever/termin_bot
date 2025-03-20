import { Module } from '@nestjs/common';
import { MonitoringService } from './monitoring.service';
import { LoggingService } from '../common/logging.service';
import { ConfigModule } from '../../config/config.module';

@Module({
  imports: [ConfigModule],
  providers: [MonitoringService, LoggingService],
  exports: [MonitoringService]
})
export class MonitoringModule {} 