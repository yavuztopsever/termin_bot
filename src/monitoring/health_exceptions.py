class HealthCheckError(Exception):
    """Base exception for health check errors."""
    pass

class HealthCheckInitializationError(HealthCheckError):
    """Raised when there is an error initializing the health check manager."""
    pass

class HealthCheckExecutionError(HealthCheckError):
    """Raised when there is an error executing a health check."""
    pass

class ComponentHealthError(HealthCheckError):
    """Raised when a component health check fails."""
    pass

class HealthCheckTimeoutError(HealthCheckError):
    """Raised when a health check times out."""
    pass

class HealthCheckRetryError(HealthCheckError):
    """Raised when a health check fails after all retries."""
    pass

class HealthCheckConfigurationError(HealthCheckError):
    """Raised when there is an error with health check configuration."""
    pass

class HealthCheckValidationError(HealthCheckError):
    """Raised when there is an error validating health check data."""
    pass

class HealthCheckRegistrationError(HealthCheckError):
    """Raised when there is an error registering a health check."""
    pass

class HealthCheckCleanupError(HealthCheckError):
    """Raised when there is an error cleaning up health check data."""
    pass

class HealthCheckStatusError(HealthCheckError):
    """Raised when there is an error updating health check status."""
    pass

class HealthCheckMetricError(HealthCheckError):
    """Raised when there is an error recording health check metrics."""
    pass

class HealthCheckAlertError(HealthCheckError):
    """Raised when there is an error creating health check alerts."""
    pass

class HealthCheckShutdownError(HealthCheckError):
    """Raised when there is an error shutting down the health check manager."""
    pass

class HealthCheckTaskError(HealthCheckError):
    """Raised when there is an error with health check tasks."""
    pass

class HealthCheckComponentNotFoundError(HealthCheckError):
    """Raised when a requested component is not found."""
    pass

class HealthCheckDisabledError(HealthCheckError):
    """Raised when health checks are disabled."""
    pass 