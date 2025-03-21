"""Notification service module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database import get_database
from src.models import Notification, User
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        """Initialize the notification service."""
        self.logger = logger
        
    async def create_notification(self, user_id: int, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new notification."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                # Check if user exists
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                if not user:
                    self.logger.error(f"User {user_id} not found")
                    return None
                    
                # Create notification
                notification = Notification(
                    user_id=user_id,
                    message=notification_data.get("message"),
                    notification_type=notification_data.get("notification_type", "telegram"),
                    status="pending",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(notification)
                await session.commit()
                
                return {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "status": notification.status,
                    "created_at": notification.created_at.isoformat(),
                    "updated_at": notification.updated_at.isoformat()
                }
                
        except IntegrityError as e:
            self.logger.error(f"Failed to create notification: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating notification: {e}")
            return None
            
    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get a notification by ID."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                notification = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = notification.scalar_one_or_none()
                
                if not notification:
                    return None
                    
                return {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "status": notification.status,
                    "created_at": notification.created_at.isoformat(),
                    "updated_at": notification.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting notification: {e}")
            return None
            
    async def get_user_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all notifications for a user."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                notifications = await session.execute(
                    select(Notification).where(Notification.user_id == user_id)
                )
                notifications = notifications.scalars().all()
                
                return [{
                    "id": notif.id,
                    "user_id": notif.user_id,
                    "message": notif.message,
                    "notification_type": notif.notification_type,
                    "status": notif.status,
                    "created_at": notif.created_at.isoformat(),
                    "updated_at": notif.updated_at.isoformat()
                } for notif in notifications]
                
        except Exception as e:
            self.logger.error(f"Error getting user notifications: {e}")
            return []
            
    async def update_notification(self, notification_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a notification."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                notification = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = notification.scalar_one_or_none()
                
                if not notification:
                    return None
                    
                for key, value in update_data.items():
                    if hasattr(notification, key):
                        setattr(notification, key, value)
                notification.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "status": notification.status,
                    "created_at": notification.created_at.isoformat(),
                    "updated_at": notification.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error updating notification: {e}")
            return None
            
    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                notification = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = notification.scalar_one_or_none()
                
                if not notification:
                    return False
                    
                await session.delete(notification)
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting notification: {e}")
            return False 