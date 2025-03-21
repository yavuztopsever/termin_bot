from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import json
from dataclasses import dataclass
import asyncio

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

@dataclass
class Notification:
    """Represents a notification."""
    id: str
    channel: str
    recipient: str
    subject: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.utcnow()
    sent_at: Optional[datetime] = None
    status: str = "pending"

class NotificationManager:
    """Manager for sending notifications through various channels."""
    
    def __init__(self):
        """Initialize the notification manager."""
        self._initialized = False
        self._notifications: Dict[str, Notification] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize the notification manager."""
        try:
            # Create HTTP session
            self._session = aiohttp.ClientSession()
            
            # Start notification worker
            self._worker_task = asyncio.create_task(self._process_notifications())
            
            self._initialized = True
            logger.info("Notification manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize notification manager", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="notification_manager",
                message=f"Failed to initialize notification manager: {str(e)}"
            )
            raise
            
    async def _process_notifications(self) -> None:
        """Background task to process notifications."""
        while self._initialized:
            try:
                # Get notification from queue
                notification = await self._queue.get()
                
                try:
                    # Send notification
                    await self._send_notification(notification)
                    
                    # Update status
                    notification.status = "sent"
                    notification.sent_at = datetime.utcnow()
                    
                    # Record metrics
                    metrics_manager.record_notification("sent", None)
                    
                except Exception as e:
                    logger.error(f"Failed to send notification {notification.id}", error=str(e))
                    notification.status = "failed"
                    metrics_manager.record_notification("failed", None)
                    
                finally:
                    self._queue.task_done()
                    
            except Exception as e:
                logger.error("Error processing notifications", error=str(e))
                await asyncio.sleep(1)  # Wait before retrying
                
    async def _send_notification(self, notification: Notification) -> None:
        """Send a notification through the specified channel."""
        if not self._session:
            raise RuntimeError("Notification manager not initialized")
            
        try:
            if notification.channel == "email":
                await self._send_email(notification)
            elif notification.channel == "slack":
                await self._send_slack(notification)
            elif notification.channel == "webhook":
                await self._send_webhook(notification)
            else:
                raise ValueError(f"Unsupported notification channel: {notification.channel}")
                
        except Exception as e:
            logger.error(f"Failed to send notification through {notification.channel}", error=str(e))
            raise
            
    async def _send_email(self, notification: Notification) -> None:
        """Send an email notification."""
        # TODO: Implement email sending
        # For now, we'll just log it
        logger.info(f"Sending email to {notification.recipient}: {notification.subject}")
        
    async def _send_slack(self, notification: Notification) -> None:
        """Send a Slack notification."""
        if not config.notifications.slack_webhook_url:
            raise ValueError("Slack webhook URL not configured")
            
        payload = {
            "text": f"*{notification.subject}*\n{notification.message}",
            "attachments": [
                {
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (notification.metadata or {}).items()
                    ]
                }
            ]
        }
        
        async with self._session.post(
            config.notifications.slack_webhook_url,
            json=payload,
            timeout=10
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to send Slack notification: {await response.text()}")
                
    async def _send_webhook(self, notification: Notification) -> None:
        """Send a webhook notification."""
        if not config.notifications.webhook_url:
            raise ValueError("Webhook URL not configured")
            
        payload = {
            "id": notification.id,
            "channel": notification.channel,
            "recipient": notification.recipient,
            "subject": notification.subject,
            "message": notification.message,
            "metadata": notification.metadata,
            "created_at": notification.created_at.isoformat()
        }
        
        async with self._session.post(
            config.notifications.webhook_url,
            json=payload,
            timeout=10
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to send webhook notification: {await response.text()}")
                
    async def send_notification(
        self,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Queue a notification for sending."""
        try:
            # Create notification
            notification = Notification(
                id=f"notif_{datetime.utcnow().timestamp()}",
                channel=channel,
                recipient=recipient,
                subject=subject,
                message=message,
                metadata=metadata
            )
            
            # Store notification
            self._notifications[notification.id] = notification
            
            # Queue notification
            await self._queue.put(notification)
            
            # Record metrics
            metrics_manager.record_notification("queued", None)
            
            return notification.id
            
        except Exception as e:
            logger.error("Failed to queue notification", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="notification_manager",
                message=f"Failed to queue notification: {str(e)}"
            )
            raise
            
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get a notification by ID."""
        return self._notifications.get(notification_id)
        
    def get_notifications(
        self,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        recipient: Optional[str] = None
    ) -> List[Notification]:
        """Get notifications with optional filters."""
        notifications = self._notifications.values()
        
        if channel:
            notifications = [n for n in notifications if n.channel == channel]
            
        if status:
            notifications = [n for n in notifications if n.status == status]
            
        if recipient:
            notifications = [n for n in notifications if n.recipient == recipient]
            
        return list(notifications)
        
    async def shutdown(self) -> None:
        """Shutdown the notification manager."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
                
        if self._session:
            await self._session.close()
            
        self._initialized = False
        logger.info("Notification manager shut down")
        
    @property
    def initialized(self) -> bool:
        """Check if the notification manager is initialized."""
        return self._initialized

# Create singleton instance
notification_manager = NotificationManager() 