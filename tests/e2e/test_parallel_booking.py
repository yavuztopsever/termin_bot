"""End-to-end tests for the parallel appointment booking system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from telegram import Update, Message, Chat, User as TelegramUser
from telegram.ext import Application

from src.bot import create_bot
from src.models import User, Subscription, Appointment
from src.services.appointment import AppointmentService
from src.services.subscription import SubscriptionService
from src.services.notification import NotificationService
from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.monitoring.metrics import MetricsCollector

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
async def test_parallel_booking_flow(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test parallel booking flow with multiple available slots."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
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
    
    # Mock multiple available slots
    mock_api.return_value.json.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "14:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "15:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "16:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
    }
    
    # Wait for appointment check and notification
    await asyncio.sleep(2)
    
    # Verify appointment notification
    notifications = await mongodb.notifications.find(
        {"user_id": str(user["_id"])}
    ).to_list(length=None)
    
    assert len(notifications) > 0
    assert any(n["type"] == "appointment_found" for n in notifications)
    
    # Get available slots
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) >= 5, "Not enough slots available for parallel booking test"
    
    # Test parallel booking
    user_id = int(user["telegram_id"])
    subscription_id = str(subscription["_id"])
    
    # Reset metrics
    metrics.reset()
    
    # Attempt parallel booking
    success, details = await booking_manager.book_appointment_parallel(
        service_id="test_service",
        location_id="test_location",
        slots=slots,
        user_id=user_id,
        subscription_id=subscription_id
    )
    
    # Verify booking success
    assert success is True
    assert details is not None
    assert "booking_id" in details
    assert "appointment_id" in details
    
    # Verify appointment in database
    appointment = await mongodb.appointments.find_one({
        "booking_id": details["booking_id"]
    })
    assert appointment is not None
    assert appointment["status"] == "booked"
    
    # Verify booking notification
    await asyncio.sleep(1)
    booking_notifications = await mongodb.notifications.find(
        {"user_id": str(user["_id"]),
         "type": "appointment_booked"}
    ).to_list(length=None)
    
    assert len(booking_notifications) > 0
    
    # Verify metrics
    booking_metrics = metrics.get_all_metrics()
    assert booking_metrics["counters"]["successful_bookings"] >= 1
    
    # Verify subscription status update
    updated_subscription = await mongodb.subscriptions.find_one({
        "_id": subscription["_id"]
    })
    assert updated_subscription["status"] == "completed"

@pytest.mark.asyncio
async def test_parallel_booking_timeout(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test parallel booking timeout handling."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
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
    
    # Mock available slots
    mock_api.return_value.json.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
    }
    
    # Get available slots
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) >= 2, "Not enough slots available for timeout test"
    
    # Mock API to simulate timeout
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(2.0)  # Longer than our test timeout
        return {"success": True, "booking_id": "booking123"}
        
    mock_api.book_appointment.side_effect = slow_response
    
    # Override timeout for test
    original_timeout = booking_manager.booking_timeout
    booking_manager.booking_timeout = 1.0  # Short timeout for test
    
    # Reset metrics
    metrics.reset()
    
    try:
        # Attempt parallel booking (should timeout)
        success, details = await booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=int(user["telegram_id"]),
            subscription_id=str(subscription["_id"])
        )
        
        # Verify booking timeout
        assert success is False
        assert details is None
        
        # Verify metrics
        booking_metrics = metrics.get_all_metrics()
        assert booking_metrics["counters"]["timeout_bookings"] >= 1
        
        # Verify timeout notification
        await asyncio.sleep(1)
        timeout_notifications = await mongodb.notifications.find(
            {"user_id": str(user["_id"]),
             "type": "booking_failed"}
        ).to_list(length=None)
        
        assert len(timeout_notifications) > 0
        assert any("timeout" in n["content"].lower() for n in timeout_notifications)
        
    finally:
        # Restore original timeout
        booking_manager.booking_timeout = original_timeout

@pytest.mark.asyncio
async def test_parallel_booking_all_fail(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test parallel booking when all attempts fail."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
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
    
    # Mock available slots
    mock_api.return_value.json.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
    }
    
    # Get available slots
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) >= 2, "Not enough slots available for failure test"
    
    # Mock API to simulate all booking attempts failing
    mock_api.book_appointment.return_value = {
        "success": False,
        "message": "Slot already taken"
    }
    
    # Reset metrics
    metrics.reset()
    
    # Attempt parallel booking (all should fail)
    success, details = await booking_manager.book_appointment_parallel(
        service_id="test_service",
        location_id="test_location",
        slots=slots,
        user_id=int(user["telegram_id"]),
        subscription_id=str(subscription["_id"])
    )
    
    # Verify booking failure
    assert success is False
    assert details is None
    
    # Verify metrics
    booking_metrics = metrics.get_all_metrics()
    assert booking_metrics["counters"]["failed_bookings"] >= 1
    
    # Verify failure notification
    await asyncio.sleep(1)
    failure_notifications = await mongodb.notifications.find(
        {"user_id": str(user["_id"]),
         "type": "booking_failed"}
    ).to_list(length=None)
    
    assert len(failure_notifications) > 0
    
    # Verify subscription status not updated
    updated_subscription = await mongodb.subscriptions.find_one({
        "_id": subscription["_id"]
    })
    assert updated_subscription["status"] != "completed"

@pytest.mark.asyncio
async def test_parallel_booking_performance(
    mongodb,
    redis_client,
    mock_api,
    bot: Application,
    clean_db
):
    """Test performance of parallel booking vs sequential booking."""
    # Initialize services
    appointment_service = AppointmentService()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
    # Create test user
    user_id = 987654321
    user_data = {
        "telegram_id": str(user_id),
        "username": "performance_test",
        "first_name": "Performance",
        "last_name": "Test",
        "settings": {
            "notifications_enabled": True,
            "language": "en"
        }
    }
    await mongodb.users.insert_one(user_data)
    
    # Create test subscription
    subscription_data = {
        "user_id": user_data["_id"],
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    }
    subscription_result = await mongodb.subscriptions.insert_one(subscription_data)
    subscription_id = str(subscription_result.inserted_id)
    
    # Generate many test slots
    num_slots = 20
    slots = [
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": f"{10 + i // 2:02d}:{(i % 2) * 30:02d}",
            "service_id": "test_service",
            "location_id": "test_location"
        }
        for i in range(num_slots)
    ]
    
    # Mock API to simulate successful booking on the 10th attempt
    success_index = 9  # 0-based index
    
    async def mock_book_appointment(*args, **kwargs):
        nonlocal mock_calls
        mock_calls += 1
        
        if mock_calls == success_index + 1:
            return {
                "success": True,
                "booking_id": f"booking_{uuid.uuid4()}"
            }
        else:
            return {
                "success": False,
                "message": "Slot already taken"
            }
    
    # Test sequential booking
    mock_calls = 0
    mock_api.book_appointment.side_effect = mock_book_appointment
    
    # Reset metrics
    metrics.reset()
    
    # Start timer for sequential booking
    sequential_start = datetime.now()
    
    # Attempt sequential booking
    sequential_success = False
    sequential_details = None
    
    for slot in slots:
        result = await appointment_service.book_appointment(
            slot_id=f"{slot['date']}_{slot['time']}_{slot['service_id']}_{slot['location_id']}",
            service_id=slot["service_id"],
            location_id=slot["location_id"],
            user_id=user_id
        )
        
        if result["success"]:
            sequential_success = True
            sequential_details = result
            break
    
    sequential_duration = (datetime.now() - sequential_start).total_seconds()
    
    # Test parallel booking
    mock_calls = 0
    mock_api.book_appointment.side_effect = mock_book_appointment
    
    # Reset metrics
    metrics.reset()
    
    # Start timer for parallel booking
    parallel_start = datetime.now()
    
    # Attempt parallel booking
    parallel_success, parallel_details = await booking_manager.book_appointment_parallel(
        service_id="test_service",
        location_id="test_location",
        slots=slots,
        user_id=user_id,
        subscription_id=subscription_id
    )
    
    parallel_duration = (datetime.now() - parallel_start).total_seconds()
    
    # Verify both approaches succeeded
    assert sequential_success is True
    assert parallel_success is True
    
    # Verify parallel booking is faster
    assert parallel_duration < sequential_duration
    
    # Log performance metrics
    print(f"Sequential booking time: {sequential_duration:.2f}s")
    print(f"Parallel booking time: {parallel_duration:.2f}s")
    print(f"Speedup factor: {sequential_duration / parallel_duration:.2f}x")
    
    # Verify metrics
    booking_metrics = metrics.get_all_metrics()
    assert booking_metrics["counters"]["successful_bookings"] >= 1
