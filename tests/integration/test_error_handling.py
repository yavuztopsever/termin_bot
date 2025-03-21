"""Integration tests for error handling and recovery."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, AsyncMock, MagicMock

from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.manager.tasks import task_manager
from src.monitoring.metrics import MetricsCollector
from src.utils.retry import async_retry, RetryConfig

@pytest.mark.asyncio
async def test_api_error_recovery(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test recovery from API errors."""
    # Initialize managers
    await booking_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active"
        }
        subscription_result = await mongodb.subscriptions.insert_one(subscription_data)
        subscription_id = str(subscription_result.inserted_id)
        
        # Create slots
        slots = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to fail first, then succeed
        call_count = 0
        
        async def mock_book_appointment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails with connection error
                raise ConnectionError("API Connection Error")
            else:
                # Subsequent calls succeed
                return {
                    "success": True,
                    "booking_id": "booking123"
                }
                
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
        # Define a function with retry
        @async_retry(
            retry_config=RetryConfig(
                max_retries=3,
                retry_delay=0.1,
                backoff_factor=2,
                exceptions=(ConnectionError,)
            )
        )
        async def book_with_retry():
            return await mock_api_config.book_appointment(
                service_id="test_service",
                office_id="test_location",
                date=slots[0]["date"],
                time=slots[0]["time"]
            )
            
        # Attempt booking with retry
        result = await book_with_retry()
        
        # Verify booking success after retry
        assert result["success"] is True
        assert result["booking_id"] == "booking123"
        
        # Verify API was called multiple times
        assert call_count == 2
        
    finally:
        # Close manager
        await booking_manager.close()

