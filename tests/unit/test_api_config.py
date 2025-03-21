"""Unit tests for the API Configuration Module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from aiohttp import ClientSession

from src.api.api_config import APIConfig
from src.models import WebsiteConfig
from src.exceptions import (
    ConfigurationError,
    RateLimitExceeded,
    APIRequestError
)

@pytest.fixture
async def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.website_config = MagicMock()
    db.website_config.find_one = AsyncMock()
    db.website_config.replace_one = AsyncMock()
    return db

@pytest.fixture
def sample_website_config():
    """Create a sample website configuration."""
    return {
        "id": 1,
        "service_id": "test_service",
        "location_id": "test_location",
        "url": "https://test.com",
        "api_endpoints": {
            "check": "/api/v1/check",
            "book": "/api/v1/book"
        }
    }

@pytest.fixture
async def api_config(mock_db, sample_website_config):
    """Create an API configuration instance."""
    with patch("src.api.api_config.db", mock_db):
        config = APIConfig()
        mock_db.get_website_config.return_value = sample_website_config
        await config.initialize()
        return config

@pytest.mark.asyncio
async def test_initialization(api_config):
    """Test API configuration initialization."""
    assert isinstance(api_config._session, ClientSession)
    assert api_config.config is not None
    assert api_config._rate_limiters != {}
    assert api_config._locks != {}
    assert api_config._refresh_task is not None

@pytest.mark.asyncio
async def test_load_config_success(mock_db, sample_website_config, api_config):
    """Test successful configuration loading."""
    db = await mock_db
    db.website_config.find_one.return_value = sample_website_config
    await api_config._load_config()
    
    assert api_config.config.service_id == sample_website_config["service_id"]
    assert api_config.config.location_id == sample_website_config["location_id"]
    assert api_config.config.base_url == sample_website_config["url"]

@pytest.mark.asyncio
async def test_load_config_not_found(mock_db, api_config):
    """Test configuration loading when no config exists."""
    db = await mock_db
    db.website_config.find_one.return_value = None
    await api_config._load_config()
    
    assert api_config.config is None

@pytest.mark.asyncio
async def test_load_config_error(mock_db, api_config):
    """Test configuration loading error."""
    db = await mock_db
    db.website_config.find_one.side_effect = Exception("Database error")
    
    with pytest.raises(ConfigurationError):
        await api_config._load_config()

@pytest.mark.asyncio
async def test_update_config_success(mock_db, sample_website_config, api_config):
    """Test successful configuration update."""
    db = await mock_db
    new_config = sample_website_config.copy()
    new_config["service_id"] = "new_service"
    
    await api_config.update_config(new_config)
    
    db.website_config.replace_one.assert_called_once_with(
        {},
        new_config,
        upsert=True
    )
    assert api_config.config.service_id == "new_service"

@pytest.mark.asyncio
async def test_update_config_invalid(api_config):
    """Test configuration update with invalid config."""
    invalid_config = {
        "service_id": "test_service"
    }
    
    with pytest.raises(ConfigurationError):
        await api_config.update_config(invalid_config)

@pytest.mark.asyncio
async def test_check_rate_limit(api_config):
    """Test rate limit checking."""
    # Test successful rate limit check
    await api_config._check_rate_limit("/api/v1/check")
    
    # Test rate limit exceeded
    api_config._rate_limiters["/api/v1/check"]["tokens"] = 0
    with pytest.raises(RateLimitExceeded):
        await api_config._check_rate_limit("/api/v1/check")

@pytest.mark.asyncio
async def test_get_check_availability_request(api_config):
    """Test constructing check availability request."""
    request = await api_config.get_check_availability_request(
        service_id="test_service",
        location_id="test_location",
        date_preferences={"date": "2024-03-20"}
    )
    
    assert request["method"] == "POST"
    assert "serviceID" in request["body"]
    assert "locationID" in request["body"]
    assert "datePreferences" in request["body"]

@pytest.mark.asyncio
async def test_get_book_appointment_request(api_config):
    """Test constructing book appointment request."""
    appointment_details = {
        "service_id": "test_service",
        "location_id": "test_location",
        "date": "2024-03-20",
        "time": "14:30"
    }
    
    request = await api_config.get_book_appointment_request(appointment_details)
    
    assert request["method"] == "POST"
    assert request["body"]["serviceID"] == "test_service"
    assert request["body"]["locationID"] == "test_location"
    assert request["body"]["date"] == "2024-03-20"
    assert request["body"]["time"] == "14:30"

def test_parse_availability_response(api_config):
    """Test parsing availability response."""
    response_data = {
        "slots": [
            {
                "date": "2024-03-20",
                "time": "14:30",
                "locationId": "test_location",
                "serviceId": "test_service"
            }
        ]
    }
    
    slots = api_config.parse_availability_response(response_data)
    
    assert len(slots) == 1
    assert slots[0]["date"] == "2024-03-20"
    assert slots[0]["time"] == "14:30"
    assert slots[0]["location_id"] == "test_location"
    assert slots[0]["service_id"] == "test_service"

def test_parse_booking_response_success(api_config):
    """Test parsing successful booking response."""
    response_data = {
        "success": True,
        "bookingId": "12345",
        "message": "Booking successful"
    }
    
    result = api_config.parse_booking_response(response_data)
    
    assert result["success"] is True
    assert result["booking_id"] == "12345"
    assert result["message"] == "Booking successful"

def test_parse_booking_response_failure(api_config):
    """Test parsing failed booking response."""
    response_data = {
        "success": False,
        "message": "Booking failed"
    }
    
    result = api_config.parse_booking_response(response_data)
    
    assert result["success"] is False
    assert result["message"] == "Booking failed"

@pytest.mark.asyncio
async def test_cleanup(api_config):
    """Test cleanup of resources."""
    await api_config.close()
    assert api_config._refresh_task.cancelled()
    # Note: We can't easily test if the session is closed as it's managed by aiohttp 