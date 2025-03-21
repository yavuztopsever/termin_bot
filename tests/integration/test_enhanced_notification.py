"""Integration tests for the enhanced notification system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from src.manager.notification_manager import notification_manager
from src.monitoring.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_notification_manager_initialization(
    mongodb,
    redis_client,
    clean_db
):
    """Test notification manager initialization and shutdown."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    # Verify initialization
    assert notification_manager.application is not None
    
    # Close notification manager
    await notification_manager.close()

@pytest.mark.asyncio
async def test_rich_message_formatting(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test rich message formatting with HTML and emojis."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Test appointment found notification
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00",
            "parallel_attempts": 3
        }
        
        # Send notification
        success = await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Verify notification was sent
        assert success is True
        
        # Verify message formatting
        mock_telegram_bot.send_message.assert_called_once()
        call_args = mock_telegram_bot.send_message.call_args[1]
        
        # Check HTML formatting
        assert "<b>" in call_args["text"]
        assert "</b>" in call_args["text"]
        
        # Check emoji usage
        assert "🎉" in call_args["text"]
        
        # Check content
        assert "Found an available appointment" in call_args["text"]
        assert "Residence Registration" in call_args["text"]
        assert "KVR Munich" in call_args["text"]
        assert "2025-04-01" in call_args["text"]
        assert "10:00" in call_args["text"]
        assert "multiple slots" in call_args["text"]
        
        # Check parse mode
        assert call_args["parse_mode"] == "HTML"
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_inline_buttons(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test inline buttons in notifications."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Test appointment booked notification
        booking_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00",
            "booking_id": "booking123",
            "location_coordinates": [48.137154, 11.576124]  # Munich coordinates
        }
        
        # Send notification
        success = await notification_manager.send_appointment_booked_notification(
            user_id=user_id,
            booking_details=booking_details
        )
        
        # Verify notification was sent
        assert success is True
        
        # Verify inline buttons
        mock_telegram_bot.send_message.assert_called_once()
        call_args = mock_telegram_bot.send_message.call_args[1]
        
        # Check reply markup
        assert call_args["reply_markup"] is not None
        
        # Convert reply markup to dict for easier testing
        reply_markup_dict = call_args["reply_markup"].to_dict()
        
        # Check buttons
        assert len(reply_markup_dict["inline_keyboard"]) >= 2
        
        # Check first row buttons
        first_row = reply_markup_dict["inline_keyboard"][0]
        assert len(first_row) == 2
        assert first_row[0]["text"] == "Add to Calendar"
        assert "calendar_" in first_row[0]["callback_data"]
        assert first_row[1]["text"] == "Cancel Booking"
        assert "cancel_" in first_row[1]["callback_data"]
        
        # Check Google Maps button (URL button)
        maps_button = None
        for row in reply_markup_dict["inline_keyboard"]:
            for button in row:
                if "Open in Google Maps" in button.get("text", ""):
                    maps_button = button
                    break
        
        assert maps_button is not None
        assert "url" in maps_button
        assert "google.com/maps" in maps_button["url"]
        assert "48.137154" in maps_button["url"]
        assert "11.576124" in maps_button["url"]
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_notification_preferences(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test notification preferences and filtering."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test users with different preferences
        users = [
            {
                "telegram_id": "111111",
                "username": "user1",
                "first_name": "User",
                "last_name": "One",
                "settings": {
                    "notifications_enabled": True,
                    "notification_frequency": "immediate",
                    "notification_types": ["all"]
                }
            },
            {
                "telegram_id": "222222",
                "username": "user2",
                "first_name": "User",
                "last_name": "Two",
                "settings": {
                    "notifications_enabled": True,
                    "notification_frequency": "booked_only",
                    "notification_types": ["appointment_booked", "booking_reminder"]
                }
            },
            {
                "telegram_id": "333333",
                "username": "user3",
                "first_name": "User",
                "last_name": "Three",
                "settings": {
                    "notifications_enabled": False,
                    "notification_frequency": "immediate",
                    "notification_types": ["all"]
                }
            }
        ]
        
        for user in users:
            await mongodb.users.insert_one(user)
        
        # Test notification for all users
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00"
        }
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # Send appointment found notification to all users
        for user in users:
            await notification_manager.send_appointment_found_notification(
                user_id=int(user["telegram_id"]),
                appointment_details=appointment_details
            )
        
        # Verify notifications based on preferences
        # User 1: Should receive (all notifications enabled)
        # User 2: Should not receive (only booked notifications)
        # User 3: Should not receive (notifications disabled)
        assert mock_telegram_bot.send_message.call_count == 1
        
        # Verify the call was for User 1
        call_args = mock_telegram_bot.send_message.call_args[1]
        assert call_args["chat_id"] == 111111
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # Send booking notification to all users
        booking_details = {
            **appointment_details,
            "booking_id": "booking123"
        }
        
        for user in users:
            await notification_manager.send_appointment_booked_notification(
                user_id=int(user["telegram_id"]),
                booking_details=booking_details
            )
        
        # Verify notifications based on preferences
        # User 1: Should receive (all notifications enabled)
        # User 2: Should receive (booked notifications enabled)
        # User 3: Should not receive (notifications disabled)
        assert mock_telegram_bot.send_message.call_count == 2
        
        # Verify calls were for User 1 and User 2
        chat_ids = [
            call[1]["chat_id"]
            for call in mock_telegram_bot.send_message.call_args_list
        ]
        assert 111111 in chat_ids
        assert 222222 in chat_ids
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_notification_cooldown(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test notification cooldown periods."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Test appointment found notification
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00"
        }
        
        # Send first notification
        success1 = await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Verify first notification was sent
        assert success1 is True
        assert mock_telegram_bot.send_message.call_count == 1
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # Send second notification immediately (should be on cooldown)
        success2 = await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details={
                **appointment_details,
                "time": "11:00"
            }
        )
        
        # Verify second notification was not sent due to cooldown
        assert success2 is False
        assert mock_telegram_bot.send_message.call_count == 0
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # Send high priority notification (should bypass cooldown)
        success3 = await notification_manager.notify_user(
            user_id=user_id,
            notification_type="appointment_found",
            content=appointment_details,
            priority="high"
        )
        
        # Verify high priority notification was sent despite cooldown
        assert success3 is True
        assert mock_telegram_bot.send_message.call_count == 1
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_notification_types(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test different notification types."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Test all notification types
        
        # 1. Appointment Found
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00",
            "parallel_attempts": 3
        }
        
        success1 = await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        assert success1 is True
        assert mock_telegram_bot.send_message.call_count == 1
        assert "Found an available appointment" in mock_telegram_bot.send_message.call_args[1]["text"]
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # 2. Appointment Booked
        booking_details = {
            **appointment_details,
            "booking_id": "booking123"
        }
        
        success2 = await notification_manager.send_appointment_booked_notification(
            user_id=user_id,
            booking_details=booking_details
        )
        
        assert success2 is True
        assert mock_telegram_bot.send_message.call_count == 1
        assert "Successfully booked an appointment" in mock_telegram_bot.send_message.call_args[1]["text"]
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # 3. Booking Failed
        failure_details = {
            **appointment_details,
            "reason": "Slot already taken"
        }
        
        success3 = await notification_manager.send_booking_failed_notification(
            user_id=user_id,
            booking_details=failure_details
        )
        
        assert success3 is True
        assert mock_telegram_bot.send_message.call_count == 1
        assert "Booking attempt failed" in mock_telegram_bot.send_message.call_args[1]["text"]
        assert "Slot already taken" in mock_telegram_bot.send_message.call_args[1]["text"]
        
        # Reset mock
        mock_telegram_bot.send_message.reset_mock()
        
        # 4. Booking Reminder
        reminder_details = {
            **booking_details,
            "days_left": 1
        }
        
        success4 = await notification_manager.send_booking_reminder_notification(
            user_id=user_id,
            booking_details=reminder_details
        )
        
        assert success4 is True
        assert mock_telegram_bot.send_message.call_count == 1
        assert "Appointment Reminder" in mock_telegram_bot.send_message.call_args[1]["text"]
        assert "tomorrow" in mock_telegram_bot.send_message.call_args[1]["text"]
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_daily_digest(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test daily digest for batched notifications."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "daily",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Create pending notifications
        notifications = [
            {
                "user_id": str(user_result.inserted_id),
                "type": "appointment_found",
                "status": "pending",
                "content": {
                    "service_id": "service1",
                    "service_name": "Residence Registration",
                    "location_id": "location1",
                    "location_name": "KVR Munich",
                    "date": "2025-04-01",
                    "time": "10:00"
                },
                "created_at": datetime.utcnow()
            },
            {
                "user_id": str(user_result.inserted_id),
                "type": "appointment_found",
                "status": "pending",
                "content": {
                    "service_id": "service1",
                    "service_name": "Residence Registration",
                    "location_id": "location1",
                    "location_name": "KVR Munich",
                    "date": "2025-04-01",
                    "time": "11:00"
                },
                "created_at": datetime.utcnow()
            },
            {
                "user_id": str(user_result.inserted_id),
                "type": "booking_failed",
                "status": "pending",
                "content": {
                    "service_id": "service2",
                    "service_name": "Passport Application",
                    "location_id": "location2",
                    "location_name": "KVR Pasing",
                    "date": "2025-04-02",
                    "time": "14:00",
                    "reason": "Slot already taken"
                },
                "created_at": datetime.utcnow()
            }
        ]
        
        for notification in notifications:
            await mongodb.notifications.insert_one(notification)
        
        # Send daily digest
        success = await notification_manager.send_daily_digest(user_id)
        
        # Verify digest was sent
        assert success is True
        assert mock_telegram_bot.send_message.call_count == 1
        
        # Check digest content
        digest_text = mock_telegram_bot.send_message.call_args[1]["text"]
        assert "Daily Notification Digest" in digest_text
        assert "Found 2 available appointments" in digest_text
        assert "1 booking attempts failed" in digest_text
        
        # Verify notifications were marked as sent
        updated_notifications = await mongodb.notifications.find({
            "user_id": str(user_result.inserted_id)
        }).to_list(length=None)
        
        for notification in updated_notifications:
            assert notification["status"] == "sent"
            assert "sent_at" in notification
            
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_metrics_tracking(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test metrics tracking for notifications."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Send test notification
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00"
        }
        
        await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Verify metrics
        notification_metrics = metrics.get_all_metrics()
        assert notification_metrics["counters"]["notifications_sent"] >= 1
        assert notification_metrics["counters"]["notification_type_appointment_found"] >= 1
        
        # Simulate notification error
        mock_telegram_bot.send_message.side_effect = Exception("Test error")
        
        await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Verify error metrics
        updated_metrics = metrics.get_all_metrics()
        assert updated_metrics["counters"]["notification_errors"] >= 1
        
    finally:
        # Close notification manager
        await notification_manager.close()

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    with patch('src.manager.notification_manager.Application') as mock:
        mock.builder.return_value.token.return_value.build.return_value = MagicMock()
        mock.builder.return_value.token.return_value.build.return_value.bot = MagicMock()
        mock.builder.return_value.token.return_value.build.return_value.bot.send_message = AsyncMock()
        mock.builder.return_value.token.return_value.build.return_value.shutdown = AsyncMock()
        yield mock.builder.return_value.token.return_value.build.return_value.bot
