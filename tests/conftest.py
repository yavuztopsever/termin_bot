"""Test configuration and fixtures."""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlite3 import connect
from src.data.database.database import Database
from src.data.redis.redis_client import RedisClient
from src.data.metrics.metrics_client import MetricsClient
from src.control.health.health_monitor import HealthMonitor
from src.config import settings

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def database() -> AsyncGenerator[Database, None]:
    """Create a test database instance."""
    # Use a test database file
    test_db_path = "data/test.db"
    
    # Create database instance
    db = Database(db_path=test_db_path)
    await db.start()
    
    yield db
    
    # Cleanup
    await db.stop()
    
    # Remove test database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.fixture(scope="session")
async def redis() -> AsyncGenerator[RedisClient, None]:
    """Create a test Redis client instance."""
    # Create Redis client instance
    redis_client = RedisClient(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )
    await redis_client.start()
    
    yield redis_client
    
    # Cleanup
    await redis_client.stop()

@pytest.fixture(scope="session")
async def metrics() -> AsyncGenerator[MetricsClient, None]:
    """Create a test metrics client instance."""
    # Create metrics client instance
    metrics_client = MetricsClient()
    await metrics_client.start()
    
    yield metrics_client
    
    # Cleanup
    await metrics_client.stop()

@pytest.fixture(scope="session")
async def health_monitor() -> AsyncGenerator[HealthMonitor, None]:
    """Create a test health monitor instance."""
    # Create health monitor instance
    monitor = HealthMonitor(
        check_interval=settings.HEALTH_CHECK_INTERVAL,
        alert_threshold=settings.HEALTH_ALERT_THRESHOLD,
        max_history=settings.HEALTH_MAX_HISTORY
    )
    await monitor.start()
    
    yield monitor
    
    # Cleanup
    await monitor.stop() 