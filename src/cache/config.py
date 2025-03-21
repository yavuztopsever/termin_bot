from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class CacheConfig:
    """Configuration for caching system."""
    
    # Cache size settings
    max_size: int = 1000
    max_value_size: int = 1024 * 1024  # 1MB
    
    # TTL settings
    default_ttl: timedelta = timedelta(minutes=5)
    max_ttl: timedelta = timedelta(days=7)
    
    # Cleanup settings
    cleanup_interval: timedelta = timedelta(minutes=5)
    cleanup_batch_size: int = 100
    
    # Memory settings
    max_memory_percent: float = 80.0
    memory_check_interval: timedelta = timedelta(minutes=1)
    
    # Performance settings
    compression_enabled: bool = True
    compression_threshold: int = 1024  # 1KB
    compression_level: int = 6
    
    # Error handling
    max_retries: int = 3
    retry_delay: int = 1
    retry_backoff_factor: float = 2.0
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_interval: timedelta = timedelta(minutes=1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "max_size": self.max_size,
            "max_value_size": self.max_value_size,
            "default_ttl": str(self.default_ttl),
            "max_ttl": str(self.max_ttl),
            "cleanup_interval": str(self.cleanup_interval),
            "cleanup_batch_size": self.cleanup_batch_size,
            "max_memory_percent": self.max_memory_percent,
            "memory_check_interval": str(self.memory_check_interval),
            "compression_enabled": self.compression_enabled,
            "compression_threshold": self.compression_threshold,
            "compression_level": self.compression_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff_factor": self.retry_backoff_factor,
            "metrics_enabled": self.metrics_enabled,
            "metrics_interval": str(self.metrics_interval)
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheConfig':
        """Create configuration from dictionary."""
        # Convert string durations to timedelta
        duration_fields = [
            "default_ttl",
            "max_ttl",
            "cleanup_interval",
            "memory_check_interval",
            "metrics_interval"
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
                    "default_ttl",
                    "max_ttl",
                    "cleanup_interval",
                    "memory_check_interval",
                    "metrics_interval"
                ] and isinstance(value, str):
                    value = timedelta.fromisoformat(value)
                setattr(self, key, value)

# Default configuration
DEFAULT_CONFIG = CacheConfig(
    max_size=1000,
    max_value_size=1024 * 1024,  # 1MB
    default_ttl=timedelta(minutes=5),
    max_ttl=timedelta(days=7),
    cleanup_interval=timedelta(minutes=5),
    cleanup_batch_size=100,
    max_memory_percent=80.0,
    memory_check_interval=timedelta(minutes=1),
    compression_enabled=True,
    compression_threshold=1024,  # 1KB
    compression_level=6,
    max_retries=3,
    retry_delay=1,
    retry_backoff_factor=2.0,
    metrics_enabled=True,
    metrics_interval=timedelta(minutes=1)
)

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "max_size": 100,
        "max_value_size": 512 * 1024,  # 512KB
        "default_ttl": timedelta(minutes=1),
        "max_ttl": timedelta(hours=1),
        "cleanup_interval": timedelta(minutes=1),
        "cleanup_batch_size": 10,
        "max_memory_percent": 50.0,
        "memory_check_interval": timedelta(seconds=30),
        "compression_enabled": False,
        "metrics_interval": timedelta(seconds=30)
    },
    "testing": {
        "max_size": 50,
        "max_value_size": 256 * 1024,  # 256KB
        "default_ttl": timedelta(seconds=30),
        "max_ttl": timedelta(minutes=5),
        "cleanup_interval": timedelta(seconds=30),
        "cleanup_batch_size": 5,
        "max_memory_percent": 30.0,
        "memory_check_interval": timedelta(seconds=15),
        "compression_enabled": False,
        "metrics_interval": timedelta(seconds=15)
    },
    "production": {
        "max_size": 1000,
        "max_value_size": 1024 * 1024,  # 1MB
        "default_ttl": timedelta(minutes=5),
        "max_ttl": timedelta(days=7),
        "cleanup_interval": timedelta(minutes=5),
        "cleanup_batch_size": 100,
        "max_memory_percent": 80.0,
        "memory_check_interval": timedelta(minutes=1),
        "compression_enabled": True,
        "metrics_interval": timedelta(minutes=1)
    }
} 