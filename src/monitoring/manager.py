from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import json
import time

from src.config.config import config
from src.utils.logger import setup_logger
from src.notifications.manager import notification_manager

logger = setup_logger(__name__)

@dataclass
class Metric:
    """Represents a metric measurement."""
    name: str
    value: float
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    """Represents an alert."""
    level: str
    component: str
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class MonitoringManager:
    """Manager for collecting metrics and handling alerts."""
    
    def __init__(self):
        """Initialize the monitoring manager."""
        self._initialized = False
        self._metrics: List[Metric] = []
        self._alerts: List[Alert] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize the monitoring manager."""
        try:
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_old_data())
            
            self._initialized = True
            logger.info("Monitoring manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize monitoring manager", error=str(e))
            await self.create_alert(
                level="critical",
                component="monitoring_manager",
                message=f"Failed to initialize monitoring manager: {str(e)}"
            )
            raise
            
    async def _cleanup_old_data(self) -> None:
        """Background task to clean up old metrics and alerts."""
        while self._initialized:
            try:
                now = datetime.utcnow()
                
                # Clean up old metrics
                self._metrics = [
                    m for m in self._metrics
                    if now - m.timestamp < config.monitoring.metrics_retention
                ]
                
                # Clean up old alerts
                self._alerts = [
                    a for a in self._alerts
                    if now - a.timestamp < config.monitoring.alerts_retention
                ]
                
                await asyncio.sleep(config.monitoring.cleanup_interval.total_seconds())
                
            except Exception as e:
                logger.error("Error cleaning up old monitoring data", error=str(e))
                await asyncio.sleep(1)  # Wait before retrying
                
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric measurement.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            tags: Optional tags for the metric
            metadata: Optional metadata for the metric
        """
        try:
            if not self._initialized:
                raise RuntimeError("Monitoring manager not initialized")
                
            # Create metric
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags,
                metadata=metadata
            )
            
            # Add to metrics list
            self._metrics.append(metric)
            
            # Check thresholds
            await self._check_thresholds(metric)
            
        except Exception as e:
            logger.error("Failed to record metric", error=str(e))
            
    async def create_alert(
        self,
        level: str,
        component: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create an alert.
        
        Args:
            level: Alert level (info, warning, error, critical)
            component: Component that generated the alert
            message: Alert message
            metadata: Optional metadata for the alert
        """
        try:
            if not self._initialized:
                raise RuntimeError("Monitoring manager not initialized")
                
            # Create alert
            alert = Alert(
                level=level,
                component=component,
                message=message,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
            # Add to alerts list
            self._alerts.append(alert)
            
            # Send notification for critical alerts
            if level == "critical":
                await notification_manager.send_notification(
                    channel="slack",
                    recipient=config.notifications.slack_channel,
                    subject=f"Critical Alert: {component}",
                    message=message,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error("Failed to create alert", error=str(e))
            
    async def _check_thresholds(self, metric: Metric) -> None:
        """Check if metric exceeds thresholds and create alerts if needed."""
        try:
            # Get thresholds for metric
            thresholds = config.monitoring.metric_thresholds.get(metric.name, {})
            
            # Check each threshold
            for level, threshold in thresholds.items():
                if metric.value > threshold:
                    await self.create_alert(
                        level=level,
                        component="monitoring_manager",
                        message=f"Metric {metric.name} exceeded threshold of {threshold}",
                        metadata={
                            "metric": metric.name,
                            "value": metric.value,
                            "threshold": threshold,
                            "tags": metric.tags
                        }
                    )
                    
        except Exception as e:
            logger.error("Failed to check metric thresholds", error=str(e))
            
    def get_metrics(
        self,
        name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        """Get metrics matching the given criteria.
        
        Args:
            name: Optional metric name to filter by
            tags: Optional tags to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            List of matching metrics
        """
        try:
            if not self._initialized:
                raise RuntimeError("Monitoring manager not initialized")
                
            # Filter metrics
            metrics = self._metrics
            
            if name:
                metrics = [m for m in metrics if m.name == name]
                
            if tags:
                metrics = [
                    m for m in metrics
                    if all(m.tags and m.tags.get(k) == v for k, v in tags.items())
                ]
                
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
                
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]
                
            return metrics
            
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            return []
            
    def get_alerts(
        self,
        level: Optional[str] = None,
        component: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Alert]:
        """Get alerts matching the given criteria.
        
        Args:
            level: Optional alert level to filter by
            component: Optional component to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            List of matching alerts
        """
        try:
            if not self._initialized:
                raise RuntimeError("Monitoring manager not initialized")
                
            # Filter alerts
            alerts = self._alerts
            
            if level:
                alerts = [a for a in alerts if a.level == level]
                
            if component:
                alerts = [a for a in alerts if a.component == component]
                
            if start_time:
                alerts = [a for a in alerts if a.timestamp >= start_time]
                
            if end_time:
                alerts = [a for a in alerts if a.timestamp <= end_time]
                
            return alerts
            
        except Exception as e:
            logger.error("Failed to get alerts", error=str(e))
            return []
            
    async def shutdown(self) -> None:
        """Shutdown the monitoring manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        self._initialized = False
        logger.info("Monitoring manager shut down")
        
    @property
    def initialized(self) -> bool:
        """Check if the monitoring manager is initialized."""
        return self._initialized

# Create singleton instance
monitoring_manager = MonitoringManager() 