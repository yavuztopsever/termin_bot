"""Integration tests for task system and booking manager integration."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, AsyncMock, MagicMock

from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.manager.tasks import TaskManager, task_manager
from src.monitoring.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_task_manager_booking_integration(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test integration between task manager and booking manager."""
    # Initialize managers
    await booking_manager.initialize()
    await notification_manager.initialize()
    await task_manager.initialize()
    
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
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active",
            "auto_book": True
        }
        subscription_result = await mongodb.subscriptions.insert_one(subscription_data)
        
        # Mock API to return available slots
        mock_api_config.check_availability.return_value = {
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
        
        # Mock API to simulate successful booking
        mock_api_config.book_appointment.return_value = {
            "success": True,
            "booking_id": "booking123"
        }
        
        # Trigger check_appointments task
        await task_manager.check_appointments()
        
        # Wait for async operations to complete
        await asyncio.sleep(1)
        
        # Verify appointment in database
        appointment = await mongodb.appointments.find_one({
            "booking_id": "booking123"
        })
        assert appointment is not None
        assert appointment["status"] == "booked"
        
        # Verify subscription status update
        updated_subscription = await mongodb.subscriptions.find_one({
            "_id": subscription_result.inserted_id
        })
        assert updated_subscription["status"] == "completed"
        
        # Verify metrics
        booking_metrics = metrics.get_all_metrics()
        assert booking_metrics["counters"]["successful_bookings"] >= 1
        
    finally:
        # Close managers
        await task_manager.close()
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_task_scheduling(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test task scheduling for appointment checks."""
    # Mock task manager's check_appointments method
    with patch('src.manager.tasks.TaskManager.check_appointments', new_callable=AsyncMock) as mock_check:
        # Initialize task manager
        test_task_manager = TaskManager()
        await test_task_manager.initialize()
        
        try:
            # Start scheduled tasks
            test_task_manager.start_scheduled_tasks()
            
            # Wait for scheduled task to run (should run immediately)
            await asyncio.sleep(1)
            
            # Verify check_appointments was called
            mock_check.assert_called()
            
            # Stop scheduled tasks
            test_task_manager.stop_scheduled_tasks()
            
        finally:
            # Close task manager
            await test_task_manager.close()

@pytest.mark.asyncio
async def test_task_error_handling(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test error handling in task execution."""
    # Initialize managers
    await booking_manager.initialize()
    await notification_manager.initialize()
    await task_manager.initialize()
    
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
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active",
            "auto_book": True
        }
        await mongodb.subscriptions.insert_one(subscription_data)
        
        # Mock API to simulate error
        mock_api_config.check_availability.side_effect = Exception("Test error")
        
        # Trigger check_appointments task (should handle error gracefully)
        await task_manager.check_appointments()
        
        # Wait for async operations to complete
        await asyncio.sleep(1)
        
        # Verify error was logged
        error_logs = await mongodb.error_logs.find({}).to_list(length=None)
        assert len(error_logs) > 0
        assert any("Test error" in log.get("message", "") for log in error_logs)
        
        # Verify metrics
        error_metrics = metrics.get_all_metrics()
        assert error_metrics["counters"]["task_errors"] >= 1
        
    finally:
        # Close managers
        await task_manager.close()
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_multiple_subscriptions_handling(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test handling of multiple subscriptions."""
    # Initialize managers
    await booking_manager.initialize()
    await notification_manager.initialize()
    await task_manager.initialize()
    
    try:
        # Create test users
        user1_id = 111111
        user2_id = 222222
        
        user1_data = {
            "telegram_id": str(user1_id),
            "username": "user1",
            "first_name": "User",
            "last_name": "One",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user1_result = await mongodb.users.insert_one(user1_data)
        
        user2_data = {
            "telegram_id": str(user2_id),
            "username": "user2",
            "first_name": "User",
            "last_name": "Two",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user2_result = await mongodb.users.insert_one(user2_data)
        
        # Create test subscriptions
        subscription1_data = {
            "user_id": str(user1_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "12:00",
            "status": "active",
            "auto_book": True
        }
        await mongodb.subscriptions.insert_one(subscription1_data)
        
        subscription2_data = {
            "user_id": str(user2_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "13:00",
            "time_to": "17:00",
            "status": "active",
            "auto_book": True
        }
        await mongodb.subscriptions.insert_one(subscription2_data)
        
        # Mock API to return different slots for different time ranges
        async def mock_check_availability(*args, **kwargs):
            time_from = kwargs.get("time_from", "")
            
            if time_from == "09:00":
                # Morning slots for user 1
                return {
                    "slots": [
                        {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": "10:00",
                            "service_id": "test_service",
                            "location_id": "test_location"
                        }
                    ]
                }
            else:
                # Afternoon slots for user 2
                return {
                    "slots": [
                        {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": "14:00",
                            "service_id": "test_service",
                            "location_id": "test_location"
                        }
                    ]
                }
                
        mock_api_config.check_availability.side_effect = mock_check_availability
        
        # Mock API to simulate successful booking
        booking_id_counter = 0
        
        async def mock_book_appointment(*args, **kwargs):
            nonlocal booking_id_counter
            booking_id_counter += 1
            return {
                "success": True,
                "booking_id": f"booking{booking_id_counter}"
            }
            
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
        # Trigger check_appointments task
        await task_manager.check_appointments()
        
        # Wait for async operations to complete
        await asyncio.sleep(1)
        
        # Verify appointments in database
        appointments = await mongodb.appointments.find({}).to_list(length=None)
        assert len(appointments) == 2
        
        # Verify each user got their own appointment
        user1_appointments = [a for a in appointments if a["user_id"] == str(user1_result.inserted_id)]
        user2_appointments = [a for a in appointments if a["user_id"] == str(user2_result.inserted_id)]
        
        assert len(user1_appointments) == 1
        assert len(user2_appointments) == 1
        
        assert user1_appointments[0]["time"] == "10:00"
        assert user2_appointments[0]["time"] == "14:00"
        
    finally:
        # Close managers
        await task_manager.close()
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_daily_digest_task(
    mongodb,
    redis_client,
    clean_db
):
    """Test daily digest task execution."""
    # Initialize managers
    await notification_manager.initialize()
    await task_manager.initialize()
    
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
        
        # Mock notification_manager's send_daily_digest method
        with patch('src.manager.notification_manager.NotificationManager.send_daily_digest', new_callable=AsyncMock) as mock_digest:
            # Trigger send_daily_digests task
            await task_manager.send_daily_digests()
            
            # Wait for async operations to complete
            await asyncio.sleep(1)
            
            # Verify send_daily_digest was called for the user
            mock_digest.assert_called_once_with(user_id)
            
    finally:
        # Close managers
        await task_manager.close()
        await notification_manager.close()

@pytest.fixture
def mock_api_config():
    """Mock API config for testing."""
    with patch('src.manager.tasks.api_config') as mock:
        mock.check_availability = AsyncMock()
        mock.book_appointment = AsyncMock()
        yield mock
