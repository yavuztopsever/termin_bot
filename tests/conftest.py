"""Test fixtures and configuration."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import os

from src.api.app import app
from src.models import HealthMetrics
from src.database.database import AsyncDatabase
from src.monitoring.health_check import HealthMonitor
from src.bot.telegram_bot import TelegramBot
from src.database.db import AsyncDatabase, Base

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create a test database."""
    # Use an in-memory SQLite database for testing
    test_db = AsyncDatabase(test_mode=True)
    await test_db.connect()  # This will create all tables
    yield test_db
    await test_db.close()

@pytest.fixture
async def mock_db():
    """Create a mock database."""
    db = AsyncMock(spec=AsyncDatabase)
    db.users = AsyncMock()
    db.subscriptions = AsyncMock()
    db.appointments = AsyncMock()
    db.website_config = AsyncMock()
    return db

@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis

@pytest.fixture
async def mock_metrics():
    """Create a mock metrics collector."""
    metrics = MagicMock()
    metrics.increment = MagicMock()
    metrics.timing = MagicMock()
    metrics.gauge = MagicMock()
    return metrics

@pytest.fixture
async def mock_health_monitor():
    """Create a mock health monitor."""
    monitor = AsyncMock(spec=HealthMonitor)
    monitor.get_current_metrics = AsyncMock()
    monitor.get_metrics_history = AsyncMock()
    monitor.get_detailed_status = AsyncMock()
    return monitor

@pytest.fixture
async def mock_celery():
    """Create a mock Celery instance."""
    celery = MagicMock()
    celery.send_task = MagicMock()
    return celery

@pytest.fixture
async def mock_api_server():
    """Create a mock API server."""
    server = MagicMock()
    server.get = AsyncMock(return_value=MagicMock(status_code=200))
    server.post = AsyncMock(return_value=MagicMock(status_code=200))
    return server

@pytest.fixture
async def test_client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def sample_metrics_data():
    """Create sample metrics data."""
    return {
        "critical": HealthMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=95.0,
            memory_usage=90.0,
            disk_usage=85.0,
            request_rate=10.0,
            error_rate=0.02,
            active_tasks=20,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.98,
            average_response_time=0.5,
            rate_limit_status={"test": {"blocked": False, "usage": 0.5}},
            errors_last_hour=10
        ),
        "warning": HealthMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=75.0,
            memory_usage=70.0,
            disk_usage=65.0,
            request_rate=8.0,
            error_rate=0.05,
            active_tasks=15,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.95,
            average_response_time=1.0,
            rate_limit_status={"test": {"blocked": False, "usage": 0.7}},
            errors_last_hour=30
        ),
        "healthy": HealthMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=50.0,
            memory_usage=40.0,
            disk_usage=45.0,
            request_rate=5.0,
            error_rate=0.01,
            active_tasks=10,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.99,
            average_response_time=0.3,
            rate_limit_status={"test": {"blocked": False, "usage": 0.3}},
            errors_last_hour=5
        )
    }

@pytest.fixture
def sample_user():
    """Create a sample user."""
    return {
        "user_id": "123456789",
        "chat_id": "987654321",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
        "created_at": datetime.utcnow() - timedelta(days=1),
        "last_active": datetime.utcnow()
    }

@pytest.fixture
def sample_subscription():
    """Create a sample subscription."""
    return {
        "user_id": "123456789",
        "chat_id": "987654321",
        "preferences": {
            "locations": ["Test Location"],
            "appointment_types": ["Regular"],
            "time_ranges": [{"start": "09:00", "end": "17:00"}],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        },
        "active": True,
        "last_check": datetime.utcnow() - timedelta(minutes=30),
        "created_at": datetime.utcnow() - timedelta(days=1)
    }

@pytest.fixture
def sample_appointment():
    """Create a sample appointment."""
    return {
        "user_id": "123456789",
        "service_id": "service123",
        "location_id": "location456",
        "date": datetime.utcnow().date().isoformat(),
        "time": "14:30",
        "status": "booked",
        "booking_id": "booking789",
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def sample_notification():
    """Create a sample notification."""
    return {
        "user_id": "123456789",
        "chat_id": "987654321",
        "type": "appointment_available",
        "content": {
            "service_id": "service123",
            "location_id": "location456",
            "date": datetime.utcnow().date().isoformat(),
            "time": "14:30"
        },
        "status": "pending",
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def sample_slot():
    """Create a sample slot."""
    return {
        "date": datetime.utcnow().date().isoformat(),
        "time": "14:30",
        "location": "Test Location",
        "type": "Regular",
        "available": True
    }

@pytest.fixture
def bot(mock_db, mock_redis, mock_metrics):
    """Create a bot instance."""
    return TelegramBot(
        token="test_token",
        db=mock_db,
        redis=mock_redis,
        metrics=mock_metrics
    ) 