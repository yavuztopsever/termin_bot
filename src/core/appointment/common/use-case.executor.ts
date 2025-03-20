import { Injectable } from '@nestjs/common';
import { LoggingService } from '../../../../services/common/logging.service';
import { MonitoringService } from '../../../../services/monitoring/monitoring.service';
import { ErrorService } from '../../../../services/common/error.service';

@Injectable()
export class UseCaseExecutorImpl {
  constructor(
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
    private readonly errorService: ErrorService,
  ) {}

  async execute<T>(useCase: () => Promise<T>, context: string): Promise<T> {
    const startTime = Date.now();
    
    try {
      this.loggingService.info(`Starting ${context}`);
      
      const result = await useCase();
      
      const duration = Date.now() - startTime;
      this.loggingService.info(`Completed ${context}`, { duration });
      this.monitoringService.recordLatency(context, duration);
      
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      this.loggingService.error(`Failed ${context}`, { error, duration });
      this.monitoringService.recordError(context, error);
      
      await this.errorService.handleError(error);
      throw error;
    }
  }
} 