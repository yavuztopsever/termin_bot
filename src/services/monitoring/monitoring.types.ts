export interface Metric {
  name: string;
  value: number;
  timestamp: Date;
  tags?: Record<string, string>;
}

export interface Error {
  message: string;
  stack?: string;
  timestamp: Date;
  tags?: Record<string, string>;
}

export interface MonitoringConfig {
  endpoint?: string;
  maxMetrics: number;
  flushInterval: number;
  enabled: boolean;
  tags?: Record<string, string>;
}

export interface MonitoringStats {
  totalMetrics: number;
  totalErrors: number;
  lastFlushTime?: Date;
  lastErrorTime?: Date;
  recordsByTag: Record<string, number>;
  errorsByTag: Record<string, number>;
} 