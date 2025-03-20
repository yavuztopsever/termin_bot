import { Module } from '@nestjs/common';
import { ConfigModule } from '../../config/config.module';
import { LoggingService } from './logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { RedisService } from './redis.service';
import { PersistenceService } from './persistence.service';
import { NotificationService } from './notification.service';
import { ValidationService } from './validation.service';
import { ErrorService } from './error.service';

@Module({
  imports: [ConfigModule],
  providers: [
    LoggingService,
    MonitoringService,
    RedisService,
    PersistenceService,
    NotificationService,
    ValidationService,
    ErrorService
  ],
  exports: [
    LoggingService,
    MonitoringService,
    RedisService,
    PersistenceService,
    NotificationService,
    ValidationService,
    ErrorService
  ]
})
export class CommonModule {} 