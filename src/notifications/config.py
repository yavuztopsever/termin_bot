from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class NotificationConfig:
    """Configuration for notification system."""
    
    # Email settings
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_timeout: int = 30
    email_from: str
    email_reply_to: Optional[str] = None
    
    # Slack settings
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_username: str = "Termin Bot"
    slack_icon_emoji: str = ":calendar:"
    
    # Webhook settings
    webhook_url: Optional[str] = None
    webhook_timeout: int = 10
    webhook_retries: int = 3
    webhook_retry_delay: int = 5
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Retry settings
    max_retries: int = 3
    retry_delay: int = 5
    retry_backoff_factor: float = 2.0
    
    # Queue settings
    queue_size: int = 1000
    worker_count: int = 5
    
    # Timeout settings
    send_timeout: int = 30
    connect_timeout: int = 10
    
    # Cleanup settings
    cleanup_interval: timedelta = timedelta(hours=24)
    retention_days: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_username": self.smtp_username,
            "smtp_password": "********",  # Mask sensitive data
            "smtp_use_tls": self.smtp_use_tls,
            "smtp_timeout": self.smtp_timeout,
            "email_from": self.email_from,
            "email_reply_to": self.email_reply_to,
            "slack_webhook_url": self.slack_webhook_url,
            "slack_channel": self.slack_channel,
            "slack_username": self.slack_username,
            "slack_icon_emoji": self.slack_icon_emoji,
            "webhook_url": self.webhook_url,
            "webhook_timeout": self.webhook_timeout,
            "webhook_retries": self.webhook_retries,
            "webhook_retry_delay": self.webhook_retry_delay,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff_factor": self.retry_backoff_factor,
            "queue_size": self.queue_size,
            "worker_count": self.worker_count,
            "send_timeout": self.send_timeout,
            "connect_timeout": self.connect_timeout,
            "cleanup_interval": str(self.cleanup_interval),
            "retention_days": self.retention_days
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationConfig':
        """Create configuration from dictionary."""
        # Convert string duration to timedelta
        if "cleanup_interval" in data and isinstance(data["cleanup_interval"], str):
            data["cleanup_interval"] = timedelta.fromisoformat(data["cleanup_interval"])
            
        return cls(**data)
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in data.items():
            if hasattr(self, key):
                if key == "cleanup_interval" and isinstance(value, str):
                    value = timedelta.fromisoformat(value)
                setattr(self, key, value)

# Default configuration
DEFAULT_CONFIG = NotificationConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="",
    smtp_password="",
    smtp_use_tls=True,
    smtp_timeout=30,
    email_from="noreply@terminbot.com",
    email_reply_to="support@terminbot.com",
    slack_webhook_url=None,
    slack_channel="#termin-bot",
    slack_username="Termin Bot",
    slack_icon_emoji=":calendar:",
    webhook_url=None,
    webhook_timeout=10,
    webhook_retries=3,
    webhook_retry_delay=5,
    rate_limit_per_minute=60,
    rate_limit_per_hour=1000,
    max_retries=3,
    retry_delay=5,
    retry_backoff_factor=2.0,
    queue_size=1000,
    worker_count=5,
    send_timeout=30,
    connect_timeout=10,
    cleanup_interval=timedelta(hours=24),
    retention_days=30
)

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_username": "",
        "smtp_password": "",
        "smtp_use_tls": False,
        "rate_limit_per_minute": 1000,
        "rate_limit_per_hour": 10000,
        "queue_size": 100,
        "worker_count": 2,
        "retention_days": 7
    },
    "testing": {
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_username": "",
        "smtp_password": "",
        "smtp_use_tls": False,
        "rate_limit_per_minute": 1000,
        "rate_limit_per_hour": 10000,
        "queue_size": 100,
        "worker_count": 2,
        "retention_days": 1
    },
    "production": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "rate_limit_per_minute": 60,
        "rate_limit_per_hour": 1000,
        "queue_size": 1000,
        "worker_count": 5,
        "retention_days": 30
    }
} 