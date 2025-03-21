from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timedelta
import json
import aiohttp
from dataclasses import dataclass

from src.config.config import ALERT_CONFIG
from src.utils.logger import setup_logger
from src.monitoring.exceptions import (
    AlertError,
    AlertInitializationError,
    AlertDeliveryError,
    AlertConfigurationError
)
from src.monitoring.metrics import metrics_manager

logger = setup_logger(__name__)

@dataclass
class Alert:
    """Represents a system alert."""
    id: str
    level: str
    component: str
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """Manager for system alerts and notifications."""
    
    def __init__(self):
        """Initialize the alert manager."""
        self._initialized = False
        self._alerts: Dict[str, Alert] = {}
        self._cooldowns: Dict[str, datetime] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize the alert manager."""
        try:
            # Create aiohttp session for sending alerts
            self._session = aiohttp.ClientSession()
            
            # Initialize alert handlers
            self._handlers = {
                "slack": self._send_slack_alert,
                "email": self._send_email_alert,
                "webhook": self._send_webhook_alert
            }
            
            self._initialized = True
            logger.info("Alert manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize alert manager", error=str(e))
            raise AlertInitializationError(f"Failed to initialize alert manager: {str(e)}")
            
    async def close(self) -> None:
        """Close the alert manager."""
        if self._session:
            await self._session.close()
        self._initialized = False
        
    def _generate_alert_id(self) -> str:
        """Generate a unique alert ID."""
        return f"alert_{datetime.utcnow().timestamp()}_{len(self._alerts)}"
        
    def _check_cooldown(self, alert_key: str) -> bool:
        """Check if an alert is in cooldown period."""
        if alert_key in self._cooldowns:
            cooldown_end = self._cooldowns[alert_key]
            if datetime.utcnow() < cooldown_end:
                return True
        return False
        
    def _set_cooldown(self, alert_key: str) -> None:
        """Set cooldown period for an alert."""
        self._cooldowns[alert_key] = datetime.utcnow() + timedelta(seconds=ALERT_CONFIG["cooldown"])
        
    async def create_alert(
        self,
        level: str,
        component: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create and send a new alert."""
        if not self._initialized:
            raise AlertError("Alert manager not initialized")
            
        # Generate alert key for cooldown check
        alert_key = f"{level}_{component}_{message}"
        
        # Check cooldown
        if self._check_cooldown(alert_key):
            logger.debug(f"Alert in cooldown: {alert_key}")
            return None
            
        try:
            # Create alert
            alert = Alert(
                id=self._generate_alert_id(),
                level=level,
                component=component,
                message=message,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
            # Store alert
            self._alerts[alert.id] = alert
            
            # Set cooldown
            self._set_cooldown(alert_key)
            
            # Send alert through configured channels
            await self._send_alert(alert)
            
            # Record alert metric
            metrics_manager.increment("alerts_total", level=level, component=component)
            
            return alert
            
        except Exception as e:
            logger.error("Failed to create alert", error=str(e))
            raise AlertError(f"Failed to create alert: {str(e)}")
            
    async def _send_alert(self, alert: Alert) -> None:
        """Send alert through configured channels."""
        for channel in ALERT_CONFIG["channels"]:
            if channel in self._handlers:
                try:
                    await self._handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send alert through {channel}", error=str(e))
                    metrics_manager.increment(
                        "alert_delivery_failures_total",
                        channel=channel,
                        level=alert.level
                    )
                    
    async def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert to Slack."""
        if not ALERT_CONFIG["slack"]["webhook_url"]:
            return
            
        try:
            payload = {
                "text": f"*{alert.level.upper()} Alert*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{alert.level.upper()} Alert",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Component:*\n{alert.component}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{alert.timestamp.isoformat()}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:*\n{alert.message}"
                        }
                    }
                ]
            }
            
            if alert.metadata:
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Metadata:*\n```{json.dumps(alert.metadata, indent=2)}```"
                    }
                })
                
            async with self._session.post(
                ALERT_CONFIG["slack"]["webhook_url"],
                json=payload
            ) as response:
                if response.status != 200:
                    raise AlertDeliveryError(f"Failed to send Slack alert: {response.status}")
                    
        except Exception as e:
            raise AlertDeliveryError(f"Failed to send Slack alert: {str(e)}")
            
    async def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        if not ALERT_CONFIG["email"]["enabled"]:
            return
            
        try:
            # TODO: Implement email sending
            # This would typically use an email service or SMTP
            pass
            
        except Exception as e:
            raise AlertDeliveryError(f"Failed to send email alert: {str(e)}")
            
    async def _send_webhook_alert(self, alert: Alert) -> None:
        """Send alert to configured webhook."""
        if not ALERT_CONFIG["webhook"]["url"]:
            return
            
        try:
            payload = {
                "id": alert.id,
                "level": alert.level,
                "component": alert.component,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            async with self._session.post(
                ALERT_CONFIG["webhook"]["url"],
                json=payload,
                headers=ALERT_CONFIG["webhook"]["headers"]
            ) as response:
                if response.status != 200:
                    raise AlertDeliveryError(f"Failed to send webhook alert: {response.status}")
                    
        except Exception as e:
            raise AlertDeliveryError(f"Failed to send webhook alert: {str(e)}")
            
    async def resolve_alert(self, alert_id: str) -> None:
        """Mark an alert as resolved."""
        if alert_id not in self._alerts:
            raise AlertError(f"Alert not found: {alert_id}")
            
        alert = self._alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        
        # Send resolution notification
        await self._send_alert(alert)
        
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self._alerts.get(alert_id)
        
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self._alerts.values() if not alert.resolved]
        
    def get_component_alerts(self, component: str) -> List[Alert]:
        """Get all alerts for a specific component."""
        return [
            alert for alert in self._alerts.values()
            if alert.component == component
        ]
        
    def get_level_alerts(self, level: str) -> List[Alert]:
        """Get all alerts of a specific level."""
        return [
            alert for alert in self._alerts.values()
            if alert.level == level
        ]

# Create singleton instance
alert_manager = AlertManager() 