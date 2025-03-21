import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str
    timeout: float
    rate_limit: int
    rate_limit_period: float
    retries: int
    retry_delay: float
    
@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int
    pool_timeout: float
    query_timeout: float
    
@dataclass
class CacheConfig:
    """Cache configuration settings."""
    host: str
    port: int
    database: int
    ttl: int
    max_size: int
    cleanup_interval: float
    
@dataclass
class MonitoringConfig:
    """Monitoring configuration settings."""
    prometheus_port: int
    prometheus_path: str
    health_check_interval: float
    health_check_timeout: float
    metrics_retention_days: int
    alert_cooldown: float
    dashboard_port: int
    dashboard_refresh_interval: float
    
@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str
    format: str
    file: Optional[str]
    max_size: int
    backup_count: int
    
@dataclass
class Config:
    """Main configuration class."""
    api: APIConfig
    database: DatabaseConfig
    cache: CacheConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            api=APIConfig(
                base_url=os.getenv('API_BASE_URL', 'https://api.example.com'),
                timeout=float(os.getenv('API_TIMEOUT', '30.0')),
                rate_limit=int(os.getenv('API_RATE_LIMIT', '100')),
                rate_limit_period=float(os.getenv('API_RATE_LIMIT_PERIOD', '60.0')),
                retries=int(os.getenv('API_RETRIES', '3')),
                retry_delay=float(os.getenv('API_RETRY_DELAY', '1.0'))
            ),
            database=DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                database=os.getenv('DB_NAME', 'app_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
                pool_timeout=float(os.getenv('DB_POOL_TIMEOUT', '30.0')),
                query_timeout=float(os.getenv('DB_QUERY_TIMEOUT', '10.0'))
            ),
            cache=CacheConfig(
                host=os.getenv('CACHE_HOST', 'localhost'),
                port=int(os.getenv('CACHE_PORT', '6379')),
                database=int(os.getenv('CACHE_DB', '0')),
                ttl=int(os.getenv('CACHE_TTL', '3600')),
                max_size=int(os.getenv('CACHE_MAX_SIZE', '1000')),
                cleanup_interval=float(os.getenv('CACHE_CLEANUP_INTERVAL', '300.0'))
            ),
            monitoring=MonitoringConfig(
                prometheus_port=int(os.getenv('PROMETHEUS_PORT', '9090')),
                prometheus_path=os.getenv('PROMETHEUS_PATH', '/metrics'),
                health_check_interval=float(os.getenv('HEALTH_CHECK_INTERVAL', '60.0')),
                health_check_timeout=float(os.getenv('HEALTH_CHECK_TIMEOUT', '5.0')),
                metrics_retention_days=int(os.getenv('METRICS_RETENTION_DAYS', '7')),
                alert_cooldown=float(os.getenv('ALERT_COOLDOWN', '300.0')),
                dashboard_port=int(os.getenv('DASHBOARD_PORT', '8080')),
                dashboard_refresh_interval=float(os.getenv('DASHBOARD_REFRESH_INTERVAL', '5.0'))
            ),
            logging=LoggingConfig(
                level=os.getenv('LOG_LEVEL', 'INFO'),
                format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                file=os.getenv('LOG_FILE'),
                max_size=int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
                backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
            )
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'api': {
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'rate_limit': self.api.rate_limit,
                'rate_limit_period': self.api.rate_limit_period,
                'retries': self.api.retries,
                'retry_delay': self.api.retry_delay
            },
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'user': self.database.user,
                'password': self.database.password,
                'pool_size': self.database.pool_size,
                'pool_timeout': self.database.pool_timeout,
                'query_timeout': self.database.query_timeout
            },
            'cache': {
                'host': self.cache.host,
                'port': self.cache.port,
                'database': self.cache.database,
                'ttl': self.cache.ttl,
                'max_size': self.cache.max_size,
                'cleanup_interval': self.cache.cleanup_interval
            },
            'monitoring': {
                'prometheus_port': self.monitoring.prometheus_port,
                'prometheus_path': self.monitoring.prometheus_path,
                'health_check_interval': self.monitoring.health_check_interval,
                'health_check_timeout': self.monitoring.health_check_timeout,
                'metrics_retention_days': self.monitoring.metrics_retention_days,
                'alert_cooldown': self.monitoring.alert_cooldown,
                'dashboard_port': self.monitoring.dashboard_port,
                'dashboard_refresh_interval': self.monitoring.dashboard_refresh_interval
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file': self.logging.file,
                'max_size': self.logging.max_size,
                'backup_count': self.logging.backup_count
            }
        }

