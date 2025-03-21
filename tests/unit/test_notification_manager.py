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
    async def notification_manager(self):
        """Create a notification manager instance for testing."""
        manager = NotificationManager()
        await manager.initialize()
        yield manager
        await manager.close()
        
    @pytest.fixture
    def mock_telegram_bot(self):
        """Mock the Telegram bot."""
        with patch('src.manager.notification_manager.Application') as mock:
            mock_instance = MagicMock()
            mock_instance.bot = MagicMock()
            mock_instance.bot.send_message = AsyncMock()
            mock_instance.shutdown = AsyncMock()
            mock.builder.return_value.token.return_value.build.return_value = mock_instance
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
        assert notification_manager.application is not None
        assert notification_manager.application.bot is not None
        assert notification_manager.application.bot.send_message is not None
        
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
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
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
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": False
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
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
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "booked_only",
                "notification_types": ["appointment_booked", "booking_reminder"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
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
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "booked_only",
                "notification_types": ["appointment_booked", "booking_reminder"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
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
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
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
        """Test notify_user with exception handling."""
        # Setup mocks
        user = {
            "id": 123,
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        notification_manager.application.bot.send_message.side_effect = Exception("Test error")
        
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
        """Test message formatting."""
        # Test with title and message
        content = {
            "title": "Test Title",
            "message": "Test Message"
        }
        formatted = await notification_manager._format_message(content)
        assert "Test Title" in formatted
        assert "Test Message" in formatted
        
        # Test with buttons
        content = {
            "title": "Test Title",
            "message": "Test Message",
            "buttons": [
                [
                    {"text": "Button 1", "callback_data": "button1"},
                    {"text": "Button 2", "callback_data": "button2"}
                ]
            ]
        }
        formatted = await notification_manager._format_message(content)
        assert "Test Title" in formatted
        assert "Test Message" in formatted
        assert "Button 1" in formatted
        assert "Button 2" in formatted
        
    @pytest.mark.asyncio
    async def test_send_appointment_found_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending appointment found notification."""
        # Setup mocks
        user = {
            "id": 123,
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Call method
        success = await notification_manager.send_appointment_found_notification(
            user_id=123,
            service_id="test_service",
            location_id="test_location",
            date="2025-04-01",
            time="14:30"
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_appointment_found")
        
    @pytest.mark.asyncio
    async def test_send_appointment_booked_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending appointment booked notification."""
        # Setup mocks
        user = {
            "id": 123,
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Call method
        success = await notification_manager.send_appointment_booked_notification(
            user_id=123,
            service_id="test_service",
            location_id="test_location",
            date="2025-04-01",
            time="14:30",
            booking_id="test_booking_id"
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_appointment_booked")
        
    @pytest.mark.asyncio
    async def test_send_booking_failed_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending booking failed notification."""
        # Setup mocks
        user = {
            "id": 123,
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Call method
        success = await notification_manager.send_booking_failed_notification(
            user_id=123,
            service_id="test_service",
            location_id="test_location",
            error_message="Test error"
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_booking_failed")
        
    @pytest.mark.asyncio
    async def test_send_booking_reminder_notification(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_user_repository,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending booking reminder notification."""
        # Setup mocks
        user = {
            "id": 123,
            "chat_id": "987654321",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        mock_user_repository.find_by_id.return_value = user
        
        # Call method
        success = await notification_manager.send_booking_reminder_notification(
            user_id=123,
            service_id="test_service",
            location_id="test_location",
            date="2025-04-01",
            time="14:30"
        )
        
        # Assertions
        assert success is True
        mock_user_repository.find_by_id.assert_called_once_with(123)
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.create.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_booking_reminder")
        
    @pytest.mark.asyncio
    async def test_send_daily_digest(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending daily digest notification."""
        # Setup mocks
        mock_notification_repository.find_by_user_id.return_value = [
            {
                "id": 1,
                "user_id": 123,
                "type": "appointment_found",
                "content": {
                    "service_id": "test_service",
                    "location_id": "test_location",
                    "date": "2025-04-01",
                    "time": "14:30"
                },
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Call method
        success = await notification_manager.send_daily_digest(user_id=123)
        
        # Assertions
        assert success is True
        notification_manager.application.bot.send_message.assert_called_once()
        mock_notification_repository.update.assert_called_once()
        mock_metrics.increment.assert_any_call("notifications_sent")
        mock_metrics.increment.assert_any_call("notification_type_daily_digest")
        
    @pytest.mark.asyncio
    async def test_send_daily_digest_no_pending(
        self, 
        notification_manager, 
        mock_telegram_bot,
        mock_notification_repository,
        mock_metrics
    ):
        """Test sending daily digest with no pending notifications."""
        # Setup mocks
        mock_notification_repository.find_by_user_id.return_value = []
        
        # Call method
        success = await notification_manager.send_daily_digest(user_id=123)
        
        # Assertions
        assert success is False
        notification_manager.application.bot.send_message.assert_not_called()
        mock_notification_repository.update.assert_not_called()
        mock_metrics.increment.assert_not_called()
