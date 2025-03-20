import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { StateData, StateOptions, StateQuery, StateStats, StateOperation } from './state.types';

@Injectable()
export class StateService {
  private state: Map<string, StateData> = new Map();
  private options: StateOptions;

  constructor(
    private readonly configService: ConfigService,
    private readonly monitoringService: MonitoringService,
  ) {
    this.options = this.loadOptions();
  }

  private loadOptions(): StateOptions {
    return {
      ttl: this.configService.get<number>('state.ttl', 3600000), // 1 hour default
      persistent: this.configService.get<boolean>('state.persistent', false),
    };
  }

  async set(key: string, data: any, options?: StateOptions): Promise<void> {
    try {
      const stateData: StateData = {
        id: key,
        type: typeof data,
        data,
        timestamp: Date.now(),
      };

      this.state.set(key, stateData);
      await this.monitoringService.recordMetric('state_set', 1);
    } catch (error) {
      await this.monitoringService.recordError('state_set_error', error);
      throw error;
    }
  }

  async get(key: string): Promise<any> {
    try {
      const stateData = this.state.get(key);
      if (!stateData) {
        return null;
      }

      if (this.isExpired(stateData)) {
        await this.delete(key);
        return null;
      }

      await this.monitoringService.recordMetric('state_get', 1);
      return stateData.data;
    } catch (error) {
      await this.monitoringService.recordError('state_get_error', error);
      throw error;
    }
  }

  async delete(key: string): Promise<void> {
    try {
      this.state.delete(key);
      await this.monitoringService.recordMetric('state_delete', 1);
    } catch (error) {
      await this.monitoringService.recordError('state_delete_error', error);
      throw error;
    }
  }

  async query(query: StateQuery): Promise<StateData[]> {
    try {
      return Array.from(this.state.values()).filter(data => {
        if (query.type && data.type !== query.type) return false;
        if (query.startTime && data.timestamp < query.startTime) return false;
        if (query.endTime && data.timestamp > query.endTime) return false;
        if (query.metadata) {
          return Object.entries(query.metadata).every(
            ([key, value]) => data.metadata?.[key] === value
          );
        }
        return true;
      });
    } catch (error) {
      await this.monitoringService.recordError('state_query_error', error);
      throw error;
    }
  }

  async getStats(): Promise<StateStats> {
    const stats: StateStats = {
      total: this.state.size,
      byType: {},
      oldest: Infinity,
      newest: 0,
    };

    for (const data of this.state.values()) {
      stats.byType[data.type] = (stats.byType[data.type] || 0) + 1;
      stats.oldest = Math.min(stats.oldest, data.timestamp);
      stats.newest = Math.max(stats.newest, data.timestamp);
    }

    return stats;
  }

  private isExpired(data: StateData): boolean {
    if (!this.options.ttl) return false;
    return Date.now() - data.timestamp > this.options.ttl;
  }
} 