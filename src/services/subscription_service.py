"""Subscription service for managing subscription operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.db import Subscription, db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SubscriptionService:
    """Service for managing subscription operations."""
    
    @staticmethod
    async def create_subscription(subscription_data: Dict[str, Any]) -> Subscription:
        """Create a new subscription."""
        try:
            async with db.async_session() as session:
                subscription = Subscription(**subscription_data)
                session.add(subscription)
                await session.commit()
                logger.info(f"Created new subscription for user: {subscription.user_id}")
                return subscription
        except IntegrityError:
            logger.error(f"Failed to create subscription: User {subscription_data.get('user_id')} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
            
    @staticmethod
    async def get_subscription(subscription_id: int) -> Optional[Subscription]:
        """Get a subscription by ID."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = result.scalar_one_or_none()
                if subscription:
                    logger.info(f"Retrieved subscription: {subscription_id}")
                else:
                    logger.info(f"Subscription not found: {subscription_id}")
                return subscription
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            raise
            
    @staticmethod
    async def get_user_subscriptions(user_id: int) -> List[Subscription]:
        """Get all subscriptions for a user."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
                subscriptions = result.scalars().all()
                logger.info(f"Retrieved {len(subscriptions)} subscriptions for user: {user_id}")
                return subscriptions
        except Exception as e:
            logger.error(f"Failed to get user subscriptions: {e}")
            raise
            
    @staticmethod
    async def get_active_subscriptions() -> List[Subscription]:
        """Get all active subscriptions."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.status == 'active')
                )
                subscriptions = result.scalars().all()
                logger.info(f"Retrieved {len(subscriptions)} active subscriptions")
                return subscriptions
        except Exception as e:
            logger.error(f"Failed to get active subscriptions: {e}")
            raise
            
    @staticmethod
    async def update_subscription(subscription_id: int, update_data: Dict[str, Any]) -> bool:
        """Update subscription information."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = result.scalar_one_or_none()
                if not subscription:
                    logger.info(f"Subscription not found for update: {subscription_id}")
                    return False
                    
                for key, value in update_data.items():
                    setattr(subscription, key, value)
                subscription.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated subscription: {subscription_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update subscription: {e}")
            raise
            
    @staticmethod
    async def delete_subscription(subscription_id: int) -> bool:
        """Delete a subscription."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = result.scalar_one_or_none()
                if not subscription:
                    logger.info(f"Subscription not found for deletion: {subscription_id}")
                    return False
                    
                await session.delete(subscription)
                await session.commit()
                logger.info(f"Deleted subscription: {subscription_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete subscription: {e}")
            raise
            
    @staticmethod
    async def deactivate_subscription(subscription_id: int) -> bool:
        """Deactivate a subscription."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = result.scalar_one_or_none()
                if not subscription:
                    logger.info(f"Subscription not found for deactivation: {subscription_id}")
                    return False
                    
                subscription.status = 'inactive'
                subscription.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"Deactivated subscription: {subscription_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to deactivate subscription: {e}")
            raise 