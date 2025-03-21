"""Configuration module for the application."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings."""
    TELEGRAM_BOT_TOKEN: str
    MONGODB_URI: str
    REDIS_URI: str
    MOCK_API_HOST: Optional[str] = None
    MOCK_API_PORT: Optional[int] = None

from .config import *  # Import all configuration variables
