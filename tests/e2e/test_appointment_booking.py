"""End-to-end tests for the appointment booking system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Update, Message, Chat, User as TelegramUser
from telegram.ext import Application

from src.bot import create_bot
from src.models import User, Subscription, Appointment
from src.services.appointment import AppointmentService
from src.services.subscription import SubscriptionService
from src.services.notification import NotificationService
from src.monitoring.metrics import MetricsManager

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

@pytest.mark.asyncio
async def test_complete_booking_flow(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test complete booking flow from user interaction to confirmation."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    notification_service = NotificationService()
    
    # Simulate user starting conversation
    start_update = MockTelegramUpdate("/start")
    await bot.process_update(Update.de_json(start_update.to_dict(), bot.bot))
    
    # Verify user creation
    user = await mongodb.users.find_one({"telegram_id": str(start_update.message.from_user.id)})
    assert user is not None
    
    # Simulate subscription command
    subscribe_update = MockTelegramUpdate(
        "/subscribe test_service test_location 2024-03-21 2024-04-21 09:00 17:00"
    )
    await bot.process_update(Update.de_json(subscribe_update.to_dict(), bot.bot))
    
    # Verify subscription creation
    subscription = await mongodb.subscriptions.find_one({
        "user_id": str(user["_id"]),
        "service_id": "test_service"
    })
    assert subscription is not None
    
    # Wait for appointment check and notification
    await asyncio.sleep(2)
    
    # Verify appointment notification
    notifications = await mongodb.notifications.find(
        {"user_id": str(user["_id"])}
    ).to_list(length=None)
    
    assert len(notifications) > 0
    assert any(n["type"] == "slot_found" for n in notifications)
    
    # Simulate booking command
    slot_notification = next(n for n in notifications if n["type"] == "slot_found")
    slot_id = slot_notification["slot_id"]
    
    book_update = MockTelegramUpdate(f"/book {slot_id}")
    await bot.process_update(Update.de_json(book_update.to_dict(), bot.bot))
    
    # Verify booking status
    appointment = await mongodb.appointments.find_one({
        "user_id": str(user["_id"]),
        "slot_id": slot_id
    })
    assert appointment is not None
    assert appointment["status"] == "booked"
    
    # Verify booking confirmation notification
    await asyncio.sleep(1)
    notifications = await mongodb.notifications.find(
        {"user_id": str(user["_id"]),
         "type": "booking_confirmation"}
    ).to_list(length=None)
    
    assert len(notifications) > 0
    confirmation = notifications[0]
    assert "booking_id" in confirmation["content"]
    assert "confirmation_code" in confirmation["content"]

@pytest.mark.asyncio
async def test_system_resilience(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test system resilience under load."""
    # Create multiple mock users
    users = []
    for i in range(5):
        update = MockTelegramUpdate(
            "/start",
            chat_id=1000000 + i,
            user_id=1000000 + i,
            username=f"test_user_{i}"
        )
        await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
        users.append(update)
    
    # Verify all users were created
    db_users = await mongodb.users.find({}).to_list(length=None)
    assert len(db_users) == 5
    
    # Simulate concurrent subscription requests
    subscription_tasks = []
    for user in users:
        update = MockTelegramUpdate(
            "/subscribe test_service test_location 2024-03-21 2024-04-21 09:00 17:00",
            chat_id=user.message.chat.id,
            user_id=user.message.from_user.id,
            username=user.message.from_user.username
        )
        task = asyncio.create_task(
            bot.process_update(Update.de_json(update.to_dict(), bot.bot))
        )
        subscription_tasks.append(task)
    
    await asyncio.gather(*subscription_tasks)
    
    # Verify all subscriptions were created
    subscriptions = await mongodb.subscriptions.find({}).to_list(length=None)
    assert len(subscriptions) == 5
    
    # Verify system health
    metrics = MetricsManager()
    system_metrics = await metrics.get_system_metrics()
    
    assert system_metrics["cpu_usage"] < 90  # CPU usage should be reasonable
    assert system_metrics["memory_usage"] < 90  # Memory usage should be reasonable
    assert system_metrics["error_rate"] < 0.1  # Error rate should be low

