"""Configuration settings for the application."""

import os
from dotenv import load_dotenv
from typing import Dict, Any, List
import asyncio

# Load environment variables from .env file
load_dotenv()

# Environment
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test_key")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# API rate limits configuration
API_RATE_LIMITS = {
    'default': {
        'rate': 10.0,  # requests per second
        'burst': 20    # maximum burst size
    },
    'endpoints': {
        '/api/v1/check': {
            'rate': 5.0,
            'burst': 10
        },
        '/api/v1/book': {
            'rate': 2.0,
            'burst': 5
        }
    }
}

# Anti-bot configuration
ANTI_BOT_CONFIG = {
    "enabled": bool(os.getenv("ANTI_BOT_ENABLED", "true")),
    "max_requests_per_ip": int(os.getenv("MAX_REQUESTS_PER_IP", "100")),
    "max_requests_per_second": float(os.getenv("MAX_REQUESTS_PER_SECOND", "10.0")),
    "window_size": int(os.getenv("WINDOW_SIZE", "3600")),  # seconds
    "block_duration": int(os.getenv("BLOCK_DURATION", "86400")),  # seconds
    "whitelist": os.getenv("IP_WHITELIST", "").split(","),
    "blacklist": os.getenv("IP_BLACKLIST", "").split(","),
    "patterns": {
        "suspicious_ua": [
            "bot",
            "crawler",
            "spider",
            "curl"
        ]
    }
}

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///app.db"
)

# Database Pool Configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "1"))  # seconds

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = os.getenv(
    "REDIS_URL",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "test_token")
BOT_USERNAME = os.getenv("BOT_USERNAME", "termin_bot")
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL", "")
BOT_WEBHOOK_PATH = os.getenv("BOT_WEBHOOK_PATH", "/webhook")

# Appointment Manager Configuration
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "3"))
MAX_PARALLEL_BOOKINGS = int(os.getenv("MAX_PARALLEL_BOOKINGS", "5"))  # maximum number of parallel booking attempts
BOOKING_TIMEOUT = int(os.getenv("BOOKING_TIMEOUT", "30"))  # seconds to wait for booking attempts

# Health check thresholds
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "80.0"))
MEMORY_THRESHOLD = float(os.getenv("MEMORY_THRESHOLD", "80.0"))
REQUEST_SUCCESS_RATE_THRESHOLD = float(os.getenv("REQUEST_SUCCESS_RATE_THRESHOLD", "0.95"))
RESPONSE_TIME_THRESHOLD = float(os.getenv("RESPONSE_TIME_THRESHOLD", "2.0"))
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", "0.05"))
ERROR_THRESHOLD = int(os.getenv("ERROR_THRESHOLD", "100"))
SUCCESS_RATE_THRESHOLD = float(os.getenv("SUCCESS_RATE_THRESHOLD", "0.95"))

# Health Check Configuration
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # seconds
HEALTH_CHECK_HISTORY_SIZE = int(os.getenv("HEALTH_CHECK_HISTORY_SIZE", "100"))
HEALTH_CHECK_CONFIG = {
    "interval": HEALTH_CHECK_INTERVAL,
    "history_size": HEALTH_CHECK_HISTORY_SIZE,
    "thresholds": {
        "critical": {
            "cpu_usage": 90.0,
            "memory_usage": 85.0,
            "disk_usage": 80.0,
            "request_rate": 1000.0,
            "error_rate": 0.1,
            "active_tasks": 50,
            "response_time": 2.0,
            "rate_limit_usage": 0.9,
            "errors_last_hour": 100
        },
        "warning": {
            "cpu_usage": 70.0,
            "memory_usage": 65.0,
            "disk_usage": 60.0,
            "request_rate": 800.0,
            "error_rate": 0.05,
            "active_tasks": 30,
            "response_time": 1.0,
            "rate_limit_usage": 0.7,
            "errors_last_hour": 50
        }
    }
}

