from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    
    # General settings
    enabled: bool = True
    environment: str = "development"
    
    # Default check settings
    default_interval: timedelta = timedelta(minutes=1)
    default_timeout: timedelta = timedelta(seconds=5)
    default_retries: int = 3
    default_retry_delay: timedelta = timedelta(seconds=1)
    
    # Component-specific settings
    database_check: Dict[str, Any] = None
    api_check: Dict[str, Any] = None
    cache_check: Dict[str, Any] = None
    
    # Threshold settings
    cpu_threshold: float = 90.0
    memory_threshold: float = 90.0
    disk_threshold: float = 90.0
    
    # Alert settings
    alert_on_failure: bool = True
    alert_on_recovery: bool = True
    alert_cooldown: timedelta = timedelta(minutes=5)
    
    # Performance settings
    max_concurrent_checks: int = 5
    check_batch_size: int = 10
    check_queue_size: int = 100
    
    # Cleanup settings
    status_retention: timedelta = timedelta(days=7)
    cleanup_interval: timedelta = timedelta(hours=1)
    cleanup_batch_size: int = 100
    
    def __post_init__(self):
        """Initialize component-specific settings."""
        if self.database_check is None:
            self.database_check = {
                "enabled": True,
                "interval": self.default_interval,
                "timeout": self.default_timeout,
                "retries": self.default_retries,
                "retry_delay": self.default_retry_delay,
                "check_connection": True,
                "check_query": True,
                "check_pool": True
            }
            
        if self.api_check is None:
            self.api_check = {
                "enabled": True,
                "interval": self.default_interval,
                "timeout": self.default_timeout,
                "retries": self.default_retries,
                "retry_delay": self.default_retry_delay,
                "check_endpoint": True,
                "check_auth": True,
                "check_rate_limit": True
            }
            
        if self.cache_check is None:
            self.cache_check = {
                "enabled": True,
                "interval": self.default_interval,
                "timeout": self.default_timeout,
                "retries": self.default_retries,
                "retry_delay": self.default_retry_delay,
                "check_connection": True,
                "check_operations": True,
                "check_memory": True
            }
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "environment": self.environment,
            "default_interval": str(self.default_interval),
            "default_timeout": str(self.default_timeout),
            "default_retries": self.default_retries,
            "default_retry_delay": str(self.default_retry_delay),
            "database_check": self.database_check,
            "api_check": self.api_check,
            "cache_check": self.cache_check,
            "cpu_threshold": self.cpu_threshold,
            "memory_threshold": self.memory_threshold,
            "disk_threshold": self.disk_threshold,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_recovery": self.alert_on_recovery,
            "alert_cooldown": str(self.alert_cooldown),
            "max_concurrent_checks": self.max_concurrent_checks,
            "check_batch_size": self.check_batch_size,
            "check_queue_size": self.check_queue_size,
            "status_retention": str(self.status_retention),
            "cleanup_interval": str(self.cleanup_interval),
            "cleanup_batch_size": self.cleanup_batch_size
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthCheckConfig':
        """Create configuration from dictionary."""
        # Convert string durations to timedelta
        duration_fields = [
            "default_interval", "default_timeout", "default_retry_delay",
            "alert_cooldown", "status_retention", "cleanup_interval"
        ]
        
        for field in duration_fields:
            if field in data and isinstance(data[field], str):
                data[field] = timedelta.fromisoformat(data[field])
                
        return cls(**data)
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        # Convert string durations to timedelta
        duration_fields = [
            "default_interval", "default_timeout", "default_retry_delay",
            "alert_cooldown", "status_retention", "cleanup_interval"
        ]
        
        for field in duration_fields:
            if field in data and isinstance(data[field], str):
                data[field] = timedelta.fromisoformat(data[field])
                
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
        # Reinitialize component settings
        self.__post_init__()

# Default configuration
DEFAULT_CONFIG = HealthCheckConfig()

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": HealthCheckConfig(
        environment="development",
        default_interval=timedelta(minutes=5),
        default_timeout=timedelta(seconds=10),
        alert_cooldown=timedelta(minutes=10),
        status_retention=timedelta(days=3)
    ),
    
    "testing": HealthCheckConfig(
        environment="testing",
        default_interval=timedelta(minutes=2),
        default_timeout=timedelta(seconds=5),
        alert_cooldown=timedelta(minutes=5),
        status_retention=timedelta(days=1)
    ),
    
    "production": HealthCheckConfig(
        environment="production",
        default_interval=timedelta(minutes=1),
        default_timeout=timedelta(seconds=3),
        alert_cooldown=timedelta(minutes=5),
        status_retention=timedelta(days=7),
        max_concurrent_checks=10,
        check_batch_size=20,
        check_queue_size=200
    )
} 