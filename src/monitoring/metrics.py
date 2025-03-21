from typing import Dict, Any, Optional
import time
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.exposition import start_http_server

from src.config.config import PROMETHEUS_PORT, ENABLE_METRICS
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MetricsManager:
    """Manager for application metrics."""
    
    def __init__(self):
        """Initialize the metrics manager."""
        self._initialized = False
        self._metrics: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize metrics and start Prometheus server."""
        try:
            if ENABLE_METRICS:
                # Initialize Prometheus metrics
                self._initialize_prometheus_metrics()
                
                # Start Prometheus HTTP server
                start_http_server(PROMETHEUS_PORT)
                logger.info(f"Started Prometheus metrics server on port {PROMETHEUS_PORT}")
                
            self._initialized = True
            
        except Exception as e:
            logger.error("Failed to initialize metrics manager", error=str(e))
            
    def _initialize_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # API metrics
        self._metrics["api_requests_total"] = Counter(
            "api_requests_total",
            "Total number of API requests",
            ["endpoint", "method", "status"]
        )
        
        self._metrics["api_request_duration_seconds"] = Histogram(
            "api_request_duration_seconds",
            "API request duration in seconds",
            ["endpoint", "method"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Appointment metrics
        self._metrics["appointments_total"] = Counter(
            "appointments_total",
            "Total number of appointments",
            ["status"]
        )
        
        self._metrics["appointment_booking_duration_seconds"] = Histogram(
            "appointment_booking_duration_seconds",
            "Appointment booking duration in seconds",
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # Rate limiting metrics
        self._metrics["rate_limit_requests_total"] = Counter(
            "rate_limit_requests_total",
            "Total number of rate-limited requests",
            ["endpoint"]
        )
        
        self._metrics["rate_limit_exceeded_total"] = Counter(
            "rate_limit_exceeded_total",
            "Total number of rate limit exceeded events",
            ["endpoint"]
        )
        
        # Database metrics
        self._metrics["db_operations_total"] = Counter(
            "db_operations_total",
            "Total number of database operations",
            ["operation", "model"]
        )
        
        self._metrics["db_operation_duration_seconds"] = Histogram(
            "db_operation_duration_seconds",
            "Database operation duration in seconds",
            ["operation", "model"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
        )
        
        # Cache metrics
        self._metrics["cache_hits_total"] = Counter(
            "cache_hits_total",
            "Total number of cache hits",
            ["cache_type"]
        )
        
        self._metrics["cache_misses_total"] = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            ["cache_type"]
        )
        
        # Error metrics
        self._metrics["errors_total"] = Counter(
            "errors_total",
            "Total number of errors",
            ["type", "component"]
        )
        
        # System metrics
        self._metrics["memory_usage_bytes"] = Gauge(
            "memory_usage_bytes",
            "Current memory usage in bytes"
        )
        
        self._metrics["cpu_usage_percent"] = Gauge(
            "cpu_usage_percent",
            "Current CPU usage percentage"
        )
        
        # Health check metrics
        self._metrics["health_check_duration_seconds"] = Summary(
            "health_check_duration_seconds",
            "Health check duration in seconds",
            ["component"]
        )
        
    def increment(self, metric_name: str, **labels) -> None:
        """Increment a counter metric."""
        if not self._initialized or not ENABLE_METRICS:
            return
            
        try:
            if metric_name in self._metrics:
                self._metrics[metric_name].labels(**labels).inc()
        except Exception as e:
            logger.error(f"Failed to increment metric {metric_name}", error=str(e))
            
    def observe(self, metric_name: str, value: float, **labels) -> None:
        """Observe a value for a histogram or summary metric."""
        if not self._initialized or not ENABLE_METRICS:
            return
            
        try:
            if metric_name in self._metrics:
                self._metrics[metric_name].labels(**labels).observe(value)
        except Exception as e:
            logger.error(f"Failed to observe metric {metric_name}", error=str(e))
            
    def set(self, metric_name: str, value: float, **labels) -> None:
        """Set a value for a gauge metric."""
        if not self._initialized or not ENABLE_METRICS:
            return
            
        try:
            if metric_name in self._metrics:
                self._metrics[metric_name].labels(**labels).set(value)
        except Exception as e:
            logger.error(f"Failed to set metric {metric_name}", error=str(e))
            
    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float
    ) -> None:
        """Record an API request."""
        self.increment("api_requests_total", endpoint=endpoint, method=method, status=status)
        self.observe("api_request_duration_seconds", duration, endpoint=endpoint, method=method)
        
    def record_appointment(self, status: str, booking_duration: Optional[float] = None) -> None:
        """Record an appointment."""
        self.increment("appointments_total", status=status)
        if booking_duration is not None:
            self.observe("appointment_booking_duration_seconds", booking_duration)
            
    def record_rate_limit(self, endpoint: str, exceeded: bool = False) -> None:
        """Record a rate limit event."""
        if exceeded:
            self.increment("rate_limit_exceeded_total", endpoint=endpoint)
        else:
            self.increment("rate_limit_requests_total", endpoint=endpoint)
            
    def record_db_operation(
        self,
        operation: str,
        model: str,
        duration: float
    ) -> None:
        """Record a database operation."""
        self.increment("db_operations_total", operation=operation, model=model)
        self.observe("db_operation_duration_seconds", duration, operation=operation, model=model)
        
    def record_cache_event(self, cache_type: str, hit: bool) -> None:
        """Record a cache event."""
        if hit:
            self.increment("cache_hits_total", cache_type=cache_type)
        else:
            self.increment("cache_misses_total", cache_type=cache_type)
            
    def record_error(self, error_type: str, component: str) -> None:
        """Record an error."""
        self.increment("errors_total", type=error_type, component=component)
        
    def record_system_metrics(self, memory_bytes: int, cpu_percent: float) -> None:
        """Record system metrics."""
        self.set("memory_usage_bytes", memory_bytes)
        self.set("cpu_usage_percent", cpu_percent)
        
    def record_health_check(self, component: str, duration: float) -> None:
        """Record a health check."""
        self.observe("health_check_duration_seconds", duration, component=component)

# Create singleton instance
metrics_manager = MetricsManager() 