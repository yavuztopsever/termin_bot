"""Database connection and operations."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.future import select

from src.config.config import DATABASE_URL
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create base class for declarative models
Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    language_code = Column(String, default='en')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(Base):
    """Subscription model."""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service_id = Column(String, nullable=False)
    location_id = Column(String)
    preferences = Column(JSON)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Appointment(Base):
    """Appointment model."""
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(String, nullable=False)
    location_id = Column(String)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, default='available')
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    """Notification model."""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    error_message = Column(String)

class WebsiteConfig(Base):
    """Website configuration model."""
    __tablename__ = 'website_config'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(String, nullable=False)
    location_id = Column(String)
    url = Column(String, nullable=False)
    api_endpoints = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AsyncDatabase:
    """Asynchronous database operations."""

    def __init__(self, test_mode: bool = False):
        """Initialize database connection."""
        self.engine = create_async_engine(
            DATABASE_URL if not test_mode else "sqlite+aiosqlite:///test.db",
            echo=True if os.getenv("DEBUG", "false").lower() == "true" else False
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def connect(self) -> None:
        """Create database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def close(self) -> None:
        """Close database connection."""
        try:
            await self.engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close database connection: {e}")
            raise

    async def add_user(self, user_data: Dict[str, Any]) -> User:
        """Add a new user to the database."""
        async with self.async_session() as session:
            try:
                user = User(**user_data)
                session.add(user)
                await session.commit()
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add user: {e}")
                raise

    async def get_user(self, telegram_id: str) -> Optional[User]:
        """Get a user by telegram ID."""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def add_subscription(self, subscription_data: Dict[str, Any]) -> Subscription:
        """Add a new subscription to the database."""
        async with self.async_session() as session:
            try:
                subscription = Subscription(**subscription_data)
                session.add(subscription)
                await session.commit()
                return subscription
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add subscription: {e}")
                raise

    async def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.status == 'active')
            )
            return result.scalars().all()

    async def add_appointment(self, appointment_data: Dict[str, Any]) -> Appointment:
        """Add a new appointment to the database."""
        async with self.async_session() as session:
            try:
                appointment = Appointment(**appointment_data)
                session.add(appointment)
                await session.commit()
                return appointment
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add appointment: {e}")
                raise

    async def add_notification(self, notification_data: Dict[str, Any]) -> Notification:
        """Add a new notification to the database."""
        async with self.async_session() as session:
            try:
                notification = Notification(**notification_data)
                session.add(notification)
                await session.commit()
                return notification
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add notification: {e}")
                raise

    async def get_website_config(self) -> Optional[Dict[str, Any]]:
        """Get the website configuration."""
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(WebsiteConfig).order_by(WebsiteConfig.updated_at.desc())
                )
                config = result.scalar_one_or_none()
                if config:
                    return {
                        'service_id': config.service_id,
                        'location_id': config.location_id,
                        'url': config.url,
                        'api_endpoints': config.api_endpoints
                    }
                return None
            except Exception as e:
                logger.error(f"Failed to get website configuration: {e}")
                raise

    async def add_website_config(self, config_data: Dict[str, Any]) -> WebsiteConfig:
        """Add a new website configuration."""
        async with self.async_session() as session:
            try:
                config = WebsiteConfig(**config_data)
                session.add(config)
                await session.commit()
                return config
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add website configuration: {e}")
                raise

# Create a database instance
db = AsyncDatabase() 