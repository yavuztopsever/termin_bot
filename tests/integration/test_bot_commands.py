"""Integration tests for the bot commands."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from telegram import Update, Message, Chat, User as TelegramUser
from telegram.ext import Application

from src.bot import create_bot
from src.models import User, Subscription, Appointment
from src.services.user import UserService
from src.services.subscription import SubscriptionService
from src.services.appointment import AppointmentService

class MockTelegramUpdate:
    """Mock Telegram update for testing."""
    
    def __init__(
        self,
        message_text: str,
        chat_id: int = 123456789,
        user_id: int = 123456789,
        username: str = "test_user",
        first_name: str = "Test",
        last_name: str = "User"
    ):
        self.message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(
                id=chat_id,
                type="private"
            ),
            from_user=TelegramUser(
                id=user_id,
                is_bot=False,
                first_name=first_name,
                last_name=last_name,
                username=username
            ),
            text=message_text
        )
        
    def to_dict(self) -> Dict:
        """Convert update to dict format."""
        return {
            "update_id": 1,
            "message": {
                "message_id": self.message.message_id,
                "date": int(self.message.date.timestamp()),
                "chat": {
                    "id": self.message.chat.id,
                    "type": self.message.chat.type
                },
                "from": {
                    "id": self.message.from_user.id,
                    "is_bot": self.message.from_user.is_bot,
                    "first_name": self.message.from_user.first_name,
                    "last_name": self.message.from_user.last_name,
                    "username": self.message.from_user.username
                },
                "text": self.message.text
            }
        }

@pytest.fixture
async def bot(mongodb, redis_client):
    """Create a test bot instance."""
    bot = create_bot()
    await bot.initialize()
    return bot

@pytest.mark.asyncio
async def test_start_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /start command."""
    update = MockTelegramUpdate("/start")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify user was created
    user_service = UserService()
    user = await user_service.get_user_by_telegram_id(str(update.message.from_user.id))
    assert user is not None
    assert user.telegram_id == str(update.message.from_user.id)

@pytest.mark.asyncio
async def test_help_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /help command."""
    # Send /help command
    update = MockTelegramUpdate("/help")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify help message was sent
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    help_message = messages[-1]
    assert "help" in help_message["content"].lower()
    assert "commands" in help_message["content"].lower()

@pytest.mark.asyncio
async def test_subscribe_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /subscribe command."""
    # Create user first
    update = MockTelegramUpdate("/start")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Send subscribe command
    subscribe_update = MockTelegramUpdate(
        "/subscribe test_service test_location 2024-03-21 2024-04-21 09:00 17:00"
    )
    await bot.process_update(Update.de_json(subscribe_update.to_dict(), bot.bot))
    
    # Verify subscription was created
    subscription = await mongodb.subscriptions.find_one({
        "service_id": "test_service",
        "location_id": "test_location"
    })
    assert subscription is not None
    assert subscription["time_from"] == "09:00"
    assert subscription["time_to"] == "17:00"
    assert subscription["status"] == "active"

@pytest.mark.asyncio
async def test_check_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /check command."""
    # Create user and subscription first
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    await subscription_service.create_subscription({
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    })
    
    # Send check command
    update = MockTelegramUpdate("/check")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify check was performed
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    check_message = messages[-1]
    assert "checking" in check_message["content"].lower()

@pytest.mark.asyncio
async def test_status_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /status command."""
    # Create user and subscription first
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    subscription = await subscription_service.create_subscription({
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    })
    
    # Send status command
    update = MockTelegramUpdate("/status")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify status was shown
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    status_message = messages[-1]
    assert "test_service" in status_message["content"]
    assert "test_location" in status_message["content"]
    assert "active" in status_message["content"]

@pytest.mark.asyncio
async def test_cancel_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /cancel command."""
    # Create user and subscription first
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    subscription = await subscription_service.create_subscription({
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    })
    
    # Send cancel command
    update = MockTelegramUpdate(f"/cancel {subscription.id}")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify subscription was cancelled
    cancelled_subscription = await mongodb.subscriptions.find_one({
        "_id": subscription.id
    })
    assert cancelled_subscription is None

@pytest.mark.asyncio
async def test_settings_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /settings command."""
    # Create user first
    user_service = UserService()
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Send settings command
    update = MockTelegramUpdate("/settings")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify settings message was sent
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    settings_message = messages[-1]
    assert "settings" in settings_message["content"].lower()
    
    # Test updating settings
    update = MockTelegramUpdate("/settings notification_enabled true")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify settings were updated
    updated_user = await mongodb.users.find_one({"_id": user.id})
    assert updated_user["preferences"]["notification_enabled"] is True

@pytest.mark.asyncio
async def test_locations_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /locations command."""
    # Send locations command
    update = MockTelegramUpdate("/locations")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify locations were shown
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    locations_message = messages[-1]
    assert "locations" in locations_message["content"].lower()

@pytest.mark.asyncio
async def test_services_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /services command."""
    # Send services command
    update = MockTelegramUpdate("/services")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify services were shown
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    services_message = messages[-1]
    assert "services" in services_message["content"].lower()

@pytest.mark.asyncio
async def test_history_command(
    mongodb,
    redis_client,
    bot: Application,
    clean_db
):
    """Test the /history command."""
    # Create user and some activity first
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Create some subscriptions
    for i in range(3):
        await subscription_service.create_subscription({
            "user_id": user.id,
            "service_id": f"service_{i}",
            "location_id": f"location_{i}",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active"
        })
    
    # Send history command
    update = MockTelegramUpdate("/history")
    await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
    
    # Verify history was shown
    messages = await mongodb.messages.find({
        "chat_id": str(update.message.chat.id)
    }).to_list(length=None)
    
    assert len(messages) > 0
    history_message = messages[-1]
    assert "history" in history_message["content"].lower()
    assert "service_0" in history_message["content"]
    assert "service_1" in history_message["content"]
    assert "service_2" in history_message["content"] 