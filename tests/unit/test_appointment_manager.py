"""Unit tests for the Appointment Manager Module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import threading
import queue
import time
from aiohttp import ClientSession
from pytest_asyncio import fixture

from src.manager.appointment_manager import AppointmentManager
from src.models import WebsiteConfig
from src.database.db import AsyncDatabase, Subscription, Appointment
from src.exceptions import (
    APIRequestError,
    RateLimitExceeded,
    BookingError,
    ConfigurationError
)
from src.api.api_config import APIConfig

@pytest.fixture
def mock_db():
    """Mock database."""
    mock = AsyncMock()
    mock.get_active_subscriptions.return_value = []
    return mock

@pytest.fixture
def mock_api_config():
    """Mock API configuration."""
    mock = AsyncMock()
    mock._session = AsyncMock()
    mock._check_rate_limit = AsyncMock(return_value=True)
    mock.get_check_availability_request = AsyncMock(return_value={
        "url": "/api/v1/check",
        "method": "POST",
        "data": {}
    })
    mock.get_book_appointment_request = AsyncMock(return_value={
        "url": "/api/v1/book",
        "method": "POST",
        "data": {}
    })
    mock.parse_availability_response = AsyncMock(return_value=[{
        "date": "2024-03-20",
        "time": "14:30"
    }])
    mock.parse_booking_response = AsyncMock(return_value={
        "success": True,
        "booking_id": "12345"
    })
    mock._session.post = AsyncMock()
    mock._session.post.return_value.json = AsyncMock(return_value={
        "slots": [{"date": "2024-03-20", "time": "14:30"}]
    })
    mock._session.post.return_value.status = 200
    return mock

@pytest.fixture
def mock_notify():
    """Mock notification functions."""
    return {
        "found": AsyncMock(),
        "booked": AsyncMock()
    }

@pytest.fixture
def sample_subscription():
    """Sample subscription data."""
    return MagicMock(
        id=1,
        user_id=1,
        service_id="test_service",
        location_id="test_location",
        date_preferences={"date": "2024-03-20"},
        time_preferences={"start": "09:00", "end": "17:00"}
    )

@pytest.fixture
async def appointment_manager(mock_db, mock_api_config, mock_notify):
    """Create an appointment manager instance."""
    with patch("src.manager.appointment_manager.db", mock_db), \
         patch("src.manager.appointment_manager.api_config", mock_api_config), \
         patch("src.manager.appointment_manager.notify_user_appointment_found", mock_notify["found"]), \
         patch("src.manager.appointment_manager.notify_user_appointment_booked", mock_notify["booked"]):
        manager = AppointmentManager()
        await manager.initialize()
        return manager

@pytest.fixture(autouse=True)
async def cleanup_appointment_manager(appointment_manager):
    """Clean up the appointment manager after each test."""
    yield
    await appointment_manager.close()

@pytest.mark.asyncio
async def test_initialization(appointment_manager):
    """Test appointment manager initialization."""
    manager = await appointment_manager
    assert manager is not None
    assert manager.task_queue is not None
    assert manager.workers is not None
    assert manager.scheduler is not None
    assert manager.is_running is True

@pytest.mark.asyncio
async def test_cleanup(appointment_manager):
    """Test cleanup of resources."""
    manager = await appointment_manager
    await manager.close()
    assert manager.is_running is False
    assert len(manager.workers) == 0
    assert manager.scheduler is None

@pytest.mark.asyncio
async def test_start_stop(appointment_manager):
    """Test start and stop functionality."""
    manager = await appointment_manager
    await manager.stop()
    assert manager.is_running is False
    
    await manager.start()
    assert manager.is_running is True
    assert len(manager.workers) > 0
    assert manager.scheduler is not None

@pytest.mark.asyncio
async def test_check_appointments(appointment_manager, sample_subscription, mock_api_config):
    """Test checking appointments."""
    manager = await appointment_manager
    # Stop the scheduler and wait for it to complete
    await manager.stop()
    await asyncio.sleep(0.1)  # Give time for scheduler to stop
    
    # Setup mock responses
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"slots": [{"date": "2024-03-20", "time": "14:30"}]}
    mock_api_config._session.post.return_value = mock_response
    
    # Execute test
    await manager._check_appointments()
    
    # Verify
    mock_api_config._check_rate_limit.assert_awaited_once_with('/api/v1/check')
    mock_api_config._session.post.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_appointments_rate_limit(appointment_manager, sample_subscription, mock_api_config):
    """Test rate limit handling in check appointments."""
    manager = await appointment_manager
    # Stop the scheduler and wait for it to complete
    await manager.stop()
    await asyncio.sleep(0.1)  # Give time for scheduler to stop
    
    # Setup rate limit exceeded
    mock_api_config._check_rate_limit.return_value = False
    
    # Execute test
    await manager._check_appointments()
    
    # Verify
    mock_api_config._check_rate_limit.assert_awaited_once_with('/api/v1/check')
    mock_api_config._session.post.assert_not_awaited()

@pytest.mark.asyncio
async def test_process_booking_task(appointment_manager, sample_subscription, mock_api_config):
    """Test processing a booking task."""
    manager = await appointment_manager
    # Stop the scheduler and wait for it to complete
    await manager.stop()
    await asyncio.sleep(0.1)  # Give time for scheduler to stop
    
    # Setup mock responses
    task = {
        "user_id": sample_subscription.user_id,
        "service_id": sample_subscription.service_id,
        "location_id": sample_subscription.location_id,
        "slot": {
            "date": "2024-03-20",
            "time": "14:30"
        }
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"success": True, "booking_id": "12345"}
    mock_api_config._session.post.return_value = mock_response
    
    # Execute test
    result = await manager._process_booking_task(task)
    
    # Verify
    assert result["success"] is True
    mock_api_config._check_rate_limit.assert_awaited_once_with('/api/v1/book')
    mock_api_config._session.post.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_availability(appointment_manager, mock_api_config):
    """Test checking appointment availability."""
    manager = await appointment_manager
    # Stop the scheduler and wait for it to complete
    await manager.stop()
    await asyncio.sleep(0.1)  # Give time for scheduler to stop
    
    # Setup mock responses
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"slots": [{"date": "2024-03-20", "time": "14:30"}]}
    mock_api_config._session.post.return_value = mock_response
    
    # Execute test
    slots = await manager._check_availability(
        service_id="test_service",
        location_id="test_location",
        date_preferences={"date": "2024-03-20"}
    )
    
    # Verify
    assert len(slots) == 1
    mock_api_config._check_rate_limit.assert_awaited_once_with('/api/v1/check')
    mock_api_config._session.post.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_availability_error(appointment_manager, mock_api_config):
    """Test error handling in check availability."""
    manager = await appointment_manager
    # Stop the scheduler and wait for it to complete
    await manager.stop()
    await asyncio.sleep(0.1)  # Give time for scheduler to stop
    
    # Setup error response
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.json.return_value = {"error": "Internal server error"}
    mock_api_config._session.post.return_value = mock_response
    
    # Execute test
    slots = await manager._check_availability(
        service_id="test_service",
        location_id="test_location",
        date_preferences={"date": "2024-03-20"}
    )
    
    # Verify
    assert len(slots) == 0
    mock_api_config._check_rate_limit.assert_awaited_once_with('/api/v1/check')
    mock_api_config._session.post.assert_awaited_once()

@pytest.mark.asyncio
async def test_matches_preferences(appointment_manager):
    """Test matching appointment slots against user preferences."""
    manager = await appointment_manager
    slot = {
        "date": "2024-03-20",  # Wednesday
        "time": "14:30"
    }
    
    preferences = {
        "date_range": {
            "start": "2024-03-20",
            "end": "2024-03-25"
        },
        "time_range": {
            "start": "09:00",
            "end": "17:00"
        },
        "weekdays": [2, 3]  # Wednesday, Thursday
    }
    
    # Execute test
    result = await manager._matches_preferences(slot, preferences)
    
    # Verify
    assert result is True

@pytest.mark.asyncio
async def test_matches_preferences_outside_range(appointment_manager):
    """Test matching slots outside preferred range."""
    manager = await appointment_manager
    slot = {
        "date": "2024-03-20",
        "time": "08:00"  # Outside time range
    }
    
    preferences = {
        "date_range": {
            "start": "2024-03-20",
            "end": "2024-03-25"
        },
        "time_range": {
            "start": "09:00",
            "end": "17:00"
        }
    }
    
    # Execute test
    result = await manager._matches_preferences(slot, preferences)
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_matches_preferences_invalid_date(appointment_manager):
    """Test matching slots with invalid date format."""
    manager = await appointment_manager
    slot = {
        "date": "invalid_date",
        "time": "14:30"
    }
    
    preferences = {
        "date_range": {
            "start": "2024-03-20",
            "end": "2024-03-25"
        }
    }
    
    # Execute test
    result = await manager._matches_preferences(slot, preferences)
    
    # Verify
    assert result is False 