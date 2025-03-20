export interface StateData {
  id: string;
  type: string;
  data: any;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface StateOptions {
  ttl?: number; // Time to live in milliseconds
  persistent?: boolean;
}

export interface StateQuery {
  type?: string;
  startTime?: number;
  endTime?: number;
  metadata?: Record<string, any>;
}

export interface StateStats {
  total: number;
  byType: Record<string, number>;
  oldest: number;
  newest: number;
}

export interface StateOperation {
  type: 'set' | 'get' | 'delete' | 'update';
  key: string;
  data?: any;
  options?: StateOptions;
} 