@pytest.mark.asyncio
async def test_database_error_recovery(
    mongodb,
    redis_client,
    clean_db
):
    """Test recovery from database errors."""
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Mock repository with database errors
    with patch('src.database.repository.Repository.find_by_id') as mock_find:
        # Set up mock to fail first, then succeed
        call_count = 0
        
        async def mock_find_by_id(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails with database error
                raise Exception("Database Connection Error")
            else:
                # Subsequent calls succeed
                return {"id": args[1], "name": "Test Item"}
                
        mock_find.side_effect = mock_find_by_id
        
        # Define a function with retry
        @async_retry(
            retry_config=RetryConfig(
                max_retries=3,
                retry_delay=0.1,
                backoff_factor=2,
                exceptions=(Exception,)
            )
        )
        async def find_with_retry(repo, item_id):
            return await repo.find_by_id(item_id)
            
        # Create a mock repository
        mock_repo = MagicMock()
        mock_repo.find_by_id = mock_find
        
        # Attempt database operation with retry
        result = await find_with_retry(mock_repo, 123)
        
        # Verify operation success after retry
        assert result["id"] == 123
        assert result["name"] == "Test Item"
        
        # Verify repository method was called multiple times
        assert call_count == 2

@pytest.mark.asyncio
async def test_notification_error_recovery(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test recovery from notification errors."""
    # Initialize notification manager
    await notification_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Set up mock to fail first, then succeed
        call_count = 0
        
        async def mock_send_message(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails with Telegram API error
                raise Exception("Telegram API Error")
            else:
                # Subsequent calls succeed
                return MagicMock()
                
        mock_telegram_bot.send_message.side_effect = mock_send_message
        
        # Define a function with retry
        @async_retry(
            retry_config=RetryConfig(
                max_retries=3,
                retry_delay=0.1,
                backoff_factor=2,
                exceptions=(Exception,)
            )
        )
        async def send_notification_with_retry():
            return await notification_manager.send_appointment_found_notification(
                user_id=user_id,
                appointment_details={
                    "service_id": "test_service",
                    "service_name": "Residence Registration",
                    "location_id": "test_location",
                    "location_name": "KVR Munich",
                    "date": "2025-04-01",
                    "time": "10:00"
                }
            )
            
        # Attempt notification with retry
        success = await send_notification_with_retry()
        
        # Verify notification success after retry
        assert success is True
        
        # Verify send_message was called multiple times
        assert call_count == 2
        
    finally:
        # Close manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_task_error_recovery(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test recovery from task execution errors."""
    # Initialize managers
    await task_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active"
        }
        await mongodb.subscriptions.insert_one(subscription_data)
        
        # Set up mock to fail first, then succeed
        call_count = 0
        
        async def mock_check_availability(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails with API error
                raise Exception("API Error")
            else:
                # Subsequent calls succeed
                return {
                    "slots": [
                        {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": "10:00",
                            "service_id": "test_service",
                            "location_id": "test_location"
                        }
                    ]
                }
                
        mock_api_config.check_availability.side_effect = mock_check_availability
        
        # Execute task first time (should fail but handle error)
        await task_manager.check_appointments()
        
        # Verify error was logged
        error_logs = await mongodb.error_logs.find({}).to_list(length=None)
        assert len(error_logs) > 0
        assert any("API Error" in log.get("message", "") for log in error_logs)
        
        # Execute task second time (should succeed)
        await task_manager.check_appointments()
        
        # Verify API was called multiple times
        assert call_count == 2
        
    finally:
        # Close manager
        await task_manager.close()

@pytest.mark.asyncio
async def test_retry_with_backoff(
    mongodb,
    redis_client,
    clean_db
):
    """Test retry with exponential backoff."""
    # Mock function that fails multiple times
    call_times = []
    
    async def failing_function():
        call_times.append(datetime.now())
        raise Exception("Test error")
        
    # Create retry config with backoff
    retry_config = RetryConfig(
        max_retries=3,
        retry_delay=0.1,
        backoff_factor=2,
        exceptions=(Exception,)
    )
    
    # Apply retry decorator
    retrying_function = async_retry(retry_config=retry_config)(failing_function)
    
    # Call function (should retry 3 times and then fail)
    start_time = datetime.now()
    
    with pytest.raises(Exception):
        await retrying_function()
        
    # Verify function was called 4 times (initial + 3 retries)
    assert len(call_times) == 4
    
    # Verify backoff delays
    # First retry: 0.1s
    # Second retry: 0.1s * 2 = 0.2s
    # Third retry: 0.2s * 2 = 0.4s
    # Total expected delay: 0.1 + 0.2 + 0.4 = 0.7s
    delay1 = (call_times[1] - call_times[0]).total_seconds()
    delay2 = (call_times[2] - call_times[1]).total_seconds()
    delay3 = (call_times[3] - call_times[2]).total_seconds()
    
    # Allow some margin for timing inaccuracies
    assert delay1 >= 0.08  # ~0.1s
    assert delay2 >= 0.15  # ~0.2s
    assert delay3 >= 0.35  # ~0.4s
    
    # Verify total delay
    total_delay = (call_times[3] - call_times[0]).total_seconds()
    assert total_delay >= 0.6  # ~0.7s

@pytest.mark.asyncio
async def test_concurrent_error_handling(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test handling of errors in concurrent operations."""
    # Initialize booking manager
    await booking_manager.initialize()
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    try:
        # Create test user
        user_id = 123456789
        user_data = {
            "telegram_id": str(user_id),
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "settings": {
                "notifications_enabled": True,
                "notification_frequency": "immediate",
                "notification_types": ["all"]
            }
        }
        user_result = await mongodb.users.insert_one(user_data)
        
        # Create test subscription
        subscription_data = {
            "user_id": str(user_result.inserted_id),
            "service_id": "test_service",
            "location_id": "test_location",
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active"
        }
        subscription_result = await mongodb.subscriptions.insert_one(subscription_data)
        subscription_id = str(subscription_result.inserted_id)
        
        # Create slots
        slots = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "11:00",
                "service_id": "test_service",
                "location_id": "test_location"
            },
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "12:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
        
        # Mock API to simulate mixed results
        call_count = 0
        
        async def mock_book_appointment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails with error
                raise Exception("API Error")
            elif call_count == 2:
                # Second call fails with slot taken
                return {
                    "success": False,
                    "message": "Slot already taken"
                }
            else:
                # Third call succeeds
                return {
                    "success": True,
                    "booking_id": "booking123"
                }
                
        mock_api_config.book_appointment.side_effect = mock_book_appointment
        
        # Attempt parallel booking
        success, details = await booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=user_id,
            subscription_id=subscription_id
        )
        
        # Verify booking success despite some errors
        assert success is True
        assert details is not None
        assert details["booking_id"] == "booking123"
        
        # Verify all slots were attempted
        assert call_count == 3
        
        # Verify metrics
        booking_metrics = metrics.get_all_metrics()
        assert booking_metrics["counters"]["successful_bookings"] >= 1
        
    finally:
        # Close manager
        await booking_manager.close()

@pytest.fixture
def mock_api_config():
    """Mock API config for testing."""
    with patch('src.api.api_config.api_config') as mock:
        mock.check_availability = AsyncMock()
        mock.book_appointment = AsyncMock()
        yield mock

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    with patch('src.manager.notification_manager.Application') as mock:
        mock.builder.return_value.token.return_value.build.return_value = MagicMock()
        mock.builder.return_value.token.return_value.build.return_value.bot = MagicMock()
        mock.builder.return_value.token.return_value.build.return_value.bot.send_message = AsyncMock()
        mock.builder.return_value.token.return_value.build.return_value.shutdown = AsyncMock()
        yield mock.builder.return_value.token.return_value.build.return_value.bot
