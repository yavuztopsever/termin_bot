"""Configuration settings for the application."""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseSettings, validator

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Termin Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DB_PATH: str = "data/app.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    METRICS_HOST: str = "0.0.0.0"
    
    # Health Monitoring
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_ALERT_THRESHOLD: float = 0.9
    HEALTH_MAX_HISTORY: int = 1000
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
        
    @validator("HEALTH_CHECK_INTERVAL")
    def validate_health_check_interval(cls, v: int) -> int:
        """Validate health check interval."""
        if v < 1:
            raise ValueError("Health check interval must be positive")
        return v
        
    @validator("HEALTH_ALERT_THRESHOLD")
    def validate_health_alert_threshold(cls, v: float) -> float:
        """Validate health alert threshold."""
        if not 0 <= v <= 1:
            raise ValueError("Health alert threshold must be between 0 and 1")
        return v
        
    @validator("HEALTH_MAX_HISTORY")
    def validate_health_max_history(cls, v: int) -> int:
        """Validate health max history."""
        if v < 1:
            raise ValueError("Health max history must be positive")
        return v
        
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings
