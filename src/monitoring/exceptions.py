from src.exceptions import BaseError

class MonitoringError(Exception):
    """Base exception for monitoring-related errors."""
    pass

class MonitoringInitializationError(MonitoringError):
    """Raised when there is an error initializing the monitoring manager."""
    pass

class MonitoringMetricError(MonitoringError):
    """Raised when there is an error with metrics."""
    pass

class MonitoringAlertError(MonitoringError):
    """Raised when there is an error with alerts."""
    pass

class MonitoringThresholdError(MonitoringError):
    """Raised when there is an error with metric thresholds."""
    pass

class MonitoringStorageError(MonitoringError):
    """Raised when there is an error storing or retrieving monitoring data."""
    pass

class MonitoringCleanupError(MonitoringError):
    """Raised when there is an error cleaning up old monitoring data."""
    pass

class MonitoringNotificationError(MonitoringError):
    """Raised when there is an error sending monitoring notifications."""
    pass

class MonitoringConfigurationError(MonitoringError):
    """Raised when there is an error with monitoring configuration."""
    pass

class MonitoringRateLimitError(MonitoringError):
    """Raised when the monitoring rate limit is exceeded."""
    pass

class MonitoringTimeoutError(MonitoringError):
    """Raised when a monitoring operation times out."""
    pass

class MonitoringValidationError(MonitoringError):
    """Raised when there is an error validating monitoring data."""
    pass

class MonitoringBackendError(MonitoringError):
    """Raised when there is an error with the monitoring backend."""
    pass

class MonitoringConnectionError(MonitoringError):
    """Raised when there is an error connecting to monitoring services."""
    pass

class MonitoringOperationError(MonitoringError):
    """Raised when there is an error performing a monitoring operation."""
    pass

class MetricsError(MonitoringError):
    """Exception raised for errors in metrics collection and reporting."""
    pass

class HealthCheckError(MonitoringError):
    """Exception raised for errors in health checks."""
    pass

class PrometheusError(MetricsError):
    """Exception raised for errors in Prometheus metrics."""
    pass

class MetricsInitializationError(MetricsError):
    """Exception raised when metrics initialization fails."""
    pass

class MetricsCollectionError(MetricsError):
    """Exception raised when metrics collection fails."""
    pass

class MetricsReportingError(MetricsError):
    """Exception raised when metrics reporting fails."""
    pass

class HealthCheckInitializationError(HealthCheckError):
    """Exception raised when health check initialization fails."""
    pass

class HealthCheckExecutionError(HealthCheckError):
    """Exception raised when health check execution fails."""
    pass

class ComponentHealthError(HealthCheckError):
    """Exception raised when a component health check fails."""
    pass

class SystemHealthError(ComponentHealthError):
    """Exception raised when system health check fails."""
    pass

class DatabaseHealthError(ComponentHealthError):
    """Exception raised when database health check fails."""
    pass

class APIHealthError(ComponentHealthError):
    """Exception raised when API health check fails."""
    pass

class CacheHealthError(ComponentHealthError):
    """Exception raised when cache health check fails."""
    pass

class MonitoringConfigError(MonitoringError):
    """Exception raised for errors in monitoring configuration."""
    pass

class AlertError(MonitoringError):
    """Exception raised for errors in alerting system."""
    pass

class AlertInitializationError(AlertError):
    """Exception raised when alert system initialization fails."""
    pass

class AlertDeliveryError(AlertError):
    """Exception raised when alert delivery fails."""
    pass

class AlertConfigurationError(AlertError):
    """Exception raised when alert configuration is invalid."""
    pass

class MetricsValidationError(MetricsError):
    """Exception raised when metrics validation fails."""
    pass

class MetricsStorageError(MetricsError):
    """Exception raised when metrics storage operations fail."""
    pass

class MetricsRetentionError(MetricsError):
    """Exception raised when metrics retention operations fail."""
    pass

class HealthCheckTimeoutError(HealthCheckError):
    """Exception raised when a health check times out."""
    pass

class HealthCheckRetryError(HealthCheckError):
    """Exception raised when health check retries are exhausted."""
    pass

class ComponentRegistrationError(HealthCheckError):
    """Exception raised when component registration fails."""
    pass

class MonitoringManagerError(MonitoringError):
    """Exception raised for errors in monitoring manager."""
    pass

class MonitoringManagerInitializationError(MonitoringManagerError):
    """Exception raised when monitoring manager initialization fails."""
    pass

class MonitoringManagerShutdownError(MonitoringManagerError):
    """Exception raised when monitoring manager shutdown fails."""
    pass

class MonitoringContextError(MonitoringError):
    """Exception raised for errors in monitoring context."""
    pass

class MonitoringContextInitializationError(MonitoringContextError):
    """Exception raised when monitoring context initialization fails."""
    pass

class MonitoringContextCleanupError(MonitoringContextError):
    """Exception raised when monitoring context cleanup fails."""
    pass 