# Create configuration instance
config = Config.from_env()

# Export configuration as dictionaries for backward compatibility
API_CONFIG = config.api.__dict__
DATABASE_CONFIG = config.database.__dict__
CACHE_CONFIG = config.cache.__dict__
MONITORING_CONFIG = config.monitoring.__dict__
LOGGING_CONFIG = config.logging.__dict__

# Base configuration
BASE_CONFIG = {
    "app_name": "Termin Bot",
    "app_version": "1.0.0",
    "app_description": "A bot for managing appointments",
    "app_author": "Your Name",
    "app_license": "MIT",
    
    # Environment
    "environment": os.getenv("ENVIRONMENT", "development"),
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    
    # Logging
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "logs/app.log",
    
    # Database
    "database": {
        "url": os.getenv("DATABASE_URL", "sqlite:///data/app.db"),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "echo": os.getenv("DB_ECHO", "False").lower() == "true"
    },
    
    # API
    "api": {
        "base_url": os.getenv("API_BASE_URL", "https://api.example.com"),
        "timeout": int(os.getenv("API_TIMEOUT", "30")),
        "retries": int(os.getenv("API_RETRIES", "3")),
        "rate_limit": int(os.getenv("API_RATE_LIMIT", "100")),
        "rate_limit_period": int(os.getenv("API_RATE_LIMIT_PERIOD", "60"))
    },
    
    # Cache
    "cache": {
        "type": os.getenv("CACHE_TYPE", "memory"),
        "url": os.getenv("CACHE_URL", "redis://localhost:6379/0"),
        "ttl": int(os.getenv("CACHE_TTL", "300")),
        "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "cleanup_interval": int(os.getenv("CACHE_CLEANUP_INTERVAL", "60"))
    },
    
    # Monitoring
    "monitoring": {
        "enabled": os.getenv("MONITORING_ENABLED", "True").lower() == "true",
        "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
        "metrics_retention_days": int(os.getenv("METRICS_RETENTION_DAYS", "7")),
        "dashboard_port": int(os.getenv("DASHBOARD_PORT", "8080")),
        "dashboard_refresh_interval": int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "5"))
    },
    
    # Alerting
    "alerts": {
        "enabled": os.getenv("ALERTS_ENABLED", "True").lower() == "true",
        "cooldown": int(os.getenv("ALERT_COOLDOWN", "300")),
        "channels": os.getenv("ALERT_CHANNELS", "slack,email,webhook").split(","),
        "slack": {
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
            "channel": os.getenv("SLACK_CHANNEL", "#alerts")
        },
        "email": {
            "enabled": os.getenv("EMAIL_ALERTS_ENABLED", "False").lower() == "true",
            "smtp_host": os.getenv("SMTP_HOST", ""),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("FROM_EMAIL", ""),
            "to_emails": os.getenv("TO_EMAILS", "").split(",")
        },
        "webhook": {
            "url": os.getenv("WEBHOOK_URL", ""),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    },
    
    # Security
    "security": {
        "secret_key": os.getenv("SECRET_KEY", "your-secret-key"),
        "token_expiry": int(os.getenv("TOKEN_EXPIRY", "3600")),
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "rate_limit": int(os.getenv("RATE_LIMIT", "100")),
        "rate_limit_period": int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    },
    
    # Paths
    "paths": {
        "data": Path("data"),
        "logs": Path("logs"),
        "templates": Path("templates"),
        "static": Path("static")
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "debug": True,
        "log_level": "DEBUG",
        "database": {
            "echo": True
        },
        "monitoring": {
            "metrics_retention_days": 1
        },
        "alerts": {
            "cooldown": 30
        }
    },
    "testing": {
        "debug": True,
        "log_level": "DEBUG",
        "database": {
            "url": "sqlite:///data/test.db",
            "echo": True
        },
        "monitoring": {
            "metrics_retention_days": 1
        },
        "alerts": {
            "cooldown": 30
        }
    },
    "production": {
        "debug": False,
        "log_level": "INFO",
        "database": {
            "echo": False
        },
        "monitoring": {
            "metrics_retention_days": 30
        },
        "alerts": {
            "cooldown": 300
        }
    }
}

def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    environment = BASE_CONFIG["environment"]
    config = BASE_CONFIG.copy()
    
    # Apply environment-specific configuration
    if environment in ENVIRONMENT_CONFIGS:
        env_config = ENVIRONMENT_CONFIGS[environment]
        _deep_update(config, env_config)
        
    return config

