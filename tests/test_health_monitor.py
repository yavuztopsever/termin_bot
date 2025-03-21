"""Tests for health monitoring system."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import psutil
from src.monitoring.health_monitor import HealthMonitor
from src.database.database import AsyncDatabase
import asyncio

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
def health_monitor(mock_db, mock_redis, mock_metrics):
    """Create a HealthMonitor instance with mocked dependencies."""
    return HealthMonitor(
        db=mock_db,
        redis=mock_redis,
        metrics=mock_metrics
    )

@pytest.fixture
def sample_metrics():
    """Sample metrics data."""
    return {
        "cpu_usage": 45.2,
        "memory_usage": 62.8,
        "disk_usage": 78.5,
        "request_success_rate": 0.98,
        "request_latency_avg": 0.245,
        "errors_last_hour": 12,
        "active_tasks": 5,
        "queue_size": 8,
        "queue_latency_avg": 1.5,
        "rate_limit_remaining": 95,
        "timestamp": datetime.utcnow().isoformat()
    }

def test_get_current_metrics(health_monitor, mock_metrics, sample_metrics):
    """Test getting current system metrics."""
    # Mock psutil functions
    with patch("psutil.cpu_percent") as mock_cpu, \
         patch("psutil.virtual_memory") as mock_memory, \
         patch("psutil.disk_usage") as mock_disk:
        
        mock_cpu.return_value = 45.2
        mock_memory.return_value = MagicMock(percent=62.8)
        mock_disk.return_value = MagicMock(percent=78.5)
        
        # Mock Redis metrics
        health_monitor.redis.info.return_value = {
            "connected_clients": 5,
            "used_memory_peak_human": "1.2M"
        }
        
        # Get metrics
        metrics = health_monitor.get_current_metrics()
        
        # Verify system metrics
        assert metrics["cpu_usage"] == 45.2
        assert metrics["memory_usage"] == 62.8
        assert metrics["disk_usage"] == 78.5
        assert "timestamp" in metrics
        
        # Verify Redis metrics
        assert metrics["redis_clients"] == 5
        assert metrics["redis_memory_peak"] == "1.2M"

def test_check_system_health(health_monitor, sample_metrics):
    """Test system health check."""
    # Test healthy system
    status = health_monitor.check_system_health(sample_metrics)
    assert status == "healthy"
    
    # Test degraded system (high CPU)
    high_cpu_metrics = {**sample_metrics, "cpu_usage": 92.0}
    status = health_monitor.check_system_health(high_cpu_metrics)
    assert status == "degraded"
    
    # Test degraded system (high error rate)
    high_error_metrics = {**sample_metrics, "errors_last_hour": 100}
    status = health_monitor.check_system_health(high_error_metrics)
    assert status == "degraded"
    
    # Test degraded system (low success rate)
    low_success_metrics = {**sample_metrics, "request_success_rate": 0.85}
    status = health_monitor.check_system_health(low_success_metrics)
    assert status == "degraded"

def test_get_metrics_history(health_monitor, mock_redis, sample_metrics):
    """Test retrieving metrics history."""
    # Mock Redis to return historical metrics
    history = [
        {**sample_metrics, "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat()}
        for i in range(5)
    ]
    mock_redis.lrange.return_value = [str(metric) for metric in history]
    
    # Get metrics history
    result = health_monitor.get_metrics_history()
    
    # Verify history was retrieved
    assert len(result) == 5
    assert all("timestamp" in entry for entry in result)
    assert all("cpu_usage" in entry for entry in result)

def test_store_metrics(health_monitor, mock_redis, sample_metrics):
    """Test storing metrics in Redis."""
    # Store metrics
    health_monitor.store_metrics(sample_metrics)
    
    # Verify metrics were stored
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()

def test_check_component_health(health_monitor):
    """Test checking individual component health."""
    # Test database health
    with patch.object(health_monitor.db, "command") as mock_command:
        mock_command.return_value = {"ok": 1.0}
        assert health_monitor.check_database_health() is True
        
        mock_command.side_effect = Exception("Connection error")
        assert health_monitor.check_database_health() is False
    
    # Test Redis health
    with patch.object(health_monitor.redis, "ping") as mock_ping:
        mock_ping.return_value = True
        assert health_monitor.check_redis_health() is True
        
        mock_ping.side_effect = Exception("Connection error")
        assert health_monitor.check_redis_health() is False

def test_get_detailed_status(health_monitor, mock_db, sample_metrics):
    """Test getting detailed system status."""
    # Mock database counts
    mock_db.users.count_documents.side_effect = [
        10,  # Total users
        5    # Active subscriptions
    ]
    mock_db.appointments.count_documents.return_value = 3  # Appointments today
    
    # Mock current metrics
    with patch.object(health_monitor, "get_current_metrics") as mock_get_metrics:
        mock_get_metrics.return_value = sample_metrics
        
        # Get detailed status
        status = health_monitor.get_detailed_status()
        
        # Verify status content
        assert "metrics" in status
        assert "statistics" in status
        assert status["statistics"]["users"] == 10
        assert status["statistics"]["active_subscriptions"] == 5
        assert status["statistics"]["appointments_booked_today"] == 3

def test_error_handling(health_monitor, mock_metrics):
    """Test error handling in health monitor."""
    # Test error in getting metrics
    with patch("psutil.cpu_percent") as mock_cpu:
        mock_cpu.side_effect = Exception("psutil error")
        
        metrics = health_monitor.get_current_metrics()
        
        # Verify error was recorded
        mock_metrics.increment.assert_called_with(
            "errors_total",
            tags={"type": "monitoring_error"}
        )
        
        # Verify fallback values
        assert metrics["cpu_usage"] == -1

def test_threshold_checks(health_monitor, sample_metrics):
    """Test various threshold checks."""
    # Test CPU threshold
    assert health_monitor._is_cpu_critical(95.0) is True
    assert health_monitor._is_cpu_critical(45.2) is False
    
    # Test memory threshold
    assert health_monitor._is_memory_critical(92.0) is True
    assert health_monitor._is_memory_critical(62.8) is False
    
    # Test error rate threshold
    assert health_monitor._is_error_rate_critical(100) is True
    assert health_monitor._is_error_rate_critical(12) is False

@pytest.mark.asyncio
async def test_check_database_health_success(health_monitor, mock_db):
    """Test successful database health check."""
    mock_db.ping.return_value = True
    is_healthy = await health_monitor._check_database_health()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_check_database_health_failure(health_monitor, mock_db):
    """Test failed database health check."""
    mock_db.ping.side_effect = Exception("Connection failed")
    is_healthy = await health_monitor._check_database_health()
    assert is_healthy is False

@pytest.mark.asyncio
async def test_check_redis_health_success(health_monitor):
    """Test successful Redis health check."""
    with patch('src.monitoring.health_monitor.redis_client') as mock_redis:
        mock_redis.ping.return_value = True
        is_healthy = await health_monitor._check_redis_health()
        assert is_healthy is True

@pytest.mark.asyncio
async def test_check_redis_health_failure(health_monitor):
    """Test failed Redis health check."""
    with patch('src.monitoring.health_monitor.redis_client') as mock_redis:
        mock_redis.ping.side_effect = Exception("Connection failed")
        is_healthy = await health_monitor._check_redis_health()
        assert is_healthy is False

@pytest.mark.asyncio
async def test_check_system_health_all_healthy(health_monitor):
    """Test system health check when all components are healthy."""
    metrics = HealthMetrics(
        timestamp=datetime.utcnow(),
        cpu_usage=50.0,
        memory_usage=40.0,
        disk_usage=30.0,
        request_rate=10.0,
        error_rate=0.01,
        active_tasks=5,
        db_connection_healthy=True,
        redis_connection_healthy=True,
        request_success_rate=0.99,
        average_response_time=0.1,
        rate_limit_status={"test": {"blocked": False, "usage": 0.1}},
        errors_last_hour=1
    )
    warnings = health_monitor._check_thresholds(metrics)
    assert len(warnings) == 0

@pytest.mark.asyncio
async def test_check_system_health_partial_failure(health_monitor):
    """Test system health check with some component failures."""
    metrics = HealthMetrics(
        timestamp=datetime.utcnow(),
        cpu_usage=95.0,
        memory_usage=90.0,
        disk_usage=85.0,
        request_rate=1000.0,
        error_rate=0.2,
        active_tasks=100,
        db_connection_healthy=False,
        redis_connection_healthy=False,
        request_success_rate=0.7,
        average_response_time=5.0,
        rate_limit_status={"test": {"blocked": True, "usage": 1.0}},
        errors_last_hour=1000
    )
    warnings = health_monitor._check_thresholds(metrics)
    assert len(warnings) > 3  # Multiple warnings expected

@pytest.mark.asyncio
async def test_monitor_system_health(health_monitor):
    """Test continuous system health monitoring."""
    await health_monitor.start()
    await asyncio.sleep(0.1)  # Let the monitor run briefly
    await health_monitor.stop()
    history = await health_monitor.get_metrics_history()
    assert len(history) > 0 