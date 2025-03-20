export enum MetricType {
  COUNTER = 'counter',
  GAUGE = 'gauge',
  HISTOGRAM = 'histogram'
}

export interface MetricLabels {
  [key: string]: string;
}

export interface MetricValue {
  value: number;
  timestamp: number;
  labels?: MetricLabels;
  type: MetricType;
}

export interface MetricDefinition {
  name: string;
  type: MetricType;
  description: string;
  labels?: string[];
  rateLimit?: number;
}

export const STANDARD_METRICS: Record<string, MetricDefinition> = {
  // Application metrics
  'app_startup_time': {
    name: 'app_startup_time',
    type: MetricType.GAUGE,
    description: 'Application startup time in milliseconds'
  },
  'app_memory_usage': {
    name: 'app_memory_usage',
    type: MetricType.GAUGE,
    description: 'Application memory usage in bytes'
  },

  // Appointment metrics
  'appointment_search_duration': {
    name: 'appointment_search_duration',
    type: MetricType.HISTOGRAM,
    description: 'Duration of appointment search in milliseconds',
    labels: ['type', 'status']
  },
  'appointment_booking_duration': {
    name: 'appointment_booking_duration',
    type: MetricType.HISTOGRAM,
    description: 'Duration of appointment booking in milliseconds',
    labels: ['type', 'status']
  },
  'appointment_availability_count': {
    name: 'appointment_availability_count',
    type: MetricType.GAUGE,
    description: 'Number of available appointments',
    labels: ['type']
  },

  // Rate limiting metrics
  'rate_limit_exceeded': {
    name: 'rate_limit_exceeded',
    type: MetricType.COUNTER,
    description: 'Number of rate limit violations',
    labels: ['endpoint', 'user_id']
  },

  // Error metrics
  'error_count': {
    name: 'error_count',
    type: MetricType.COUNTER,
    description: 'Number of errors encountered',
    labels: ['type', 'severity']
  },

  // Performance metrics
  'request_duration': {
    name: 'request_duration',
    type: MetricType.HISTOGRAM,
    description: 'Duration of HTTP requests in milliseconds',
    labels: ['method', 'endpoint', 'status']
  },
  'database_query_duration': {
    name: 'database_query_duration',
    type: MetricType.HISTOGRAM,
    description: 'Duration of database queries in milliseconds',
    labels: ['operation', 'table']
  }
}; 