def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
    """Update a dictionary recursively."""
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value

# Create configuration instance
config = get_config()

# Export specific configurations
API_CONFIG = config["api"]
CACHE_CONFIG = config["cache"]
MONITORING_CONFIG = config["monitoring"]
ALERT_CONFIG = config["alerts"]
DASHBOARD_CONFIG = config["monitoring"]

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///app.db"
)

# API configuration
BASE_URL = os.getenv(
    "BASE_URL",
    "https://terminvereinbarung.muenchen.de"
)

API_RATE_LIMITS = {
    "check": 10,  # requests per minute
    "book": 5,    # requests per minute
    "general": 20 # general requests per minute
}

API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Captcha configuration
CAPTCHA_CONFIG = {
    "enabled": os.getenv("CAPTCHA_ENABLED", "true").lower() == "true",
    "site_key": os.getenv("CAPTCHA_SITE_KEY", ""),
    "endpoints": {
        "puzzle": "/api/v1/captcha/puzzle",
        "verify": "/api/v1/captcha/verify"
    }
}

# User credentials
USER_CREDENTIALS = {
    "username": os.getenv("API_USERNAME", ""),
    "password": os.getenv("API_PASSWORD", "")
}

# Monitoring configuration
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

# Health check configuration
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # seconds
HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))    # seconds

# Task queue configuration
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/0"
)

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
TELEGRAM_WEBHOOK_PORT = int(os.getenv("TELEGRAM_WEBHOOK_PORT", "8443"))

# Notification configuration
NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
NOTIFICATION_CHECK_INTERVAL = int(os.getenv("NOTIFICATION_CHECK_INTERVAL", "300"))  # seconds

# Cache configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # seconds
CACHE_REDIS_URL = os.getenv(
    "CACHE_REDIS_URL",
    "redis://localhost:6379/1"
)

# Security configuration
SECURITY_ENABLED = os.getenv("SECURITY_ENABLED", "true").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))  # seconds

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# Error handling configuration
ERROR_REPORTING_ENABLED = os.getenv("ERROR_REPORTING_ENABLED", "true").lower() == "true"
ERROR_REPORTING_EMAIL = os.getenv("ERROR_REPORTING_EMAIL", "")

# Development configuration
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Load additional configuration from environment
def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {
        "database": {
            "url": DATABASE_URL
        },
        "api": {
            "base_url": BASE_URL,
            "rate_limits": API_RATE_LIMITS,
            "timeout": API_TIMEOUT,
            "max_retries": MAX_RETRIES,
            "retry_delay": RETRY_DELAY
        },
        "captcha": CAPTCHA_CONFIG,
        "user_credentials": USER_CREDENTIALS,
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "logs/app.log"
        },
        "monitoring": {
            "prometheus_port": PROMETHEUS_PORT,
            "enable_metrics": ENABLE_METRICS
        },
        "health_check": {
            "interval": HEALTH_CHECK_INTERVAL,
            "timeout": HEALTH_CHECK_TIMEOUT
        },
        "task_queue": {
            "broker_url": CELERY_BROKER_URL,
            "result_backend": CELERY_RESULT_BACKEND
        },
        "telegram": {
            "bot_token": TELEGRAM_BOT_TOKEN,
            "webhook_url": TELEGRAM_WEBHOOK_URL,
            "webhook_port": TELEGRAM_WEBHOOK_PORT
        },
        "notification": {
            "enabled": NOTIFICATION_ENABLED,
            "check_interval": NOTIFICATION_CHECK_INTERVAL
        },
        "cache": {
            "enabled": CACHE_ENABLED,
            "ttl": CACHE_TTL,
            "redis_url": CACHE_REDIS_URL
        },
        "security": {
            "enabled": SECURITY_ENABLED,
            "jwt_secret": JWT_SECRET,
            "jwt_algorithm": JWT_ALGORITHM,
            "jwt_expiration": JWT_EXPIRATION
        },
        "rate_limit": {
            "enabled": RATE_LIMIT_ENABLED,
            "requests": RATE_LIMIT_REQUESTS,
            "period": RATE_LIMIT_PERIOD
        },
        "error_reporting": {
            "enabled": ERROR_REPORTING_ENABLED,
            "email": ERROR_REPORTING_EMAIL
        },
        "development": {
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "testing": TESTING
        }
    }
    
    return config 