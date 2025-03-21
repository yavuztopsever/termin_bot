"""Health check module for system monitoring."""

import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
import threading
import time
import redis
from sqlalchemy import text
import logging
import statistics

from src.utils.logger import setup_logger
from src.database import get_database, get_redis
from src.database.db import db
from src.monitoring.metrics import metrics_collector
from src.config.config import (
    HEALTH_CHECK_INTERVAL,
    CPU_THRESHOLD,
    MEMORY_THRESHOLD,
    REQUEST_SUCCESS_RATE_THRESHOLD,
    RESPONSE_TIME_THRESHOLD,
    ERROR_RATE_THRESHOLD,
    ERROR_THRESHOLD,
    SUCCESS_RATE_THRESHOLD,
    HEALTH_CHECK_CONFIG
)
from src.database.database import AsyncDatabase, get_db
from src.models import HealthMetrics

logger = logging.getLogger(__name__)

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
        return asdict(self)

    def is_healthy(self) -> bool:
        """Check if metrics indicate healthy system."""
        return (
            self.cpu_usage < HEALTH_CHECK_CONFIG["critical_cpu_threshold"] and
            self.memory_usage < HEALTH_CHECK_CONFIG["critical_memory_threshold"] and
            self.error_rate < HEALTH_CHECK_CONFIG["critical_error_rate"] and
            self.db_connection_healthy and
            self.redis_connection_healthy and
            self.request_success_rate >= HEALTH_CHECK_CONFIG["min_success_rate"] and
            self.average_response_time < HEALTH_CHECK_CONFIG["max_response_time"] and
            self.errors_last_hour < HEALTH_CHECK_CONFIG["max_errors_per_hour"]
        )

