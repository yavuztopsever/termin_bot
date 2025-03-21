"""Integration tests for the parallel booking workflow."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.services.appointment import AppointmentService
from src.services.subscription import SubscriptionService
from src.monitoring.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_booking_manager_initialization(
    mongodb,
    redis_client,
    clean_db
):
    """Test booking manager initialization and shutdown."""
    # Initialize booking manager
    await booking_manager.initialize()
    
    # Verify initialization
    assert booking_manager.semaphore is not None
    assert booking_manager.max_parallel_attempts > 0
    assert booking_manager.booking_timeout > 0
    
    # Close booking manager
    await booking_manager.close()

@pytest.mark.asyncio
async def test_parallel_booking_workflow(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test the complete parallel booking workflow."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize managers
    await booking_manager.initialize()
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
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
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
        
        # Mock API to return multiple available slots
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
                },
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "service_id": "test_service",
                    "location_id": "test_location"
                }
            ]
        }
        
        # Mock API to simulate successful booking on second attempt
        mock_api_config.book_appointment.side_effect = [
            {"success": False, "message": "Slot already taken"},
            {"success": True, "booking_id": "booking123"},
            {"success": False, "message": "Slot already taken"}
        ]
        
        # Get available slots
        slots = await appointment_service.check_availability(
            service_id="test_service",
            location_id="test_location",
            date_from=datetime.now().date().isoformat(),
            date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
        )
        
        assert len(slots) == 3, "Expected 3 available slots"
        
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
        assert details["booking_id"] == "booking123"
        
        # Verify API calls
        assert mock_api_config.book_appointment.call_count >= 2
        
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
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_parallel_booking_all_fail(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test parallel booking when all attempts fail."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize managers
    await booking_manager.initialize()
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
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
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
        
        # Mock API to return multiple available slots
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
        
        # Mock API to simulate all booking attempts failing
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "Slot already taken"
        }
        
        # Get available slots
        slots = await appointment_service.check_availability(
            service_id="test_service",
            location_id="test_location",
            date_from=datetime.now().date().isoformat(),
            date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
        )
        
        assert len(slots) == 2, "Expected 2 available slots"
        
        # Attempt parallel booking
        success, details = await booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=user_id,
            subscription_id=subscription_id
        )
        
        # Verify booking failure
        assert success is False
        assert details is None
        
        # Verify API calls
        assert mock_api_config.book_appointment.call_count == 2
        
        # Verify no appointment in database
        appointments = await mongodb.appointments.find({
            "user_id": str(user_result.inserted_id)
        }).to_list(length=None)
        assert len(appointments) == 0
        
        # Verify subscription status not updated
        updated_subscription = await mongodb.subscriptions.find_one({
            "_id": subscription_result.inserted_id
        })
        assert updated_subscription["status"] == "active"
        
        # Verify metrics
        booking_metrics = metrics.get_all_metrics()
        assert booking_metrics["counters"]["failed_bookings"] >= 1
        
        # Verify failure notification
        notifications = await mongodb.notifications.find({
            "user_id": str(user_result.inserted_id),
            "type": "booking_failed"
        }).to_list(length=None)
        assert len(notifications) > 0
        
    finally:
        # Close managers
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_parallel_booking_timeout(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test parallel booking timeout handling."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    
    # Initialize managers
    await booking_manager.initialize()
    await notification_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Save original timeout
    original_timeout = booking_manager.booking_timeout
    
    try:
        # Set short timeout for test
        booking_manager.booking_timeout = 1.0
        
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
            "status": "active"
        }
        subscription_result = await mongodb.subscriptions.insert_one(subscription_data)
        subscription_id = str(subscription_result.inserted_id)
        
        # Mock API to return multiple available slots
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
        
        # Mock API to simulate slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(2.0)  # Longer than our test timeout
            return {"success": True, "booking_id": "booking123"}
            
        mock_api_config.book_appointment.side_effect = slow_response
        
        # Get available slots
        slots = await appointment_service.check_availability(
            service_id="test_service",
            location_id="test_location",
            date_from=datetime.now().date().isoformat(),
            date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
        )
        
        assert len(slots) == 2, "Expected 2 available slots"
        
        # Attempt parallel booking
        success, details = await booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=user_id,
            subscription_id=subscription_id
        )
        
        # Verify booking timeout
        assert success is False
        assert details is None
        
        # Verify no appointment in database
        appointments = await mongodb.appointments.find({
            "user_id": str(user_result.inserted_id)
        }).to_list(length=None)
        assert len(appointments) == 0
        
        # Verify subscription status not updated
        updated_subscription = await mongodb.subscriptions.find_one({
            "_id": subscription_result.inserted_id
        })
        assert updated_subscription["status"] == "active"
        
        # Verify metrics
        booking_metrics = metrics.get_all_metrics()
        assert booking_metrics["counters"]["timeout_bookings"] >= 1
        
        # Verify timeout notification
        notifications = await mongodb.notifications.find({
            "user_id": str(user_result.inserted_id),
            "type": "booking_failed"
        }).to_list(length=None)
        assert len(notifications) > 0
        
    finally:
        # Restore original timeout
        booking_manager.booking_timeout = original_timeout
        
        # Close managers
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_parallel_vs_sequential_booking(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test performance comparison between parallel and sequential booking."""
    # Initialize services
    appointment_service = AppointmentService()
    
    # Initialize managers
    await booking_manager.initialize()
    
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
                # Simulate some delay to make the test more realistic
                await asyncio.sleep(0.1)
                return {
                    "success": False,
                    "message": "Slot already taken"
                }
        
        # Test sequential booking
        mock_calls = 0
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
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
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
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
        
    finally:
        # Close manager
        await booking_manager.close()

@pytest.mark.asyncio
async def test_integration_with_notification_system(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test integration between booking manager and notification system."""
    # Initialize managers
    await booking_manager.initialize()
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
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
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
        
        # Mock notification manager
        with patch('src.manager.booking_manager.notification_manager') as mock_notification_manager:
            mock_notification_manager.send_appointment_found_notification = AsyncMock()
            mock_notification_manager.send_appointment_booked_notification = AsyncMock()
            mock_notification_manager.send_booking_failed_notification = AsyncMock()
            
            # Get available slots
            slots = [
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
            
            # Verify notification calls
            mock_notification_manager.send_appointment_found_notification.assert_called_once()
            mock_notification_manager.send_appointment_booked_notification.assert_called_once()
            mock_notification_manager.send_booking_failed_notification.assert_not_called()
            
    finally:
        # Close managers
        await booking_manager.close()
        await notification_manager.close()

@pytest.fixture
def mock_api_config():
    """Mock API config for testing."""
    with patch('src.manager.booking_manager.api_config') as mock:
        mock.check_availability = AsyncMock()
        mock.book_appointment = AsyncMock()
        yield mock
