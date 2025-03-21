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
    async def booking_manager(self):
        """Create a booking manager instance for testing."""
        manager = BookingManager()
        await manager.initialize()
        yield manager
        await manager.close()
        
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
    def mock_notification_manager(self):
        """Mock the notification manager."""
        with patch('src.manager.booking_manager.notification_manager') as mock:
            mock.send_appointment_found_notification = AsyncMock()
            mock.send_appointment_booked_notification = AsyncMock()
            mock.send_booking_failed_notification = AsyncMock()
            yield mock
            
    @pytest.mark.asyncio
    async def test_initialize_and_close(self, booking_manager):
        """Test initialize and close methods."""
        # No assertions needed, just checking that the methods don't raise exceptions
        assert booking_manager is not None
        
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
        mock_notification_manager
    ):
        """Test book_appointment_parallel with successful booking."""
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
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_appointment_booked_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_all_fail(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notification_manager
    ):
        """Test book_appointment_parallel when all booking attempts fail."""
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
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_booking_failed_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_first_succeeds(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notification_manager
    ):
        """Test book_appointment_parallel when first attempt succeeds."""
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
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_appointment_booked_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_timeout(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_subscription_repository,
        mock_notification_manager
    ):
        """Test book_appointment_parallel with timeout."""
        # Setup API response to take longer than timeout
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(BOOKING_TIMEOUT + 1)
            return {"success": True, "booking_id": "booking123"}
            
        mock_api_config.book_appointment.side_effect = slow_response
        
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
        
        # Verify API calls were made
        assert mock_api_config.book_appointment.call_count > 0
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify no subscription update
        mock_subscription_repository.update.assert_not_called()
        
        # Verify notifications
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_booking_failed_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_book_appointment_parallel_respects_max_attempts(
        self, 
        booking_manager, 
        mock_api_config
    ):
        """Test book_appointment_parallel respects max attempts."""
        # Setup API response to always fail
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "No slots available"
        }
        
        # Setup slots - more than MAX_PARALLEL_BOOKINGS
        slots = [
            {"date": "2025-04-01", "time": f"{i:02d}:00"}
            for i in range(MAX_PARALLEL_BOOKINGS + 5)
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
        
        # Verify API calls were limited to MAX_PARALLEL_BOOKINGS
        assert mock_api_config.book_appointment.call_count == MAX_PARALLEL_BOOKINGS
        
    @pytest.mark.asyncio
    async def test_attempt_booking_success(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notification_manager
    ):
        """Test attempt_booking with successful booking."""
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
        success, details = await booking_manager.attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
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
        
        # Verify notifications
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_appointment_booked_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_attempt_booking_failure(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notification_manager
    ):
        """Test attempt_booking with failed booking."""
        # Setup API response
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "No slots available"
        }
        
        # Setup slot
        slot = {"date": "2025-04-01", "time": "10:00"}
        
        # Call method
        success, details = await booking_manager.attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify notifications
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_booking_failed_notification.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_attempt_booking_exception(
        self, 
        booking_manager, 
        mock_api_config, 
        mock_appointment_repository,
        mock_notification_manager
    ):
        """Test attempt_booking with API exception."""
        # Setup API response to raise exception
        mock_api_config.book_appointment.side_effect = Exception("API Error")
        
        # Setup slot
        slot = {"date": "2025-04-01", "time": "10:00"}
        
        # Call method
        success, details = await booking_manager.attempt_booking(
            service_id="service1",
            location_id="location1",
            slot=slot,
            user_id=123,
            subscription_id=456
        )
        
        # Assertions
        assert success is False
        assert details is None
        
        # Verify API call
        mock_api_config.book_appointment.assert_called_once()
        
        # Verify no appointment creation
        mock_appointment_repository.create.assert_not_called()
        
        # Verify notifications
        mock_notification_manager.send_appointment_found_notification.assert_called_once()
        mock_notification_manager.send_booking_failed_notification.assert_called_once()
