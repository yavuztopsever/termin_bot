"""Unit tests for booking manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
from datetime import datetime

from src.manager.booking_manager import BookingManager
from src.config.config import MAX_PARALLEL_BOOKINGS, BOOKING_TIMEOUT

class TestBookingManager:
    """Tests for BookingManager class."""
    
    @pytest.fixture
    def booking_manager(self):
        """Create a booking manager instance for testing."""
        return BookingManager()
        
    @pytest.fixture
    def mock_api_config(self):
        """Mock the API config."""
        with patch('src.manager.booking_manager.api_config') as mock:
            mock.book_appointment = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_appointment_repository(self):
        """Mock the appointment repository."""
        with patch('src.manager.booking_manager.appointment_repository') as mock:
            mock.create = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_subscription_repository(self):
        """Mock the subscription repository."""
        with patch('src.manager.booking_manager.subscription_repository') as mock:
            mock.update = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_notify_user(self):
        """Mock the notify user functions."""
        with patch('src.manager.booking_manager.notify_user_appointment_found', new_callable=AsyncMock) as mock_found, \
             patch('src.manager.booking_manager.notify_user_appointment_booked', new_callable=AsyncMock) as mock_booked:
            yield mock_found, mock_booked
            
    @pytest.mark.asyncio
    async def test_initialize_and_close(self, booking_manager):
        """Test initialize and close methods."""
        # Initialize
        await booking_manager.initialize()
        
        # Close
        await booking_manager.close()
        
        # No assertions needed, just checking that the methods don't raise exceptions
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_no_slots(self, booking_manager):
        """Test book_appointment_parallel with no slots."""
        # Call method with empty slots list
        success, details = await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=[],
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is False
        assert details is None
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_success(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notify_user
    ):
        """Test book_appointment_parallel with successful booking."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": True,
            "booking_id": "booking123"
        }
        
        # Setup appointment repository
        mock_appointment = MagicMock()
        mock_appointment.id = 789
        mock_appointment_repository.create.return_value = mock_appointment
        
        # Setup slots
        slots = [
            {"date": "2025-04-01", "time": "10:00"},
            {"date": "2025-04-01", "time": "11:00"},
            {"date": "2025-04-01", "time": "12:00"}
        ]
        
        # Call method
        success, details = await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is True
        assert details is not None
        assert "booking_id" in details
        assert details["booking_id"] == "booking123"
        assert "appointment_id" in details
        assert details["appointment_id"] == 789
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
        # Verify appointment creation
        mock_appointment_repository.create.assert_called_once()
        
        # Verify subscription update
        mock_subscription_repository.update.assert_called_once_with(
            456,
            {"status": "completed"}
        )
        
        # Verify notifications
        mock_found.assert_called_once()
        mock_booked.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_all_fail(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notify_user
    ):
        """Test book_appointment_parallel when all booking attempts fail."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "No slots available"
        }
        
        # Setup slots
        slots = [
            {"date": "2025-04-01", "time": "10:00"},
            {"date": "2025-04-01", "time": "11:00"}
        ]
        
        # Call method
        success, details = await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API calls
        assert mock_api_config.book_appointment.call_count == 2
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify no subscription update
        mock_subscription_repository.update.assert_not_called()
        
        # Verify notifications
        mock_found.assert_called_once()
        mock_booked.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_first_succeeds(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notify_user
    ):
        """Test book_appointment_parallel when first attempt succeeds."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response - first call succeeds, others would fail
        mock_api_config.book_appointment.side_effect = [
            {"success": True, "booking_id": "booking123"},
            {"success": False, "message": "No slots available"}
        ]
        
        # Setup appointment repository
        mock_appointment = MagicMock()
        mock_appointment.id = 789
        mock_appointment_repository.create.return_value = mock_appointment
        
        # Setup slots
        slots = [
            {"date": "2025-04-01", "time": "10:00"},
            {"date": "2025-04-01", "time": "11:00"}
        ]
        
        # Call method
        success, details = await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is True
        assert details is not None
        assert "booking_id" in details
        assert details["booking_id"] == "booking123"
        
        # Verify API calls - should only be called once since tasks are cancelled after first success
        assert mock_api_config.book_appointment.call_count >= 1
        
        # Verify appointment creation
        mock_appointment_repository.create.assert_called_once()
        
        # Verify subscription update
        mock_subscription_repository.update.assert_called_once()
        
        # Verify notifications
        mock_found.assert_called_once()
        mock_booked.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_timeout(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notify_user
    ):
        """Test book_appointment_parallel with timeout."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response to take longer than timeout
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.5)  # Longer than our test timeout
            return {"success": True, "booking_id": "booking123"}
            
        mock_api_config.book_appointment.side_effect = slow_response
        
        # Override timeout for test
        booking_manager.booking_timeout = 0.1  # Very short timeout for test
        
        # Setup slots
        slots = [
            {"date": "2025-04-01", "time": "10:00"},
            {"date": "2025-04-01", "time": "11:00"}
        ]
        
        # Call method
        success, details = await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API calls
        assert mock_api_config.book_appointment.call_count > 0
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify no subscription update
        mock_subscription_repository.update.assert_not_called()
        
        # Verify notifications
        mock_found.assert_called_once()
        mock_booked.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_respects_max_attempts(
        self, 
        booking_manager, 
        mock_api_config
    ):
        """Test book_appointment_parallel respects max_parallel_attempts."""
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "No slots available"
        }
        
        # Create more slots than max_parallel_attempts
        slots = [
            {"date": "2025-04-01", "time": f"{i:02d}:00"} 
            for i in range(booking_manager.max_parallel_attempts + 5)
        ]
        
        # Call method
        await booking_manager.book_appointment_parallel(
            service_id="service1",
            location_id="location1",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Verify API calls - should be limited to max_parallel_attempts
        assert mock_api_config.book_appointment.call_count <= booking_manager.max_parallel_attempts
        
    @pytest.mark.asyncio
    async def test_attempt_booking_success(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notify_user
    ):
        """Test _attempt_booking with successful booking."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": True,
            "booking_id": "booking123"
        }
        
        # Setup appointment repository
        mock_appointment = MagicMock()
        mock_appointment.id = 789
        mock_appointment_repository.create.return_value = mock_appointment
        
        # Setup slot
        slot = {"date": "2025-04-01", "time": "10:00"}
        
        # Call method
        success, details = await booking_manager._attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
            user_id=123,
            subscription_id=456,
            booking_id="test_booking_id"
        )
        
        # Assertions
        assert success is True
        assert details is not None
        assert "booking_id" in details
        assert details["booking_id"] == "booking123"
        assert "appointment_id" in details
        assert details["appointment_id"] == 789
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once_with(
            service_id="service1",
            office_id="location1",
            date="2025-04-01",
            time="10:00"
        )
        
        # Verify appointment creation
        mock_appointment_repository.create.assert_called_once()
        
        # Verify notification
        mock_booked.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_attempt_booking_failure(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notify_user
    ):
        """Test _attempt_booking with failed booking."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "No slots available"
        }
        
        # Setup slot
        slot = {"date": "2025-04-01", "time": "10:00"}
        
        # Call method
        success, details = await booking_manager._attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
            user_id=123,
            subscription_id=456,
            booking_id="test_booking_id"
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify no notification
        mock_booked.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_attempt_booking_exception(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notify_user
    ):
        """Test _attempt_booking with exception."""
        # Setup mocks
        mock_found, mock_booked = mock_notify_user
        
        # Setup API response to raise exception
        mock_api_config.book_appointment.side_effect = Exception("API error")
        
        # Setup slot
        slot = {"date": "2025-04-01", "time": "10:00"}
        
        # Call method
        success, details = await booking_manager._attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
            user_id=123,
            subscription_id=456,
            booking_id="test_booking_id"
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify no notification
        mock_booked.assert_not_called()