class HealthMonitor:
    """Monitor system health metrics."""

    def __init__(self, redis_client=None, metrics_manager=None):
        """Initialize health monitor."""
        self._running = False
        self.metrics_history = []
        self.max_history_size = 1000
        self.check_interval = 60  # seconds
        self.redis_client = redis_client
        self.metrics_manager = metrics_manager
        self._lock = asyncio.Lock()
        self.request_times = []
        self.request_success = []
        self.errors = []
        self.active_tasks = 0

    async def _store_metrics(self, metrics: HealthMetrics) -> None:
        """Store health metrics."""
        async with self._lock:
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

    async def _prune_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        now = datetime.utcnow()
        retention = timedelta(hours=24)
        async with self._lock:
            self.metrics_history = [
                m for m in self.metrics_history 
                if now - m.timestamp < retention
            ]

    async def start(self) -> None:
        """Start the health monitor."""
        if not self._running:
            self._running = True
            asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop the health monitor."""
        self._running = False

    async def get_current_metrics(self) -> HealthMetrics:
        """Get current health metrics."""
        metrics = await self._collect_metrics()
        await self._store_metrics(metrics)
        return metrics

    async def get_metrics_history(self) -> List[HealthMetrics]:
        """Get historical metrics."""
        async with self._lock:
            return list(self.metrics_history)

    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed system status."""
        metrics = await self.get_current_metrics()
        return {
            "status": "healthy" if metrics.is_healthy() else "degraded",
            "metrics": metrics.to_dict(),
            "warnings": self._check_thresholds(metrics)
        }

    async def _collect_metrics(self) -> HealthMetrics:
        """Collect current health metrics."""
        # Get system metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        # Calculate request metrics
        now = time.time()
        cutoff = now - 60  # Last minute
        recent_times = [t for t in self.request_times if t > cutoff]
        recent_success = [s for s, t in zip(self.request_success, self.request_times) if t > cutoff]
        
        request_rate = len(recent_times) / 60.0 if recent_times else 0
        success_rate = sum(recent_success) / len(recent_success) if recent_success else 1.0
        avg_response_time = statistics.mean(recent_times) if recent_times else 0.0

        # Check connections
        redis_healthy = False
        if self.redis_client is not None:
            try:
                await self.redis_client.ping()
                redis_healthy = True
            except Exception as e:
                logger.error(f"Redis connection check failed: {e}")

        # Create metrics
        metrics = HealthMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            request_rate=request_rate,
            error_rate=len(self.errors) / 60.0,  # errors per second
            active_tasks=self.active_tasks,
            redis_connection_healthy=redis_healthy,
            request_success_rate=success_rate,
            average_response_time=avg_response_time,
            rate_limit_status={},  # To be implemented
            errors_last_hour=len(self.errors)
        )

        return metrics

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                metrics = await self._collect_metrics()
                warnings = self._check_thresholds(metrics)
                
                async with self._lock:
                    await self._store_metrics(metrics)

                if warnings:
                    for warning in warnings:
                        logger.warning(warning)

                if self.metrics_manager:
                    self.metrics_manager.update_health_metrics(metrics)

                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay on error

    def _check_thresholds(self, metrics: HealthMetrics) -> List[str]:
        """Check metrics against thresholds and return warnings."""
        warnings = []

        # CPU usage checks
        if metrics.cpu_usage >= HEALTH_CHECK_CONFIG["critical_cpu_threshold"]:
            warnings.append(f"CRITICAL: CPU usage at {metrics.cpu_usage}%")
        elif metrics.cpu_usage >= HEALTH_CHECK_CONFIG["warning_cpu_threshold"]:
            warnings.append(f"WARNING: High CPU usage at {metrics.cpu_usage}%")

        # Memory usage checks
        if metrics.memory_usage >= HEALTH_CHECK_CONFIG["critical_memory_threshold"]:
            warnings.append(f"CRITICAL: Memory usage at {metrics.memory_usage}%")
        elif metrics.memory_usage >= HEALTH_CHECK_CONFIG["warning_memory_threshold"]:
            warnings.append(f"WARNING: High memory usage at {metrics.memory_usage}%")

        # Disk usage checks
        if metrics.disk_usage >= HEALTH_CHECK_CONFIG["critical_disk_threshold"]:
            warnings.append(f"CRITICAL: Disk usage at {metrics.disk_usage}%")
        elif metrics.disk_usage >= HEALTH_CHECK_CONFIG["warning_disk_threshold"]:
            warnings.append(f"WARNING: High disk usage at {metrics.disk_usage}%")

        # Request rate checks
        if metrics.request_rate >= HEALTH_CHECK_CONFIG["critical_request_rate"]:
            warnings.append(f"CRITICAL: High request rate at {metrics.request_rate} req/s")
        elif metrics.request_rate >= HEALTH_CHECK_CONFIG["warning_request_rate"]:
            warnings.append(f"WARNING: Elevated request rate at {metrics.request_rate} req/s")

        # Error rate checks
        if metrics.error_rate >= HEALTH_CHECK_CONFIG["critical_error_rate"]:
            warnings.append(f"CRITICAL: High error rate at {metrics.error_rate} errors/s")
        elif metrics.error_rate >= HEALTH_CHECK_CONFIG["warning_error_rate"]:
            warnings.append(f"WARNING: Elevated error rate at {metrics.error_rate} errors/s")

        # Success rate check
        if metrics.request_success_rate < HEALTH_CHECK_CONFIG["min_success_rate"]:
            warnings.append(f"WARNING: Low success rate at {metrics.request_success_rate*100}%")

        # Response time check
        if metrics.average_response_time > HEALTH_CHECK_CONFIG["max_response_time"]:
            warnings.append(f"WARNING: High average response time at {metrics.average_response_time}s")

        # Hourly error check
        if metrics.errors_last_hour >= HEALTH_CHECK_CONFIG["max_errors_per_hour"]:
            warnings.append(f"WARNING: High number of errors in last hour: {metrics.errors_last_hour}")

        # Connection checks
        if not metrics.redis_connection_healthy:
            warnings.append("CRITICAL: Redis connection is unhealthy")

        # Rate limit status checks
        for endpoint, status in metrics.rate_limit_status.items():
            if isinstance(status, dict):
                if status.get("blocked", False):
                    warnings.append(f"WARNING: Rate limit exceeded for {endpoint}")
                elif status.get("usage", 0) > HEALTH_CHECK_CONFIG["rate_limit_warning_threshold"]:
                    warnings.append(f"WARNING: High rate limit usage for {endpoint}")
            elif isinstance(status, (int, float)) and status > HEALTH_CHECK_CONFIG["rate_limit_warning_threshold"]:
                warnings.append(f"WARNING: High rate limit usage for {endpoint}")

        return warnings

# Create a global health monitor instance
health_monitor = HealthMonitor()

async def start_health_monitoring():
    """Start global health monitoring."""
    await health_monitor.start()

async def stop_health_monitoring():
    """Stop global health monitoring."""
    await health_monitor.stop() 