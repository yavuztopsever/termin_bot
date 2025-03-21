"""Repository implementations for database models."""

from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import and_, or_, not_
from sqlalchemy.future import select

from src.database.db import Base, User, Subscription, Appointment, Notification, WebsiteConfig
from src.database.repository import Repository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class UserRepository(Repository[User]):
    """Repository for User model."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(User)
        
    async def find_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """
        Find user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User or None if not found
        """
        return await self.find_one(User.telegram_id == telegram_id)
        
    async def get_users_with_active_subscriptions(self) -> List[User]:
        """
        Get users with active subscriptions.
        
        Returns:
            List of users
        """
        from src.database.db_pool import db_pool
        async with db_pool.session() as session:
            query = select(User).join(Subscription).where(Subscription.status == 'active').distinct()
            result = await session.execute(query)
            return list(result.scalars().all())

class SubscriptionRepository(Repository[Subscription]):
    """Repository for Subscription model."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(Subscription)
        
    async def find_by_user_id(self, user_id: int) -> List[Subscription]:
        """
        Find subscriptions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of subscriptions
        """
        return await self.find_all(Subscription.user_id == user_id)
        
    async def find_active_by_user_id(self, user_id: int) -> List[Subscription]:
        """
        Find active subscriptions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active subscriptions
        """
        return await self.find_all(
            Subscription.user_id == user_id,
            Subscription.status == 'active'
        )
        
    async def find_active_subscriptions(self) -> List[Subscription]:
        """
        Find all active subscriptions.
        
        Returns:
            List of active subscriptions
        """
        return await self.find_all(Subscription.status == 'active')
        
    async def deactivate_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """
        Deactivate a subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Updated subscription or None if not found
        """
        return await self.update(subscription_id, {'status': 'inactive'})
        
    async def activate_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """
        Activate a subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Updated subscription or None if not found
        """
        return await self.update(subscription_id, {'status': 'active'})

class AppointmentRepository(Repository[Appointment]):
    """Repository for Appointment model."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(Appointment)
        
    async def find_by_user_id(self, user_id: int) -> List[Appointment]:
        """
        Find appointments by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of appointments
        """
        return await self.find_all(Appointment.user_id == user_id)
        
    async def find_by_service_and_location(
        self,
        service_id: str,
        location_id: Optional[str] = None
    ) -> List[Appointment]:
        """
        Find appointments by service and location.
        
        Args:
            service_id: Service ID
            location_id: Optional location ID
            
        Returns:
            List of appointments
        """
        filters = [Appointment.service_id == service_id]
        if location_id:
            filters.append(Appointment.location_id == location_id)
            
        return await self.find_all(*filters)
        
    async def find_available_appointments(self) -> List[Appointment]:
        """
        Find available appointments.
        
        Returns:
            List of available appointments
        """
        return await self.find_all(Appointment.status == 'available')
        
    async def mark_as_booked(self, appointment_id: int, user_id: int) -> Optional[Appointment]:
        """
        Mark appointment as booked.
        
        Args:
            appointment_id: Appointment ID
            user_id: User ID
            
        Returns:
            Updated appointment or None if not found
        """
        return await self.update(
            appointment_id,
            {'status': 'booked', 'user_id': user_id}
        )

class NotificationRepository(Repository[Notification]):
    """Repository for Notification model."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(Notification)
        
    async def find_by_user_id(self, user_id: int) -> List[Notification]:
        """
        Find notifications by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of notifications
        """
        return await self.find_all(Notification.user_id == user_id)
        
    async def find_pending_notifications(self) -> List[Notification]:
        """
        Find pending notifications.
        
        Returns:
            List of pending notifications
        """
        return await self.find_all(Notification.status == 'pending')
        
    async def mark_as_sent(self, notification_id: int) -> Optional[Notification]:
        """
        Mark notification as sent.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Updated notification or None if not found
        """
        from datetime import datetime
        return await self.update(
            notification_id,
            {'status': 'sent', 'sent_at': datetime.utcnow()}
        )
        
    async def mark_as_failed(self, notification_id: int, error_message: str) -> Optional[Notification]:
        """
        Mark notification as failed.
        
        Args:
            notification_id: Notification ID
            error_message: Error message
            
        Returns:
            Updated notification or None if not found
        """
        return await self.update(
            notification_id,
            {'status': 'failed', 'error_message': error_message}
        )

class WebsiteConfigRepository(Repository[WebsiteConfig]):
    """Repository for WebsiteConfig model."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(WebsiteConfig)
        
    async def get_latest_config(self) -> Optional[WebsiteConfig]:
        """
        Get latest website configuration.
        
        Returns:
            Latest website configuration or None if not found
        """
        from src.database.db_pool import db_pool
        async with db_pool.session() as session:
            query = select(WebsiteConfig).order_by(WebsiteConfig.updated_at.desc())
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
    async def update_config(self, config_data: Dict[str, Any]) -> WebsiteConfig:
        """
        Update website configuration.
        
        Args:
            config_data: Configuration data
            
        Returns:
            Updated configuration
        """
        # Get latest config
        latest_config = await self.get_latest_config()
        
        if latest_config:
            # Update existing config
            return await self.update(latest_config.id, config_data)
        else:
            # Create new config
            return await self.create(config_data)

# Create repository instances
user_repository = UserRepository()
subscription_repository = SubscriptionRepository()
appointment_repository = AppointmentRepository()
notification_repository = NotificationRepository()
website_config_repository = WebsiteConfigRepository()
