import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { Metric, Error, MonitoringConfig, MonitoringStats } from './monitoring.types';
import { LoggingService } from '../common/logging.service';

@Injectable()
export class MonitoringService {
  private readonly logger = new Logger(MonitoringService.name);
  private config: MonitoringConfig;
  private metrics: Metric[] = [];
  private errors: Error[] = [];
  private readonly maxMetrics: number;
  private readonly flushInterval: number;
  private stats: MonitoringStats = {
    totalMetrics: 0,
    totalErrors: 0,
    recordsByTag: {},
    errorsByTag: {}
  };

  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
  ) {
    this.config = this.loadConfig();
    const monitoringConfig = this.configService.get('monitoring');
    this.maxMetrics = monitoringConfig.maxMetrics || 1000;
    this.flushInterval = monitoringConfig.flushInterval || 60000; // 1 minute

    if (this.config.enabled) {
      this.startPeriodicFlush();
    }
  }

  private loadConfig(): MonitoringConfig {
    return {
      enabled: this.configService.get<boolean>('monitoring.enabled', true),
      logLevel: this.configService.get<'debug' | 'info' | 'warn' | 'error'>('monitoring.logLevel', 'info'),
      metricsEnabled: this.configService.get<boolean>('monitoring.metricsEnabled', true),
      errorsEnabled: this.configService.get<boolean>('monitoring.errorsEnabled', true),
      endpoint: this.configService.get('monitoring.endpoint'),
      tags: this.configService.get('monitoring.tags')
    };
  }

  async recordMetric(name: string, value: number, labels?: Record<string, string>): Promise<void> {
    if (!this.config.enabled || !this.config.metricsEnabled) return;

    try {
      const metric: Metric = {
        name,
        value,
        timestamp: Date.now(),
        labels,
      };

      this.metrics.push(metric);
      this.logger.debug(`Recorded metric: ${name} = ${value}`);

      // If we've reached the maximum number of metrics, flush them
      if (this.metrics.length >= this.maxMetrics) {
        this.flushMetrics();
      }

      // Update tag records
      if (metric.tags) {
        Object.entries(metric.tags).forEach(([tag, value]) => {
          const tagKey = `${tag}:${value}`;
          this.stats.recordsByTag[tagKey] = (this.stats.recordsByTag[tagKey] || 0) + 1;
        });
      }
    } catch (error) {
      this.logger.error(`Failed to record metric: ${error.message}`);
    }
  }

  async recordError(name: string, error: any, context?: Record<string, any>): Promise<void> {
    if (!this.config.enabled || !this.config.errorsEnabled) return;

    try {
      const errorRecord: Error = {
        name,
        message: error.message,
        timestamp: Date.now(),
        stack: error.stack,
        context,
      };

      this.errors.push(errorRecord);
      this.logger.error(`Recorded error: ${name} - ${error.message}`);
    } catch (err) {
      this.logger.error(`Failed to record error: ${err.message}`);
    }
  }

  async recordSuccess(name: string, context?: Record<string, any>): Promise<void> {
    await this.recordMetric(name, 1, context);
  }

  async getStats(): Promise<MonitoringStats> {
    const stats: MonitoringStats = {
      metrics: {
        total: this.metrics.length,
        byName: {},
      },
      errors: {
        total: this.errors.length,
        byName: {},
      },
    };

    // Calculate metrics by name
    for (const metric of this.metrics) {
      stats.metrics.byName[metric.name] = (stats.metrics.byName[metric.name] || 0) + 1;
    }

    // Calculate errors by name
    for (const error of this.errors) {
      stats.errors.byName[error.name] = (stats.errors.byName[error.name] || 0) + 1;
    }

    // Get last error and metric
    if (this.errors.length > 0) {
      stats.lastError = this.errors[this.errors.length - 1];
    }
    if (this.metrics.length > 0) {
      stats.lastMetric = this.metrics[this.metrics.length - 1];
    }

    return stats;
  }

  async clear(): Promise<void> {
    this.metrics = [];
    this.errors = [];
    this.logger.debug('Cleared monitoring data');
  }

  private async flushMetrics(): Promise<void> {
    if (this.metrics.length === 0) {
      return;
    }

    try {
      const metricsToFlush = [...this.metrics];
      this.metrics.length = 0;

      // Here you would typically send the metrics to your monitoring system
      // For example, DataDog, Prometheus, etc.
      await this.sendMetricsToMonitoringSystem(metricsToFlush);

      this.logger.debug('Metrics flushed successfully', {
        count: metricsToFlush.length,
      });
    } catch (error) {
      this.logger.error('Failed to flush metrics', { error });
      
      // Put the metrics back in the queue if flushing failed
      this.metrics.unshift(...this.metrics);
    }
  }

  private async sendMetricsToMonitoringSystem(metrics: Metric[]): Promise<void> {
    const monitoringConfig = this.configService.get('monitoring');
    const endpoint = monitoringConfig.endpoint;

    if (!endpoint) {
      this.logger.warn('No monitoring endpoint configured');
      return;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          metrics,
          timestamp: new Date().toISOString(),
          tags: monitoringConfig.tags
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      this.logger.error('Failed to send metrics to monitoring system', {
        error,
        endpoint,
      });
      throw error;
    }
  }

  // Helper methods for common metrics
  recordLatency(operation: string, durationMs: number): void {
    this.recordMetric(`${operation}_latency`, durationMs, { operation });
  }

  recordError(operation: string, errorType: string): void {
    this.recordMetric(`${operation}_error`, 1, { operation, errorType });
  }

  recordCount(operation: string, count: number): void {
    this.recordMetric(`${operation}_count`, count, { operation });
  }

  private startPeriodicFlush(): void {
    setInterval(() => this.flushMetrics(), this.flushInterval);
  }
} 