@pytest.mark.asyncio
async def test_error_recovery(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test system recovery from API failures."""
    # Create test user
    start_update = MockTelegramUpdate("/start")
    await bot.process_update(Update.de_json(start_update.to_dict(), bot.bot))
    
    # Create subscription
    subscribe_update = MockTelegramUpdate(
        "/subscribe test_service test_location 2024-03-21 2024-04-21 09:00 17:00"
    )
    await bot.process_update(Update.de_json(subscribe_update.to_dict(), bot.bot))
    
    # Stop mock API to simulate failure
    mock_api.stop()
    
    # Try to check appointments (should fail gracefully)
    check_update = MockTelegramUpdate("/check")
    await bot.process_update(Update.de_json(check_update.to_dict(), bot.bot))
    
    # Verify error was logged
    error_logs = await mongodb.error_logs.find({}).to_list(length=None)
    assert len(error_logs) > 0
    assert any("Connection" in log["error"] for log in error_logs)
    
    # Restart mock API
    mock_api.start()
    
    # Try again (should succeed)
    await bot.process_update(Update.de_json(check_update.to_dict(), bot.bot))
    
    # Verify successful check
    notifications = await mongodb.notifications.find(
        {"user_id": str(start_update.message.from_user.id)}
    ).to_list(length=None)
    
    assert len(notifications) > 0
    assert any(n["type"] == "slot_found" for n in notifications)

@pytest.mark.asyncio
async def test_monitoring_and_metrics(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test monitoring metrics during user activity."""
    metrics = MetricsManager()
    
    # Record initial metrics
    initial_metrics = await metrics.get_system_metrics()
    
    # Generate some activity
    for i in range(3):
        update = MockTelegramUpdate(
            "/start",
            chat_id=2000000 + i,
            user_id=2000000 + i,
            username=f"metrics_user_{i}"
        )
        await bot.process_update(Update.de_json(update.to_dict(), bot.bot))
        
        subscribe_update = MockTelegramUpdate(
            "/subscribe test_service test_location 2024-03-21 2024-04-21 09:00 17:00",
            chat_id=2000000 + i,
            user_id=2000000 + i,
            username=f"metrics_user_{i}"
        )
        await bot.process_update(Update.de_json(subscribe_update.to_dict(), bot.bot))
    
    # Get updated metrics
    updated_metrics = await metrics.get_system_metrics()
    
    # Verify metrics were collected
    assert "request_count" in updated_metrics
    assert "active_users" in updated_metrics
    assert "subscription_count" in updated_metrics
    
    # Verify reasonable values
    assert updated_metrics["request_count"] > initial_metrics["request_count"]
    assert updated_metrics["active_users"] >= 3
    assert updated_metrics["subscription_count"] >= 3
    assert updated_metrics["error_rate"] < 0.1

@pytest.mark.asyncio
async def test_rate_limiting(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test rate limiting functionality."""
    # Create test user
    start_update = MockTelegramUpdate("/start")
    await bot.process_update(Update.de_json(start_update.to_dict(), bot.bot))
    
    # Generate rapid requests
    for _ in range(15):  # Exceeds rate limit
        check_update = MockTelegramUpdate(
            "/check",
            chat_id=start_update.message.chat.id,
            user_id=start_update.message.from_user.id
        )
        await bot.process_update(Update.de_json(check_update.to_dict(), bot.bot))
    
    # Verify rate limit notifications
    notifications = await mongodb.notifications.find(
        {"user_id": str(start_update.message.from_user.id)}
    ).to_list(length=None)
    
    assert any(
        "rate limit" in n["content"].lower()
        for n in notifications
    )
    
    # Wait for rate limit to reset
    await asyncio.sleep(60)
    
    # Try again (should succeed)
    check_update = MockTelegramUpdate(
        "/check",
        chat_id=start_update.message.chat.id,
        user_id=start_update.message.from_user.id
    )
    await bot.process_update(Update.de_json(check_update.to_dict(), bot.bot))
    
    # Verify successful check
    new_notifications = await mongodb.notifications.find(
        {
            "user_id": str(start_update.message.from_user.id),
            "created_at": {"$gt": datetime.now() - timedelta(seconds=5)}
        }
    ).to_list(length=None)
    
    assert len(new_notifications) > 0
    assert not any(
        "rate limit" in n["content"].lower()
        for n in new_notifications
    ) 