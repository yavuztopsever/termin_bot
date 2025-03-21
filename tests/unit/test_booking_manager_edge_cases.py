"""Unit tests for booking manager edge cases."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
from datetime import datetime, timedelta

from src.manager.booking_manager import BookingManager, booking_manager
from src.config.config import MAX_PARALLEL_BOOKINGS, BOOKING_TIMEOUT

class TestBookingManagerEdgeCases:
    """Tests for BookingManager edge cases."""
    
    @pytest.fixture
    def mock_api_config(self):
        """Mock API config for testing."""
        with patch('src.manager.booking_manager.api_config') as mock:
            mock.book_appointment = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_notification_manager(self):
        """Mock notification manager for testing."""
        with patch('src.manager.booking_manager.notification_manager') as mock:
            mock.send_appointment_found_notification = AsyncMock()
            mock.send_appointment_booked_notification = AsyncMock()
            mock.send_booking_failed_notification = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_subscription_repository(self):
        """Mock subscription repository for testing."""
        with patch('src.manager.booking_manager.subscription_repository') as mock:
            mock.update = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_appointment_repository(self):
        """Mock appointment repository for testing."""
        with patch('src.manager.booking_manager.appointment_repository') as mock:
            mock.create = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_metrics(self):
        """Mock metrics collector for testing."""
        with patch('src.manager.booking_manager.metrics') as mock:
            mock.increment = MagicMock()
            yield mock
            
    @pytest.mark.asyncio
    async def test_empty_slots_list(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test booking with empty slots list."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Attempt booking with empty slots list
        success, details = await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=[],  # Empty slots list
            user_id=123,
            subscription_id=456
        )
        
        # Verify booking failure
        assert success is False
        assert details is None
        
        # Verify no API calls
        mock_api_config.book_appointment.assert_not_called()
        
        # Verify no notifications
        mock_notification_manager.send_appointment_found_notification.assert_not_called()
        mock_notification_manager.send_appointment_booked_notification.assert_not_called()
        mock_notification_manager.send_booking_failed_notification.assert_not_called()
        
        # Verify no subscription update
        mock_subscription_repository.update.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_max_parallel_attempts_limit(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test max parallel attempts limit."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create many slots (more than max_parallel_attempts)
        num_slots = MAX_PARALLEL_BOOKINGS * 2
        slots = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": f"{10 + i // 2:02d}:{(i % 2) * 30:02d}",
                "service_id": "test_service",
                "location_id": "test_location"
            }
            for i in range(num_slots)
        ]
        
        # Mock API to simulate all booking attempts failing
        mock_api_config.book_appointment.return_value = {
            "success": False,
            "message": "Slot already taken"
        }
        
        # Attempt booking
        await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Verify max parallel attempts limit
        assert mock_api_config.book_appointment.call_count == MAX_PARALLEL_BOOKINGS
        
    @pytest.mark.asyncio
    async def test_duplicate_booking_id_handling(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test handling of duplicate booking IDs."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create slots with duplicate booking IDs
        slots = [
            {
                "date": "2025-04-01",
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": "2025-04-01",
                "time": "10:00",  # Same date and time as first slot
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to simulate successful booking
        mock_api_config.book_appointment.return_value = {
            "success": True,
            "booking_id": "booking123"
        }
        
        # Attempt booking
        await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Verify only one booking attempt (duplicate should be skipped)
        assert mock_api_config.book_appointment.call_count == 1
        
    @pytest.mark.asyncio
    async def test_active_bookings_cleanup(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test active bookings cleanup in finally block."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create slots
        slots = [
            {
                "date": "2025-04-01",
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": "2025-04-01",
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to simulate exception
        mock_api_config.book_appointment.side_effect = Exception("Test error")
        
        # Attempt booking (should raise exception)
        with pytest.raises(Exception):
            await test_booking_manager.book_appointment_parallel(
                service_id="test_service",
                location_id="test_location",
                slots=slots,
                user_id=123,
                subscription_id=456
            )
        
        # Verify active bookings were cleaned up
        assert len(test_booking_manager.active_bookings) == 0
        
    @pytest.mark.asyncio
    async def test_exception_in_booking_task(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test exception handling in booking task."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create slots
        slots = [
            {
                "date": "2025-04-01",
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to simulate exception
        mock_api_config.book_appointment.side_effect = Exception("Test error")
        
        # Attempt booking
        success, details = await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Verify booking failure
        assert success is False
        assert details is None
        
        # Verify metrics
        mock_metrics.increment.assert_called_with("failed_bookings")
        
    @pytest.mark.asyncio
    async def test_semaphore_limiting(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test semaphore limiting concurrent API requests."""
        # Initialize booking manager with small semaphore
        test_booking_manager = BookingManager()
        test_booking_manager.semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent requests
        
        # Create many slots
        slots = [
            {
                "date": "2025-04-01",
                "time": f"{10 + i:02d}:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
            for i in range(5)
        ]
        
        # Mock API to simulate slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.5)  # Slow response
            return {"success": False, "message": "Slot already taken"}
            
        mock_api_config.book_appointment.side_effect = slow_response
        
        # Start timer
        start_time = datetime.now()
        
        # Attempt booking
        await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Verify duration (should be at least 1.0 seconds for 5 slots with 2 concurrent requests)
        # Each request takes 0.5 seconds, so 5 requests with 2 concurrent should take at least 1.0 seconds
        assert duration >= 1.0
        
    @pytest.mark.asyncio
    async def test_random_shuffle(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_metrics
    ):
        """Test random shuffling of slots."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create ordered slots
        ordered_slots = [
            {
                "date": "2025-04-01",
                "time": f"{10 + i:02d}:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
            for i in range(10)
        ]
        
        # Mock random.shuffle to capture the shuffled slots
        shuffled_slots = None
        
        def capture_shuffle(slots):
            nonlocal shuffled_slots
            shuffled_slots = slots.copy()
            
        with patch('src.manager.booking_manager.random.shuffle', side_effect=capture_shuffle):
            # Mock API to simulate all booking attempts failing
            mock_api_config.book_appointment.return_value = {
                "success": False,
                "message": "Slot already taken"
            }
            
            # Attempt booking
            await test_booking_manager.book_appointment_parallel(
                service_id="test_service",
                location_id="test_location",
                slots=ordered_slots.copy(),
                user_id=123,
                subscription_id=456
            )
            
            # Verify slots were shuffled
            assert shuffled_slots is not None
            
            # Check if the order is different (this is probabilistic, but very likely)
            times_original = [slot["time"] for slot in ordered_slots]
            times_shuffled = [slot["time"] for slot in shuffled_slots]
            assert times_original != times_shuffled
            
    @pytest.mark.asyncio
    async def test_first_completed_task_cancellation(
        self,
        mock_api_config,
        mock_notification_manager,
        mock_subscription_repository,
        mock_appointment_repository,
        mock_metrics
    ):
        """Test cancellation of pending tasks when first task completes."""
        # Initialize booking manager
        test_booking_manager = BookingManager()
        
        # Create slots
        slots = [
            {
                "date": "2025-04-01",
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": "2025-04-01",
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": "2025-04-01",
                "time": "12:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to simulate first booking succeeding, others slow
        call_count = 0
        
        async def mock_book_appointment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call succeeds immediately
                return {"success": True, "booking_id": "booking123"}
            else:
                # Other calls are slow
                await asyncio.sleep(1.0)
                return {"success": False, "message": "Slot already taken"}
                
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
        # Mock appointment repository
        mock_appointment_repository.create.return_value = MagicMock(id=789)
        
        # Attempt booking
        success, details = await test_booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=123,
            subscription_id=456
        )
        
        # Verify booking success
        assert success is True
        assert details is not None
        assert details["booking_id"] == "booking123"
        
        # Verify only first booking completed, others were cancelled
        assert call_count == 1
        
        # Verify subscription update
        mock_subscription_repository.update.assert_called_once_with(
            456,
            {"status": "completed"}
        )
        
        # Verify appointment creation
        mock_appointment_repository.create.assert_called_once()
        
        # Verify booking notification
        mock_notification_manager.send_appointment_booked_notification.assert_called_once()
