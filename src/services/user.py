"""User service for managing user operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.db import User, db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class UserService:
    """Service for managing user operations."""
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        try:
            async with db.async_session() as session:
                user = User(**user_data)
                session.add(user)
                await session.commit()
                logger.info(f"Created new user: {user.telegram_id}")
                return user
        except IntegrityError:
            logger.error(f"User already exists: {user_data.get('telegram_id')}")
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
            
    @staticmethod
    async def get_user(telegram_id: str) -> Optional[User]:
        """Get a user by Telegram ID."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    logger.info(f"Retrieved user: {telegram_id}")
                else:
                    logger.info(f"User not found: {telegram_id}")
                return user
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise
            
    @staticmethod
    async def update_user(telegram_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user information."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    logger.info(f"User not found for update: {telegram_id}")
                    return False
                    
                for key, value in update_data.items():
                    setattr(user, key, value)
                user.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated user: {telegram_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise
            
    @staticmethod
    async def delete_user(telegram_id: str) -> bool:
        """Delete a user."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    logger.info(f"User not found for deletion: {telegram_id}")
                    return False
                    
                await session.delete(user)
                await session.commit()
                logger.info(f"Deleted user: {telegram_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise
            
    @staticmethod
    async def get_all_users() -> List[User]:
        """Get all users."""
        try:
            async with db.async_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                logger.info(f"Retrieved {len(users)} users")
                return users
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise 