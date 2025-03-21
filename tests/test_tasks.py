"""Tests for Celery tasks."""

import pytest
import time
from unittest.mock import patch, MagicMock, call, AsyncMock
from datetime import datetime, timedelta
from src.manager.tasks import (
    check_appointments,
    _handle_available_slots,
    _book_appointment,
    _check_availability,
    _matches_preferences,
    _send_request
)
from src.data.database.database import Database
from src.data.redis.redis_client import RedisClient
from src.data.metrics.metrics_client import MetricsClient
from src.control.health.health_monitor import HealthMonitor
from src.config import settings

@pytest.fixture
def sample_slot():
    """Sample appointment slot data."""
    return {
        "date": datetime.utcnow().date().isoformat(),
        "time": "14:30",
        "location": "Test Location",
        "type": "Regular",
        "available": True
    }

@pytest.fixture
def sample_subscription():
    """Sample subscription data."""
    return {
        "user_id": "123456789",
        "chat_id": "987654321",
        "preferences": {
            "locations": ["Test Location"],
            "appointment_types": ["Regular"],
            "time_ranges": [{"start": "09:00", "end": "17:00"}],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        },
        "active": True,
        "last_check": datetime.utcnow() - timedelta(minutes=30),
        "created_at": datetime.utcnow() - timedelta(days=1)
    }

@pytest.mark.asyncio
async def test_check_appointments(mock_db, mock_api_config, mock_notification_manager, sample_subscription):
    """Test check_appointments function."""
    # Setup mock data
    mock_db.get_subscriptions.return_value = [sample_subscription]
    mock_api_config.check_availability.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "14:30",
                "location": "Test Location",
                "type": "Regular",
                "available": True
            }
        ]
    }
    
    # Execute function
    await check_appointments()
    
    # Verify API call
    mock_api_config.check_availability.assert_called_once()
    mock_notification_manager.send_appointment_found_notification.assert_called_once()

@pytest.mark.asyncio
async def test_handle_available_slots(mock_db, mock_api_config, mock_notification_manager, sample_subscription):
    """Test _handle_available_slots function."""
    # Setup mock data
    slots = [
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "14:30",
            "location": "Test Location",
            "type": "Regular",
            "available": True
        }
    ]
    
    # Execute function
    await _handle_available_slots(slots, sample_subscription)
    
    # Verify API call
    mock_api_config.book_appointment.assert_called_once()
    mock_notification_manager.send_appointment_found_notification.assert_called_once()

@pytest.mark.asyncio
async def test_book_appointment(mock_db, mock_api_config, mock_metrics, mock_notification_manager, sample_slot, sample_subscription):
    """Test book_appointment function."""
    # Setup mock data
    mock_db.add_appointment.return_value = MagicMock()
    mock_api_config.book_appointment.return_value = {
        "success": True,
        "booking_id": "test_booking_id"
    }
    
    # Execute function
    result = await _book_appointment(sample_slot, sample_subscription)
    
    # Verify result and metrics
    assert result is True
    mock_metrics.increment.assert_called_with("appointments_booked")
    mock_notification_manager.send_appointment_booked_notification.assert_called_once()

@pytest.mark.asyncio
async def test_check_availability(mock_api_config):
    """Test _check_availability function."""
    # Setup mock data
    mock_api_config.check_availability.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "14:30",
                "location": "Test Location",
                "type": "Regular",
                "available": True
            }
        ]
    }
    
    # Execute function
    result = await _check_availability("test_service", "test_location")
    
    # Verify result
    assert result is not None
    assert "slots" in result
    assert len(result["slots"]) == 1

def test_matches_preferences(sample_slot):
    """Test _matches_preferences function."""
    # Test with matching preferences
    preferences = {
        "time_ranges": [{"start": "09:00", "end": "17:00"}],
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }
    assert _matches_preferences(sample_slot, preferences) is True
    
    # Test with non-matching preferences
    preferences = {
        "time_ranges": [{"start": "15:00", "end": "17:00"}],
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }
    assert _matches_preferences(sample_slot, preferences) is False

@pytest.mark.asyncio
async def test_send_request(mock_api_config):
    """Test _send_request function."""
    # Setup mock data
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": True}
    mock_api_config._session.post.return_value = mock_response
    
    # Execute function
    result = await _send_request(
        url="http://test.com",
        method="POST",
        headers={},
        json={}
    )
    
    # Verify result
    assert result is not None
    assert result.status == 200
    assert await result.json() == {"success": True}

@pytest.mark.asyncio
async def test_check_appointments_error_handling(mock_db, mock_metrics, mock_notification_manager):
    """Test error handling in check_appointments task."""
    # Setup mock to raise exception
    mock_db.get_subscriptions.side_effect = Exception("Test error")
    
    # Execute task and verify error handling
    await check_appointments()
    mock_metrics.increment.assert_called_with("task_errors")
    mock_notification_manager.send_booking_failed_notification.assert_called_once()

@pytest.mark.asyncio
async def test_book_appointment_rate_limit(
    mock_api_config,
    mock_metrics,
    mock_notification_manager,
    sample_slot,
    sample_subscription
):
    """Test rate limiting in book_appointment function."""
    # Mock rate limit exceeded
    mock_api_config.book_appointment.side_effect = Exception("Rate limit exceeded")
    
    # Execute function
    result = await _book_appointment(sample_slot, sample_subscription)
    
    # Verify result
    assert result is False
    mock_metrics.increment.assert_called_with("rate_limit_exceeded")
    mock_notification_manager.send_booking_failed_notification.assert_called_once()

