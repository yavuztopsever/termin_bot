"""Tests for Celery tasks."""

import pytest
import time
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from src.manager.tasks import (
    check_appointments,
    _handle_available_slots,
    _book_appointment,
    _check_availability,
    _matches_preferences,
    _send_request
)

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
async def test_check_appointments(mock_db, mock_celery, mock_metrics):
    """Test check_appointments task."""
    # Setup mock data
    mock_db.subscriptions.find.return_value = [{"user_id": "123", "active": True}]
    mock_celery.send_task.return_value = MagicMock()
    
    # Execute task
    await check_appointments()
    
    # Verify metrics were updated
    mock_metrics.increment.assert_called_with("appointments_checked")

@pytest.mark.asyncio
async def test_handle_available_slots(
    mock_db,
    mock_celery,
    mock_metrics,
    sample_slot,
    sample_subscription
):
    """Test handle_available_slots function."""
    # Setup mock data
    mock_db.subscriptions.find_one.return_value = sample_subscription
    mock_celery.send_task.return_value = MagicMock()
    
    # Execute function
    await _handle_available_slots([sample_slot])
    
    # Verify metrics were updated
    mock_metrics.increment.assert_called_with("slots_processed")

@pytest.mark.asyncio
async def test_book_appointment(
    mock_db,
    mock_metrics,
    sample_slot,
    sample_subscription
):
    """Test book_appointment function."""
    # Setup mock data
    mock_db.appointments.insert_one.return_value = MagicMock()
    
    # Execute function
    result = await _book_appointment(sample_slot, sample_subscription)
    
    # Verify result and metrics
    assert result is True
    mock_metrics.increment.assert_called_with("appointments_booked")

@pytest.mark.asyncio
async def test_check_availability(mock_metrics):
    """Test check_availability function."""
    # Setup mock response
    mock_response = {
        "slots": [
            {
                "date": datetime.utcnow().date().isoformat(),
                "time": "14:30",
                "location": "Test Location",
                "available": True
            }
        ]
    }
    
    with patch("src.manager.tasks._send_request", return_value=mock_response):
        result = await _check_availability()
        assert len(result) > 0
        mock_metrics.increment.assert_called_with("availability_checks")

def test_matches_preferences(sample_slot, sample_subscription):
    """Test matches_preferences function."""
    # Test with matching preferences
    assert _matches_preferences(sample_slot, sample_subscription["preferences"]) is True
    
    # Test with non-matching preferences
    non_matching_slot = sample_slot.copy()
    non_matching_slot["location"] = "Different Location"
    assert _matches_preferences(non_matching_slot, sample_subscription["preferences"]) is False

@pytest.mark.asyncio
async def test_send_request_with_retry(mock_metrics):
    """Test send_request function with retry logic."""
    # Mock successful request
    mock_response = {"status": "success"}
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_get.return_value.__aenter__.return_value.status = 200
        
        result = await _send_request("test_url")
        assert result == mock_response
        mock_metrics.increment.assert_called_with("requests_sent")
        
    # Test retry logic
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.side_effect = [Exception("Test error"), Exception("Test error"), mock_response]
        
        result = await _send_request("test_url", max_retries=3)
        assert result == mock_response
        assert mock_get.call_count == 3
        mock_metrics.increment.assert_has_calls([
            call("request_retries"),
            call("request_retries"),
            call("requests_sent")
        ])

@pytest.mark.asyncio
async def test_check_appointments_error_handling(mock_db, mock_metrics):
    """Test error handling in check_appointments task."""
    # Setup mock to raise exception
    mock_db.subscriptions.find.side_effect = Exception("Test error")
    
    # Execute task and verify error handling
    await check_appointments()
    mock_metrics.increment.assert_called_with("task_errors")

@pytest.mark.asyncio
async def test_book_appointment_rate_limit(
    mock_metrics,
    sample_slot,
    sample_subscription
):
    """Test rate limiting in book_appointment function."""
    # Mock rate limit exceeded
    with patch("src.manager.tasks._send_request", side_effect=Exception("Rate limit exceeded")):
        result = await _book_appointment(sample_slot, sample_subscription)
        assert result is False
        mock_metrics.increment.assert_called_with("rate_limit_exceeded") 