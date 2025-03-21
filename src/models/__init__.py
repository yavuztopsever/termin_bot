"""Data models for the application."""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

@dataclass
class Subscription:
    """Subscription model."""
    user_id: str
    service_id: str
    location_id: str
    date_from: date
    date_to: date
    time_from: str
    time_to: str
    status: str
    created_at: datetime
    updated_at: datetime
    id: Optional[str] = None

@dataclass
class User:
    """User model."""
    telegram_id: str
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    language_code: str
    created_at: datetime
    updated_at: datetime
    subscriptions: List[Subscription] = field(default_factory=list)
    id: Optional[str] = None

@dataclass
class Appointment:
    """Appointment model."""
    service_id: str
    location_id: str
    date: datetime
    time: str
    status: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class Notification:
    """Notification model."""
    user_id: str
    type: str
    message: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class HealthMetrics:
    """System health metrics."""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    request_rate: float
    error_rate: float
    active_tasks: int
    db_connection_healthy: bool
    redis_connection_healthy: bool
    request_success_rate: float
    average_response_time: float
    rate_limit_status: Dict[str, Any]
    errors_last_hour: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "request_rate": self.request_rate,
            "error_rate": self.error_rate,
            "active_tasks": self.active_tasks,
            "db_connection_healthy": self.db_connection_healthy,
            "redis_connection_healthy": self.redis_connection_healthy,
            "request_success_rate": self.request_success_rate,
            "average_response_time": self.average_response_time,
            "rate_limit_status": self.rate_limit_status,
            "errors_last_hour": self.errors_last_hour
        }

    def is_healthy(self) -> bool:
        """Check if metrics indicate healthy system."""
        from src.config.config import (
            CPU_THRESHOLD,
            MEMORY_THRESHOLD,
            REQUEST_SUCCESS_RATE_THRESHOLD,
            RESPONSE_TIME_THRESHOLD,
            ERROR_RATE_THRESHOLD,
            ERROR_THRESHOLD
        )
        
        return (
            self.cpu_usage < CPU_THRESHOLD and
            self.memory_usage < MEMORY_THRESHOLD and
            self.request_success_rate >= REQUEST_SUCCESS_RATE_THRESHOLD and
            self.average_response_time < RESPONSE_TIME_THRESHOLD and
            self.error_rate < ERROR_RATE_THRESHOLD and
            self.errors_last_hour < ERROR_THRESHOLD and
            self.db_connection_healthy and
            self.redis_connection_healthy
        )

@dataclass
class ApiRequest:
    """API request history model."""
    endpoint: str
    method: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status_code: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    response_time: Optional[float] = None  # in seconds
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

@dataclass
class CaptchaVerification:
    """Captcha verification model."""
    site_key: str
    token: str
    valid_until: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

@dataclass
class WebsiteConfig:
    """Website configuration model."""
    service_id: str
    location_id: str
    base_url: str
    check_availability_endpoint: str
    book_appointment_endpoint: str
    captcha_endpoint: Optional[str] = None
    captcha_puzzle_endpoint: Optional[str] = None
    captcha_site_key: Optional[str] = None
    captcha_enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    request_timeout: int = 30
    rate_limit: int = 10
    rate_limit_period: int = 60
    retry_count: int = 3
    retry_delay: int = 60
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None
