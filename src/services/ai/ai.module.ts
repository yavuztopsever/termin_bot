import { Module } from '@nestjs/common';
import { CommonModule } from '../common/common.module';
import { AIService } from '../../core/ai/ai.service';
import { AIServiceImpl } from '../../infrastructure/ai/ai.service.impl';
import { LangchainAgentService } from './langchain-agent.service';

@Module({
  imports: [CommonModule],
  providers: [
    {
      provide: AIService,
      useClass: AIServiceImpl
    },
    LangchainAgentService
  ],
  exports: [AIService, LangchainAgentService]
})
export class AIModule {} 