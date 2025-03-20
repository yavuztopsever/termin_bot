import { Module } from '@nestjs/common';
import { ConfigModule } from '../config/config.module';
import { LoggingService } from './logging/logging.service';
import { RedisService } from './redis/redis.service';
import { PersistenceService } from './persistence/persistence.service';
import { NotificationService } from './notification/notification.service';
import { ValidationService } from './validation/validation.service';
import { ErrorService } from './error/error.service';
import { EventBus } from './events/event-bus';

@Module({
  imports: [ConfigModule],
  providers: [
    LoggingService,
    RedisService,
    PersistenceService,
    NotificationService,
    ValidationService,
    ErrorService,
    EventBus
  ],
  exports: [
    LoggingService,
    RedisService,
    PersistenceService,
    NotificationService,
    ValidationService,
    ErrorService,
    EventBus
  ]
})
export class SharedModule {} 