@pytest.mark.asyncio
async def test_database_operations(database):
    """Test database operations."""
    # Test user operations
    user_id = "test_user_123"
    username = "test_user"
    password_hash = "test_hash"
    email = "test@example.com"
    
    # Create user
    success = database.create_user(user_id, username, password_hash, email)
    assert success
    
    # Get user
    user = database.get_user(user_id)
    assert user is not None
    assert user["id"] == user_id
    assert user["username"] == username
    assert user["email"] == email
    
    # Test appointment operations
    appointment_id = "test_appointment_123"
    service_id = "test_service"
    location_id = "test_location"
    date = datetime.now().date().isoformat()
    time = "14:30"
    
    # Create appointment
    success = database.create_appointment(
        appointment_id,
        user_id,
        service_id,
        location_id,
        date,
        time
    )
    assert success
    
    # Get appointment
    appointment = database.get_appointment(appointment_id)
    assert appointment is not None
    assert appointment["id"] == appointment_id
    assert appointment["user_id"] == user_id
    assert appointment["service_id"] == service_id
    assert appointment["location_id"] == location_id
    assert appointment["date"] == date
    assert appointment["time"] == time
    assert appointment["status"] == "pending"
    
    # Update appointment status
    success = database.update_appointment_status(appointment_id, "booked")
    assert success
    
    # Get updated appointment
    appointment = database.get_appointment(appointment_id)
    assert appointment["status"] == "booked"
    
    # Test notification operations
    notification_id = "test_notification_123"
    message = "Test notification"
    type = "appointment_available"
    
    # Create notification
    success = database.create_notification(
        notification_id,
        user_id,
        message,
        type
    )
    assert success
    
    # Get notification
    notification = database.get_notification(notification_id)
    assert notification is not None
    assert notification["id"] == notification_id
    assert notification["user_id"] == user_id
    assert notification["message"] == message
    assert notification["type"] == type
    assert notification["status"] == "pending"
    
    # Update notification status
    success = database.update_notification_status(notification_id, "sent")
    assert success
    
    # Get updated notification
    notification = database.get_notification(notification_id)
    assert notification["status"] == "sent"

@pytest.mark.asyncio
async def test_redis_operations(redis):
    """Test Redis operations."""
    # Test key-value operations
    key = "test_key"
    value = "test_value"
    
    # Set value
    success = await redis.set(key, value)
    assert success
    
    # Get value
    result = await redis.get(key)
    assert result == value
    
    # Check key exists
    exists = await redis.exists(key)
    assert exists
    
    # Delete key
    success = await redis.delete(key)
    assert success
    
    # Verify key is deleted
    exists = await redis.exists(key)
    assert not exists
    
    # Test queue operations
    queue = "test_queue"
    items = ["item1", "item2", "item3"]
    
    # Push items to queue
    for item in items:
        success = await redis.push_to_queue(queue, item)
        assert success
    
    # Get queue length
    length = await redis.get_queue_length(queue)
    assert length == len(items)
    
    # Pop items from queue
    for item in items:
        result = await redis.pop_from_queue(queue)
        assert result == item
    
    # Verify queue is empty
    length = await redis.get_queue_length(queue)
    assert length == 0
    
    # Test set operations
    set_name = "test_set"
    members = ["member1", "member2", "member3"]
    
    # Add members to set
    for member in members:
        success = await redis.add_to_set(set_name, member)
        assert success
    
    # Get set members
    result = await redis.get_set_members(set_name)
    assert set(result) == set(members)
    
    # Check member exists
    exists = await redis.is_set_member(set_name, members[0])
    assert exists
    
    # Remove member from set
    success = await redis.remove_from_set(set_name, members[0])
    assert success
    
    # Verify member is removed
    exists = await redis.is_set_member(set_name, members[0])
    assert not exists

@pytest.mark.asyncio
async def test_metrics_operations(metrics):
    """Test metrics operations."""
    # Test request metrics
    client_id = "test_client"
    status = "success"
    operation = "test_operation"
    duration = 0.5
    
    # Record request
    metrics.record_request(client_id, status, operation, duration)
    
    # Test resource metrics
    instance = "test_instance"
    cpu_percent = 50.0
    memory_bytes = 1024 * 1024  # 1MB
    disk_bytes = 1024 * 1024 * 1024  # 1GB
    
    # Record resource usage
    metrics.record_resource_usage(
        instance,
        cpu_percent,
        memory_bytes,
        disk_bytes
    )
    
    # Test appointment metrics
    status = "booked"
    
    # Record appointment
    metrics.record_appointment(status)
    
    # Test notification metrics
    type = "appointment_available"
    status = "sent"
    
    # Record notification
    metrics.record_notification(type, status)
    
    # Test error metrics
    type = "test_error"
    component = "test_component"
    
    # Record error
    metrics.record_error(type, component)
    
    # Get metrics
    metrics_text = metrics.get_metrics()
    assert metrics_text is not None
    assert len(metrics_text) > 0
    
    # Reset metrics
    metrics.reset_metrics()
    
    # Verify metrics were reset
    assert metrics.request_counter._value.get() == 0
    assert metrics.error_counter._value.get() == 0 