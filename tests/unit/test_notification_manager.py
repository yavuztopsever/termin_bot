"""Unit tests for notification manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
from datetime import datetime, timedelta

from src.manager.notification_manager import NotificationManager
from src.config.config import NOTIFICATION_CONFIG

class TestNotificationManager:
    """Tests for NotificationManager class."""
    
    @pytest.fixture
    def notification_manager(self):
        """Create a notification manager instance for testing."""
        return NotificationManager()
        
    @pytest.fixture
    def mock_telegram_bot(self):
        """Mock the Telegram bot."""
        with patch('src.manager.notification_manager.Application') as mock:
            mock.builder.return_value.token.return_value.build.return_value = MagicMock()
            mock.builder.return_value.token.return_value.build.return_value.bot = MagicMock()
            mock.builder.return_value.token.return_value.build.return_value.bot.send_message = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_user_repository(self):
        """Mock the user repository."""
        with patch('src.manager.notification_manager.user_repository') as mock:
            mock.find_by_id = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_notification_repository(self):
        """Mock the notification repository."""
        with patch('src.manager.notification_manager.notification_repository') as mock:
            mock.create = AsyncMock()
            mock.find_by_user_id = AsyncMock()
            mock.update = AsyncMock()
            yield mock
            
    @pytest.fixture
    def mock_metrics(self):
        """Mock the metrics collector."""
        with patch('src.manager.notification_manager.metrics') as mock:
            mock.increment = MagicMock()
            yield mock
            
    @pytest.mark.asyncio
    async def test_initialize_and_close(self, notification_manager, mock_telegram_bot):
        """Test initialize and close methods."""
        # Initialize
        await notification_manager.initialize()
        assert notification_manager.application is not None
        
        # Close
        await notification_manager.close()
        notification_manager.application.shutdown.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_notify_user_success(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user with successful notification."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="test",
            content={"title": "Test", "message": "Test message"},
            buttons=[
                [
                    {"text": "Button 1", "callback_data": "button1"},
                    {"text": "Button 2", "callback_data": "button2"}
                ]
            ]
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_test")
        
    @pytest.mark.asyncio
    async def test_notify_user_disabled(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user with disabled notifications."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": False
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="test",
            content={"title": "Test", "message": "Test message"}
        )
        
        # Assertions
        assert success is False
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_not_called()
        mock_notification_repository.create.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_notify_user_filtered_by_preference(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user filtered by user preferences."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "booked_only",
                "notification_types": ["appointment_booked", "booking_reminder"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="appointment_found",
            content={"title": "Test", "message": "Test message"}
        )
        
        # Assertions
        assert success is False
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_not_called()
        mock_notification_repository.create.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_notify_user_high_priority_bypass(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user with high priority bypassing filters."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "booked_only",
                "notification_types": ["appointment_booked", "booking_reminder"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="appointment_found",
            content={"title": "Test", "message": "Test message"},
            priority="high"
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_notify_user_cooldown(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user with cooldown period."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Set cooldown
        notification_manager.cooldown_users["123:test"] = datetime.utcnow() + timedelta(minutes=5)
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="test",
            content={"title": "Test", "message": "Test message"}
        )
        
        # Assertions
        assert success is False
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_not_called()
        mock_notification_repository.create.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_notify_user_exception(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test notify_user with exception."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        notification_manager.application.bot.send_message.side_effect = Exception("Test error")
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.notify_user(
            user_id=123,
            notification_type="test",
            content={"title": "Test", "message": "Test message"}
        )
        
        # Assertions
        assert success is False
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_called_with("notification_errors")
        
    @pytest.mark.asyncio
    async def test_format_message(self, notification_manager):
        """Test _format_message method."""
        # Initialize notification manager
        notification_manager.initialize()
        
        # Test appointment found format
        content = {
            "service_id": "service1",
            "location_id": "location1",
            "date": "2025-04-01",
            "time": "10:00",
            "parallel_attempts": 3
        }
        message = notification_manager._format_message("appointment_found", content)
        assert "Found an available appointment" in message
        assert "service1" in message
        assert "location1" in message
        assert "2025-04-01" in message
        assert "10:00" in message
        assert "multiple slots" in message
        
        # Test appointment booked format
        content = {
            "service_id": "service1",
            "location_id": "location1",
            "date": "2025-04-01",
            "time": "10:00",
            "booking_id": "booking123",
            "instructions": "Bring your ID"
        }
        message = notification_manager._format_message("appointment_booked", content)
        assert "Successfully booked an appointment" in message
        assert "service1" in message
        assert "location1" in message
        assert "2025-04-01" in message
        assert "10:00" in message
        assert "booking123" in message
        assert "Bring your ID" in message
        
        # Test booking failed format
        content = {
            "service_id": "service1",
            "location_id": "location1",
            "date": "2025-04-01",
            "time": "10:00",
            "reason": "Slot already taken"
        }
        message = notification_manager._format_message("booking_failed", content)
        assert "Booking attempt failed" in message
        assert "service1" in message
        assert "location1" in message
        assert "2025-04-01" in message
        assert "10:00" in message
        assert "Slot already taken" in message
        
        # Test booking reminder format
        content = {
            "service_id": "service1",
            "location_id": "location1",
            "date": "2025-04-01",
            "time": "10:00",
            "booking_id": "booking123",
            "days_left": 1
        }
        message = notification_manager._format_message("booking_reminder", content)
        assert "Appointment Reminder" in message
        assert "service1" in message
        assert "location1" in message
        assert "2025-04-01" in message
        assert "10:00" in message
        assert "booking123" in message
        assert "tomorrow" in message
        
    @pytest.mark.asyncio
    async def test_send_appointment_found_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_appointment_found_notification method."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_appointment_found_notification(
            user_id=123,
            appointment_details={
                "service_id": "service1",
                "location_id": "location1",
                "date": "2025-04-01",
                "time": "10:00",
                "parallel_attempts": 3
            }
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_appointment_booked_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_appointment_booked_notification method."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_appointment_booked_notification(
            user_id=123,
            booking_details={
                "service_id": "service1",
                "location_id": "location1",
                "date": "2025-04-01",
                "time": "10:00",
                "booking_id": "booking123"
            }
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_booking_failed_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_booking_failed_notification method."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_booking_failed_notification(
            user_id=123,
            booking_details={
                "service_id": "service1",
                "location_id": "location1",
                "date": "2025-04-01",
                "time": "10:00",
                "reason": "Slot already taken"
            }
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_booking_reminder_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_booking_reminder_notification method."""
        # Setup mocks
        user = {
            "id": 123,
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_booking_reminder_notification(
            user_id=123,
            booking_details={
                "service_id": "service1",
                "location_id": "location1",
                "date": "2025-04-01",
                "time": "10:00",
                "booking_id": "booking123",
                "days_left": 1
            }
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_daily_digest(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_daily_digest method."""
        # Setup mocks
        notifications = [
            MagicMock(
                id=1,
                type="appointment_found",
                status="pending",
                content={
                    "service_id": "service1",
                    "location_id": "location1",
                    "date": "2025-04-01",
                    "time": "10:00"
                }
            ),
            MagicMock(
                id=2,
                type="booking_failed",
                status="pending",
                content={
                    "service_id": "service2",
                    "location_id": "location2",
                    "date": "2025-04-02",
                    "time": "11:00"
                }
            ),
            MagicMock(
                id=3,
                type="booking_reminder",
                status="pending",
                content={
                    "service_id": "service3",
                    "location_id": "location3",
                    "date": "2025-04-03",
                    "time": "12:00"
                }
            )
        ]
        mock_notification_repository.find_by_user_id.return_value = notifications
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_daily_digest(user_id=123)
        
        # Assertions
        assert success is True
        mock_notification_repository.find_by_user_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        assert mock_notification_repository.update.call_count == 3
        mock_metrics.increment.assert_called_with("digest_sent")
        
    @pytest.mark.asyncio
    async def test_send_daily_digest_no_pending(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_notification_repository,
        mock_metrics
    ):
        """Test send_daily_digest with no pending notifications."""
        # Setup mocks
        notifications = [
            MagicMock(
                id=1,
                type="appointment_found",
                status="sent",
                content={
                    "service_id": "service1",
                    "location_id": "location1",
                    "date": "2025-04-01",
                    "time": "10:00"
                }
            )
        ]
        mock_notification_repository.find_by_user_id.return_value = notifications
        
        # Initialize notification manager
        await notification_manager.initialize()
        
        # Call method
        success = await notification_manager.send_daily_digest(user_id=123)
        
        # Assertions
        assert success is False
        mock_notification_repository.find_by_user_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_not_called()
        mock_notification_repository.update.assert_not_called()
