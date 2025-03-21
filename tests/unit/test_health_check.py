"""Test health check functionality."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time
import asyncio

from src.monitoring.health_check import HealthMetrics, HealthMonitor, start_health_monitoring, health_monitor
from src.config.config import HEALTH_CHECK_CONFIG

class TestHealthMetrics:
    """Test health metrics data class."""

    def test_health_metrics_creation(self):
        """Test health metrics creation."""
        now = datetime.utcnow()
        metrics = HealthMetrics(
            timestamp=now,
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=70.0,
            request_rate=5.0,
            error_rate=0.1,
            active_tasks=5,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.98,
            average_response_time=0.5,
            rate_limit_status={"test": 0.5},
            errors_last_hour=10
        )

        assert metrics.cpu_usage == 50.0
        assert metrics.memory_usage == 60.0
        assert metrics.disk_usage == 70.0
        assert metrics.request_rate == 5.0
        assert metrics.error_rate == 0.1
        assert metrics.active_tasks == 5
        assert metrics.db_connection_healthy
        assert metrics.redis_connection_healthy
        assert metrics.request_success_rate == 0.98
        assert metrics.average_response_time == 0.5
        assert metrics.rate_limit_status["test"] == 0.5
        assert metrics.errors_last_hour == 10

    def test_metrics_to_dict(self):
        """Test metrics conversion to dictionary."""
        now = datetime.utcnow()
        metrics = HealthMetrics(
            timestamp=now,
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=70.0,
            request_rate=5.0,
            error_rate=0.1,
            active_tasks=5,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.98,
            average_response_time=0.5,
            rate_limit_status={"test": 0.5},
            errors_last_hour=10
        )

        metrics_dict = metrics.to_dict()
        assert metrics_dict["cpu_usage"] == 50.0
        assert metrics_dict["memory_usage"] == 60.0
        assert metrics_dict["disk_usage"] == 70.0
        assert metrics_dict["request_rate"] == 5.0
        assert metrics_dict["error_rate"] == 0.1
        assert metrics_dict["active_tasks"] == 5
        assert metrics_dict["db_connection_healthy"]
        assert metrics_dict["redis_connection_healthy"]
        assert metrics_dict["request_success_rate"] == 0.98
        assert metrics_dict["average_response_time"] == 0.5
        assert metrics_dict["rate_limit_status"]["test"] == 0.5
        assert metrics_dict["errors_last_hour"] == 10

    def test_metrics_is_healthy(self):
        """Test health status determination."""
        now = datetime.utcnow()
        healthy_metrics = HealthMetrics(
            timestamp=now,
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=70.0,
            request_rate=5.0,
            error_rate=0.1,
            active_tasks=5,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.98,
            average_response_time=0.5,
            rate_limit_status={"test": 0.5},
            errors_last_hour=10
        )
        assert healthy_metrics.is_healthy()

        unhealthy_metrics = HealthMetrics(
            timestamp=now,
            cpu_usage=95.0,  # High CPU usage
            memory_usage=95.0,  # High memory usage
            disk_usage=95.0,  # High disk usage
            request_rate=250.0,  # High request rate
            error_rate=15.0,  # High error rate
            active_tasks=5,
            db_connection_healthy=False,  # Database connection issue
            redis_connection_healthy=False,  # Redis connection issue
            request_success_rate=0.80,  # Low success rate
            average_response_time=3.0,  # High response time
            rate_limit_status={"test": 0.5},
            errors_last_hour=200  # Many errors
        )
        assert not unhealthy_metrics.is_healthy()

class TestHealthMonitor:
    """Test health monitor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.monitor = HealthMonitor()

    @pytest.mark.asyncio
    async def test_collect_metrics(self, mock_memory, mock_cpu):
        """Test metrics collection."""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=60.0)

        # Add some test data
        self.monitor.request_times = [0.5, 0.3, 0.7]
        self.monitor.request_success = [True, True, False]
        self.monitor.active_tasks = 5
        self.monitor.errors = [
            datetime.utcnow() - timedelta(minutes=30)
            for _ in range(10)
        ]

        # Collect metrics
        metrics = await self.monitor._collect_metrics()

        # Verify metrics
        assert metrics.cpu_usage == 50.0
        assert metrics.memory_usage == 60.0
        assert metrics.request_rate == 3.0
        assert metrics.error_rate == 0.33
        assert metrics.active_tasks == 5
        assert metrics.errors_last_hour == 10

    @pytest.mark.asyncio
    async def test_metrics_history(self):
        """Test metrics history management."""
        # Add test metrics
        now = datetime.utcnow()
        old_metrics = HealthMetrics(
            timestamp=now - timedelta(days=2),
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=70.0,
            request_rate=5.0,
            error_rate=0.1,
            active_tasks=5,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.98,
            average_response_time=0.5,
            rate_limit_status={"test": {"blocked": False, "usage": 0.5}},
            errors_last_hour=10
        )
        await self.monitor._store_metrics(old_metrics)

        # Old metrics should be pruned
        await self.monitor._prune_old_metrics()
        assert len(self.monitor.metrics_history) == 0

    @pytest.mark.asyncio
    async def test_monitor_lifecycle(self):
        """Test monitor start/stop lifecycle."""
        # Start monitoring
        await self.monitor.start()
        assert self.monitor._running

        # Stop monitoring
        await self.monitor.stop()
        assert not self.monitor._running

    @pytest.mark.asyncio
    async def test_threshold_warnings(self, mock_logger):
        """Test threshold warning generation."""
        metrics = HealthMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=85.0,
            memory_usage=90.0,
            disk_usage=70.0,
            request_rate=5.0,
            error_rate=0.1,
            active_tasks=10,
            db_connection_healthy=True,
            redis_connection_healthy=True,
            request_success_rate=0.90,
            average_response_time=6.0,
            rate_limit_status={"test": {"blocked": False, "usage": 0.8}},
            errors_last_hour=60
        )

        warnings = self.monitor._check_thresholds(metrics)
        assert len(warnings) > 0
        assert any("CPU usage" in w for w in warnings)
        assert any("memory usage" in w for w in warnings)
        assert any("response time" in w for w in warnings)
        assert any("rate limit usage" in w for w in warnings)

class TestGlobalHealthMonitor:
    """Test global health monitor instance."""

    @pytest.mark.asyncio
    async def test_global_monitor(self):
        """Test global monitor start/stop."""
        from src.monitoring.health_check import start_health_monitoring, stop_health_monitoring, health_monitor

        await start_health_monitoring()
        assert health_monitor._running

        await stop_health_monitoring()
        assert not health_monitor._running

if __name__ == "__main__":
    pytest.main() 