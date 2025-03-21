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
    """Mock database for testing."""
    with patch('src.manager.appointment_manager.db') as mock:
        mock.get_subscriptions = AsyncMock()
        mock.add_appointment = AsyncMock()
        mock.update_subscription = AsyncMock()
        yield mock

@pytest.fixture
def mock_api_config():
    """Mock API config for testing."""
    with patch('src.manager.appointment_manager.api_config') as mock:
        mock.check_availability = AsyncMock()
        mock.book_appointment = AsyncMock()
        yield mock

@pytest.fixture
def mock_notification_manager():
    """Mock notification manager for testing."""
    with patch('src.manager.appointment_manager.notification_manager') as mock:
        mock.send_appointment_found_notification = AsyncMock()
        mock.send_appointment_booked_notification = AsyncMock()
        mock.send_booking_failed_notification = AsyncMock()
        yield mock

@pytest.fixture
def sample_subscription():
    """Sample subscription data for testing."""
    return {
        "user_id": "test_user_id",
        "service_id": "test_service",
        "location_id": "test_location",
        "preferences": {
            "time_ranges": [
                {"start": "09:00", "end": "17:00"}
            ],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    }

@pytest.fixture
async def appointment_manager(mock_db, mock_api_config, mock_notification_manager):
    """Create an appointment manager instance."""
    with patch("src.manager.appointment_manager.db", mock_db), \
         patch("src.manager.appointment_manager.api_config", mock_api_config), \
         patch("src.manager.appointment_manager.notification_manager", mock_notification_manager):
        manager = AppointmentManager()
        await manager.initialize()
        return manager

@pytest.fixture(autouse=True)
async def cleanup_appointment_manager(appointment_manager):
    """Clean up the appointment manager after each test."""
    yield
    await appointment_manager.close()

@pytest.mark.asyncio
async def test_initialization(mock_db, mock_api_config, mock_notification_manager):
    """Test appointment manager initialization."""
    manager = await appointment_manager
    assert manager is not None
    assert manager.task_queue is not None
    assert manager.workers is not None
    assert manager.scheduler is not None
    assert manager.is_running is True
    
    await manager.stop()

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
async def test_check_appointments(mock_db, mock_api_config, sample_subscription):
    """Test check_appointments method."""
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
    
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Execute test
        await manager.check_appointments()
        
        # Verify API call
        mock_api_config.check_availability.assert_called_once()
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_check_appointments_rate_limit(mock_db, mock_api_config):
    """Test rate limiting in check_appointments method."""
    # Setup mock data
    mock_db.get_subscriptions.return_value = [{"service_id": "test_service"}]
    mock_api_config.check_availability.side_effect = [
        {"slots": []},
        {"slots": []},
        {"slots": []}
    ]
    
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Execute test
        await manager.check_appointments()
        
        # Verify rate limiting
        assert mock_api_config.check_availability.call_count <= 2
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_process_booking_task(mock_db, mock_api_config, sample_subscription):
    """Test processing a booking task."""
    # Setup mock data
    task = {
        "user_id": sample_subscription["user_id"],
        "service_id": sample_subscription["service_id"],
        "location_id": sample_subscription["location_id"],
        "slot": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "14:30"
        }
    }
    
    mock_api_config.book_appointment.return_value = {
        "success": True,
        "booking_id": "test_booking_id"
    }
    
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Execute test
        result = await manager._process_booking_task(task)
        
        # Verify result
        assert result["success"] is True
        assert "booking_id" in result
        assert result["booking_id"] == "test_booking_id"
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_check_availability(mock_api_config):
    """Test check_availability method."""
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
    
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Execute test
        result = await manager._check_availability(
            service_id="test_service",
            location_id="test_location"
        )
        
        # Verify result
        assert result is not None
        assert "slots" in result
        assert len(result["slots"]) == 1
        
        # Verify API call
        mock_api_config.check_availability.assert_called_once()
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_check_availability_error(mock_api_config):
    """Test error handling in check_availability method."""
    # Setup mock data
    mock_api_config.check_availability.side_effect = Exception("API error")
    
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Execute test
        result = await manager._check_availability(
            service_id="test_service",
            location_id="test_location"
        )
        
        # Verify result
        assert result is None
        
        # Verify API call
        mock_api_config.check_availability.assert_called_once()
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_matches_preferences(sample_subscription):
    """Test matches_preferences method."""
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Test with matching preferences
        slot = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "14:30",
            "location": "Test Location",
            "type": "Regular"
        }
        assert manager._matches_preferences(slot, sample_subscription["preferences"]) is True
        
        # Test with non-matching preferences
        slot["time"] = "18:00"
        assert manager._matches_preferences(slot, sample_subscription["preferences"]) is False
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_matches_preferences_outside_range(sample_subscription):
    """Test matches_preferences with time outside range."""
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Test with time outside range
        slot = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "18:00",
            "location": "Test Location",
            "type": "Regular"
        }
        assert manager._matches_preferences(slot, sample_subscription["preferences"]) is False
        
    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.asyncio
async def test_matches_preferences_invalid_date(sample_subscription):
    """Test matches_preferences with invalid date."""
    # Initialize manager
    manager = await appointment_manager
    
    try:
        # Test with invalid date
        slot = {
            "date": "invalid_date",
            "time": "14:30",
            "location": "Test Location",
            "type": "Regular"
        }
        assert manager._matches_preferences(slot, sample_subscription["preferences"]) is False
        
    finally:
        # Cleanup
        await manager.stop() 