# Metrics Configuration
METRICS_CONFIG = {
    "enabled": bool(os.getenv("METRICS_ENABLED", "true")),
    "port": int(os.getenv("METRICS_PORT", "9090")),
    "path": os.getenv("METRICS_PATH", "/metrics"),
    "prefix": os.getenv("METRICS_PREFIX", "mta_"),
    "labels": {
        "environment": ENV,
        "service": "termin_bot"
    }
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
LOG_FILE = os.getenv("LOG_FILE", "termin_bot.log")

# Notification Configuration
NOTIFICATION_CONFIG = {
    "enabled": bool(os.getenv("NOTIFICATION_ENABLED", "true")),
    "max_retries": int(os.getenv("NOTIFICATION_MAX_RETRIES", "3")),
    "retry_delay": int(os.getenv("NOTIFICATION_RETRY_DELAY", "60")),  # seconds
    "batch_size": int(os.getenv("NOTIFICATION_BATCH_SIZE", "100")),
    "cooldown": int(os.getenv("NOTIFICATION_COOLDOWN", "300")),  # seconds
    "daily_digest_time": os.getenv("NOTIFICATION_DAILY_DIGEST_TIME", "08:00"),  # time to send daily digest (HH:MM)
    "reminder_days": [1, 3, 7],  # days before appointment to send reminders
    "formats": {
        "date_format": os.getenv("NOTIFICATION_DATE_FORMAT", "%Y-%m-%d"),
        "time_format": os.getenv("NOTIFICATION_TIME_FORMAT", "%H:%M"),
        "datetime_format": os.getenv("NOTIFICATION_DATETIME_FORMAT", "%Y-%m-%d %H:%M")
    },
    "priorities": {
        "appointment_found": "normal",
        "appointment_booked": "high",
        "booking_failed": "normal",
        "booking_reminder": "high",
        "daily_digest": "normal"
    }
}

# Cache Configuration
CACHE_CONFIG = {
    "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "3600")),  # seconds
    "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
    "enabled": bool(os.getenv("CACHE_ENABLED", "true"))
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Load website configuration from database
async def load_website_config() -> Dict[str, Any]:
    """Load website configuration from database."""
    try:
        from src.database.db import db
        config = await db.get_website_config()
        if not config:
            raise ValueError("Website configuration not found in database")
        return config
    except Exception as e:
        raise ValueError(f"Failed to load website configuration: {str(e)}")

# Load website configuration
try:
    # Since we're in a synchronous context, we need to handle the async call properly
    WEBSITE_CONFIG = asyncio.get_event_loop().run_until_complete(load_website_config())
except Exception as e:
    WEBSITE_CONFIG = {}

# Redis Configuration
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", "10"))

# Target Website Configuration
TARGET_URL = os.getenv(
    "TARGET_URL",
    "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
)
BASE_URL = os.getenv("WEBSITE_BASE_URL", "https://www48.muenchen.de")
WEBSITE_TIMEOUT = int(os.getenv("WEBSITE_TIMEOUT", "30"))

# Captcha Configuration
CAPTCHA_ENABLED = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"
CAPTCHA_SOLUTION_TIMEOUT = int(os.getenv("CAPTCHA_SOLUTION_TIMEOUT", "30"))
CAPTCHA_2CAPTCHA_API_KEY = os.getenv("CAPTCHA_2CAPTCHA_API_KEY", "")
CAPTCHA_SOLVER = os.getenv("CAPTCHA_SOLVER", "2captcha")  # Options: 2captcha, dummy
CAPTCHA_CONFIG = {
    "enabled": CAPTCHA_ENABLED,
    "solution_timeout": CAPTCHA_SOLUTION_TIMEOUT,
    "solver": CAPTCHA_SOLVER,
    "2captcha_api_key": CAPTCHA_2CAPTCHA_API_KEY,
    "endpoints": {
        "puzzle": "/buergeransicht/api/backend/captcha-puzzle",
        "verify": "/buergeransicht/api/backend/captcha-verify"
    }
}

# Monitoring Configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "True").lower() == "true"
MONITORING_PORT = int(os.getenv("MONITORING_PORT", "8000"))
MONITORING_HOST = os.getenv("MONITORING_HOST", "0.0.0.0")

# Task Queue Configuration
CELERY_WORKERS = int(os.getenv("CELERY_WORKERS", "2"))
TASK_SOFT_TIME_LIMIT = int(os.getenv("TASK_SOFT_TIME_LIMIT", "240"))  # seconds
TASK_TIME_LIMIT = int(os.getenv("TASK_TIME_LIMIT", "300"))  # seconds

# System Configuration
DOCKER_MODE = os.getenv("DOCKER_MODE", "False").lower() == "true"
SYSTEM_CONFIG = {
    "timezone": os.getenv("TIMEZONE", "UTC"),
    "language": os.getenv("LANGUAGE", "en"),
    "debug": bool(os.getenv("DEBUG", "false")),
    "testing": bool(os.getenv("TESTING", "false")),
    "environment": ENV
}

# Chrome/Selenium Configuration
CHROME_OPTIONS = {
    "headless": True,
    "no_sandbox": True,
    "disable_dev_shm_usage": True,
    "disable_gpu": True,
    "window_size": "1920,1080"
}

# User Credentials (from environment variables)
USER_CREDENTIALS = {
    "name": os.getenv("USER_NAME", "Yavuz Topsever"),
    "email": os.getenv("USER_EMAIL", "yavuz.topsever@windowslive.com"),
    "person_count": int(os.getenv("PERSON_COUNT", "1"))
}

# Notification Configuration
NOTIFICATION_SETTINGS = {
    "enabled": os.getenv("NOTIFICATIONS_ENABLED", "True").lower() == "true",
    "retry_delay": int(os.getenv("NOTIFICATION_RETRY_DELAY", "60")),  # seconds
    "max_retries": int(os.getenv("NOTIFICATION_MAX_RETRIES", "3"))
}

# Application Settings
LOG_FILE = os.getenv("LOG_FILE", "logs/mta.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Redis Configuration (for Celery)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Health check configuration
HEALTH_CHECK_CONFIG = {
    "warning_cpu_threshold": 80.0,
    "critical_cpu_threshold": 90.0,
    "warning_memory_threshold": 80.0,
    "critical_memory_threshold": 90.0,
    "warning_disk_threshold": 80.0,
    "critical_disk_threshold": 90.0,
    "warning_request_rate": 100.0,  # requests per second
    "critical_request_rate": 200.0,  # requests per second
    "warning_error_rate": 5.0,  # errors per second
    "critical_error_rate": 10.0,  # errors per second
    "min_success_rate": 0.95,  # 95% success rate required
    "max_response_time": 2.0,  # maximum 2 seconds average response time
    "max_errors_per_hour": 100,  # maximum 100 errors per hour
    "metrics_retention_days": 7,  # keep metrics for 7 days
    "check_interval": 60  # check every 60 seconds
}

# Configuration validation
def validate_config() -> bool:
    """Validate the application configuration."""
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DATABASE_URL",
        "REDIS_URI",
        "WEBSITE_BASE_URL"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    return True
