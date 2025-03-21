"""Subscription service module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database import get_database
from src.models import Subscription, User
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SubscriptionService:
    """Service for managing subscriptions."""
    
    def __init__(self):
        """Initialize the subscription service."""
        self.logger = logger
        
    async def create_subscription(self, user_id: int, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new subscription."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                # Check if user exists
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                if not user:
                    self.logger.error(f"User {user_id} not found")
                    return None
                    
                # Create subscription
                subscription = Subscription(
                    user_id=user_id,
                    service_type=subscription_data.get("service_type"),
                    location=subscription_data.get("location"),
                    notification_type=subscription_data.get("notification_type", "telegram"),
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(subscription)
                await session.commit()
                
                return {
                    "id": subscription.id,
                    "user_id": subscription.user_id,
                    "service_type": subscription.service_type,
                    "location": subscription.location,
                    "notification_type": subscription.notification_type,
                    "status": subscription.status,
                    "created_at": subscription.created_at.isoformat(),
                    "updated_at": subscription.updated_at.isoformat()
                }
                
        except IntegrityError as e:
            self.logger.error(f"Failed to create subscription: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating subscription: {e}")
            return None
            
    async def get_subscription(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """Get a subscription by ID."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                subscription = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = subscription.scalar_one_or_none()
                
                if not subscription:
                    return None
                    
                return {
                    "id": subscription.id,
                    "user_id": subscription.user_id,
                    "service_type": subscription.service_type,
                    "location": subscription.location,
                    "notification_type": subscription.notification_type,
                    "status": subscription.status,
                    "created_at": subscription.created_at.isoformat(),
                    "updated_at": subscription.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting subscription: {e}")
            return None
            
    async def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all subscriptions for a user."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                subscriptions = await session.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
                subscriptions = subscriptions.scalars().all()
                
                return [{
                    "id": sub.id,
                    "user_id": sub.user_id,
                    "service_type": sub.service_type,
                    "location": sub.location,
                    "notification_type": sub.notification_type,
                    "status": sub.status,
                    "created_at": sub.created_at.isoformat(),
                    "updated_at": sub.updated_at.isoformat()
                } for sub in subscriptions]
                
        except Exception as e:
            self.logger.error(f"Error getting user subscriptions: {e}")
            return []
            
    async def update_subscription(self, subscription_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a subscription."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                subscription = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = subscription.scalar_one_or_none()
                
                if not subscription:
                    return None
                    
                for key, value in update_data.items():
                    if hasattr(subscription, key):
                        setattr(subscription, key, value)
                subscription.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "id": subscription.id,
                    "user_id": subscription.user_id,
                    "service_type": subscription.service_type,
                    "location": subscription.location,
                    "notification_type": subscription.notification_type,
                    "status": subscription.status,
                    "created_at": subscription.created_at.isoformat(),
                    "updated_at": subscription.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error updating subscription: {e}")
            return None
            
    async def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                subscription = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = subscription.scalar_one_or_none()
                
                if not subscription:
                    return False
                    
                await session.delete(subscription)
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting subscription: {e}")
            return False 