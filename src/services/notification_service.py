"""Notification service for managing notification operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.db import Notification, db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class NotificationService:
    """Service for managing notification operations."""
    
    @staticmethod
    async def create_notification(notification_data: Dict[str, Any]) -> Notification:
        """Create a new notification."""
        try:
            async with db.async_session() as session:
                notification = Notification(**notification_data)
                session.add(notification)
                await session.commit()
                logger.info(f"Created new notification for user: {notification.user_id}")
                return notification
        except IntegrityError:
            logger.error(f"Failed to create notification: User {notification_data.get('user_id')} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            raise
            
    @staticmethod
    async def get_notification(notification_id: int) -> Optional[Notification]:
        """Get a notification by ID."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = result.scalar_one_or_none()
                if notification:
                    logger.info(f"Retrieved notification: {notification_id}")
                else:
                    logger.info(f"Notification not found: {notification_id}")
                return notification
        except Exception as e:
            logger.error(f"Failed to get notification: {e}")
            raise
            
    @staticmethod
    async def get_user_notifications(user_id: int) -> List[Notification]:
        """Get all notifications for a user."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Notification).where(Notification.user_id == user_id)
                )
                notifications = result.scalars().all()
                logger.info(f"Retrieved {len(notifications)} notifications for user: {user_id}")
                return notifications
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            raise
            
    @staticmethod
    async def get_pending_notifications() -> List[Notification]:
        """Get all pending notifications."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Notification).where(Notification.status == 'pending')
                )
                notifications = result.scalars().all()
                logger.info(f"Retrieved {len(notifications)} pending notifications")
                return notifications
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {e}")
            raise
            
    @staticmethod
    async def mark_notification_sent(notification_id: int, error_message: Optional[str] = None) -> bool:
        """Mark a notification as sent."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = result.scalar_one_or_none()
                if not notification:
                    logger.info(f"Notification not found: {notification_id}")
                    return False
                    
                notification.status = 'sent' if not error_message else 'error'
                notification.sent_at = datetime.utcnow()
                if error_message:
                    notification.error_message = error_message
                
                await session.commit()
                logger.info(f"Marked notification {notification_id} as {'sent' if not error_message else 'error'}")
                return True
        except Exception as e:
            logger.error(f"Failed to mark notification as sent: {e}")
            raise
            
    @staticmethod
    async def delete_notification(notification_id: int) -> bool:
        """Delete a notification."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = result.scalar_one_or_none()
                if not notification:
                    logger.info(f"Notification not found for deletion: {notification_id}")
                    return False
                    
                await session.delete(notification)
                await session.commit()
                logger.info(f"Deleted notification: {notification_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            raise 