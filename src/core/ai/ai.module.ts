import { Module } from '@nestjs/common';
import { ConfigModule } from '../../config/config.module';
import { CommonModule } from '../../services/common/common.module';
import { AIService } from './ai.service';
import { AIServiceImpl } from './ai.service.impl';

@Module({
  imports: [
    ConfigModule,
    CommonModule,
  ],
  providers: [
    {
      provide: AIService,
      useClass: AIServiceImpl,
    },
  ],
  exports: [AIService],
})
export class AIModule {} 