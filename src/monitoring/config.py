from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class MonitoringConfig:
    """Configuration for monitoring system."""
    
    # Retention settings
    metrics_retention: timedelta = timedelta(days=7)
    alerts_retention: timedelta = timedelta(days=30)
    
    # Cleanup settings
    cleanup_interval: timedelta = timedelta(hours=1)
    cleanup_batch_size: int = 1000
    
    # Threshold settings
    metric_thresholds: Dict[str, Dict[str, float]] = None
    
    # Notification settings
    notify_on_critical: bool = True
    notify_on_error: bool = True
    notify_on_warning: bool = False
    
    # Performance settings
    max_metrics_per_second: int = 1000
    max_alerts_per_second: int = 100
    
    # Storage settings
    max_metrics_in_memory: int = 100000
    max_alerts_in_memory: int = 10000
    
    def __post_init__(self):
        """Initialize default metric thresholds if not set."""
        if self.metric_thresholds is None:
            self.metric_thresholds = {
                "api_response_time": {
                    "warning": 1.0,  # 1 second
                    "error": 2.0,    # 2 seconds
                    "critical": 5.0  # 5 seconds
                },
                "api_error_rate": {
                    "warning": 0.01,  # 1%
                    "error": 0.05,    # 5%
                    "critical": 0.1   # 10%
                },
                "cache_hit_rate": {
                    "warning": 0.8,   # 80%
                    "error": 0.6,     # 60%
                    "critical": 0.4   # 40%
                },
                "memory_usage": {
                    "warning": 70.0,  # 70%
                    "error": 85.0,    # 85%
                    "critical": 95.0  # 95%
                }
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "metrics_retention": str(self.metrics_retention),
            "alerts_retention": str(self.alerts_retention),
            "cleanup_interval": str(self.cleanup_interval),
            "cleanup_batch_size": self.cleanup_batch_size,
            "metric_thresholds": self.metric_thresholds,
            "notify_on_critical": self.notify_on_critical,
            "notify_on_error": self.notify_on_error,
            "notify_on_warning": self.notify_on_warning,
            "max_metrics_per_second": self.max_metrics_per_second,
            "max_alerts_per_second": self.max_alerts_per_second,
            "max_metrics_in_memory": self.max_metrics_in_memory,
            "max_alerts_in_memory": self.max_alerts_in_memory
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringConfig':
        """Create configuration from dictionary."""
        # Convert string durations to timedelta
        duration_fields = [
            "metrics_retention",
            "alerts_retention",
            "cleanup_interval"
        ]
        
        for field in duration_fields:
            if field in data and isinstance(data[field], str):
                data[field] = timedelta.fromisoformat(data[field])
                
        return cls(**data)
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in data.items():
            if hasattr(self, key):
                if key in [
                    "metrics_retention",
                    "alerts_retention",
                    "cleanup_interval"
                ] and isinstance(value, str):
                    value = timedelta.fromisoformat(value)
                setattr(self, key, value)

# Default configuration
DEFAULT_CONFIG = MonitoringConfig(
    metrics_retention=timedelta(days=7),
    alerts_retention=timedelta(days=30),
    cleanup_interval=timedelta(hours=1),
    cleanup_batch_size=1000,
    notify_on_critical=True,
    notify_on_error=True,
    notify_on_warning=False,
    max_metrics_per_second=1000,
    max_alerts_per_second=100,
    max_metrics_in_memory=100000,
    max_alerts_in_memory=10000
)

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "metrics_retention": timedelta(hours=1),
        "alerts_retention": timedelta(hours=24),
        "cleanup_interval": timedelta(minutes=5),
        "cleanup_batch_size": 100,
        "max_metrics_in_memory": 1000,
        "max_alerts_in_memory": 100,
        "notify_on_warning": True
    },
    "testing": {
        "metrics_retention": timedelta(minutes=30),
        "alerts_retention": timedelta(hours=1),
        "cleanup_interval": timedelta(minutes=1),
        "cleanup_batch_size": 10,
        "max_metrics_in_memory": 100,
        "max_alerts_in_memory": 10,
        "notify_on_warning": True
    },
    "production": {
        "metrics_retention": timedelta(days=7),
        "alerts_retention": timedelta(days=30),
        "cleanup_interval": timedelta(hours=1),
        "cleanup_batch_size": 1000,
        "max_metrics_in_memory": 100000,
        "max_alerts_in_memory": 10000,
        "notify_on_warning": False
    }
} 