"""Integration tests for metrics collection in real-world scenarios."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, AsyncMock, MagicMock

from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.manager.tasks import task_manager
from src.monitoring.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_metrics_during_booking_flow(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test metrics collection during the booking flow."""
    # Initialize managers
    await booking_manager.initialize()
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
            }
        ]
        
        # Mock API to simulate successful booking
        mock_api_config.book_appointment.return_value = {
            "success": True,
            "booking_id": "booking123"
        }
        
        # Capture initial metrics
        initial_metrics = metrics.get_all_metrics()
        
        # Attempt booking
        success, details = await booking_manager.book_appointment_parallel(
            service_id="test_service",
            location_id="test_location",
            slots=slots,
            user_id=user_id,
            subscription_id=subscription_id
        )
        
        # Verify booking success
        assert success is True
        
        # Capture final metrics
        final_metrics = metrics.get_all_metrics()
        
        # Verify metrics were updated
        assert final_metrics["counters"]["successful_bookings"] > initial_metrics["counters"]["successful_bookings"]
        assert final_metrics["counters"]["total_bookings"] > initial_metrics["counters"]["total_bookings"]
        
        # Verify booking attempt was recorded
        booking_attempts = metrics.get_booking_attempts()
        assert len(booking_attempts) > 0
        assert booking_attempts[0]["status"] == "success"
        
    finally:
        # Close managers
        await booking_manager.close()
        await notification_manager.close()

@pytest.mark.asyncio
async def test_metrics_during_notification_flow(
    mongodb,
    redis_client,
    clean_db,
    mock_telegram_bot
):
    """Test metrics collection during the notification flow."""
    # Initialize managers
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
        
        # Capture initial metrics
        initial_metrics = metrics.get_all_metrics()
        
        # Send test notification
        appointment_details = {
            "service_id": "test_service",
            "service_name": "Residence Registration",
            "location_id": "test_location",
            "location_name": "KVR Munich",
            "date": "2025-04-01",
            "time": "10:00"
        }
        
        await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Capture final metrics
        final_metrics = metrics.get_all_metrics()
        
        # Verify metrics were updated
        assert final_metrics["counters"]["notifications_sent"] > initial_metrics["counters"]["notifications_sent"]
        assert final_metrics["counters"]["notification_type_appointment_found"] > initial_metrics["counters"].get("notification_type_appointment_found", 0)
        
        # Verify notification was recorded
        notifications = metrics.get_notifications()
        assert len(notifications) > 0
        assert notifications[0]["type"] == "appointment_found"
        
        # Simulate notification error
        mock_telegram_bot.send_message.side_effect = Exception("Test error")
        
        # Capture metrics before error
        before_error_metrics = metrics.get_all_metrics()
        
        # Send notification (should fail)
        await notification_manager.send_appointment_found_notification(
            user_id=user_id,
            appointment_details=appointment_details
        )
        
        # Capture metrics after error
        after_error_metrics = metrics.get_all_metrics()
        
        # Verify error metrics were updated
        assert after_error_metrics["counters"]["notification_errors"] > before_error_metrics["counters"]["notification_errors"]
        
    finally:
        # Close manager
        await notification_manager.close()

@pytest.mark.asyncio
async def test_metrics_during_api_requests(
    mongodb,
    redis_client,
    clean_db,
    mock_api_config
):
    """Test metrics collection during API requests."""
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Start timer for API request
    metrics.start_timer("api_request")
    
    # Mock API to simulate successful response
    mock_api_config.check_availability.return_value = {
        "slots": [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "service_id": "test_service",
                "location_id": "test_location"
            }
        ]
    }
    
    # Capture initial metrics
    initial_metrics = metrics.get_all_metrics()
    
    # Make API request
    result = await mock_api_config.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    # Stop timer
    elapsed = metrics.stop_timer("api_request")
    
    # Record API request
    metrics.record_api_request({
        "method": "GET",
        "url": "/api/available-days",
        "status_code": 200,
        "duration": elapsed,
        "service_id": "test_service",
        "location_id": "test_location"
    })
    
    # Increment request counters
    metrics.increment("total_requests")
    metrics.increment("successful_requests")
    
    # Capture final metrics
    final_metrics = metrics.get_all_metrics()
    
    # Verify metrics were updated
    assert final_metrics["counters"]["total_requests"] > initial_metrics["counters"]["total_requests"]
    assert final_metrics["counters"]["successful_requests"] > initial_metrics["counters"]["successful_requests"]
    
    # Verify API request was recorded
    api_requests = metrics.get_api_requests()
    assert len(api_requests) > 0
    assert api_requests[0]["method"] == "GET"
    assert api_requests[0]["url"] == "/api/available-days"
    
    # Verify timer recorded duration
    assert len(metrics.get_histogram("api_request_duration")) > 0
    
    # Mock API to simulate error
    mock_api_config.check_availability.side_effect = Exception("API Error")
    
    # Capture metrics before error
    before_error_metrics = metrics.get_all_metrics()
    
    # Start timer for API request
    metrics.start_timer("api_request")
    
    try:
        # Make API request (should fail)
        await mock_api_config.check_availability(
            service_id="test_service",
            location_id="test_location",
            date_from=datetime.now().date().isoformat(),
            date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
        )
    except Exception as e:
        # Stop timer
        elapsed = metrics.stop_timer("api_request")
        
        # Record API request error
        metrics.record_api_request({
            "method": "GET",
            "url": "/api/available-days",
            "status_code": 500,
            "duration": elapsed,
            "service_id": "test_service",
            "location_id": "test_location",
            "error": str(e)
        })
        
        # Record error
        metrics.record_error({
            "message": str(e),
            "source": "api_request",
            "service_id": "test_service",
            "location_id": "test_location"
        })
        
        # Increment counters
        metrics.increment("total_requests")
        metrics.increment("failed_requests")
    
    # Capture final metrics
    after_error_metrics = metrics.get_all_metrics()
    
    # Verify error metrics were updated
    assert after_error_metrics["counters"]["failed_requests"] > before_error_metrics["counters"]["failed_requests"]
    assert after_error_metrics["errors_count"] > before_error_metrics["errors_count"]

@pytest.mark.asyncio
async def test_metrics_histogram_and_gauges(
    mongodb,
    redis_client,
    clean_db
):
    """Test metrics histograms and gauges."""
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Set gauges for active tasks
    metrics.set_gauge("active_tasks", 5)
    metrics.set_gauge("active_bookings", 3)
    metrics.set_gauge("active_notifications", 2)
    
    # Verify gauges
    assert metrics.get_gauge("active_tasks") == 5
    assert metrics.get_gauge("active_bookings") == 3
    assert metrics.get_gauge("active_notifications") == 2
    
    # Observe response times
    for i in range(10):
        metrics.observe("response_time", 0.1 * (i + 1))
    
    # Verify histogram values
    response_times = metrics.get_histogram("response_time")
    assert len(response_times) == 10
    assert min(response_times) == 0.1
    assert max(response_times) == 1.0
    
    # Get histogram stats
    stats = metrics.get_histogram_stats("response_time")
    
    # Verify stats
    assert stats["min"] == 0.1
    assert stats["max"] == 1.0
    assert stats["avg"] == 0.55  # (0.1 + 0.2 + ... + 1.0) / 10
    assert stats["p50"] == 0.5  # Median
    assert stats["p90"] == 0.9  # 90th percentile
    assert stats["p95"] == 0.95  # 95th percentile
    assert stats["p99"] == 0.99  # 99th percentile

@pytest.mark.asyncio
async def test_metrics_time_series(
    mongodb,
    redis_client,
    clean_db
):
    """Test metrics time series data."""
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Record time series data
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    # Mock datetime.utcnow to return specific timestamps
    with patch('src.monitoring.metrics.datetime') as mock_datetime:
        # Record old data
        mock_datetime.utcnow.return_value = one_hour_ago
        metrics.record_time_series("active_users", 10)
        metrics.record_time_series("cpu_usage", 30.5)
        
        # Record recent data
        mock_datetime.utcnow.return_value = now
        metrics.record_time_series("active_users", 15)
        metrics.record_time_series("cpu_usage", 45.2)
        
        # Get all time series data
        active_users = metrics.get_time_series("active_users")
        cpu_usage = metrics.get_time_series("cpu_usage")
        
        # Verify time series data
        assert len(active_users) == 2
        assert active_users[0][1] == 10
        assert active_users[1][1] == 15
        
        assert len(cpu_usage) == 2
        assert cpu_usage[0][1] == 30.5
        assert cpu_usage[1][1] == 45.2
        
        # Filter by timestamp
        thirty_mins_ago = now - timedelta(minutes=30)
        recent_active_users = metrics.get_time_series("active_users", since=thirty_mins_ago)
        recent_cpu_usage = metrics.get_time_series("cpu_usage", since=thirty_mins_ago)
        
        # Verify filtered data
        assert len(recent_active_users) == 1
        assert recent_active_users[0][1] == 15
        
        assert len(recent_cpu_usage) == 1
        assert recent_cpu_usage[0][1] == 45.2

@pytest.mark.asyncio
async def test_metrics_during_error_scenarios(
    mongodb,
    redis_client,
    clean_db
):
    """Test metrics collection during error scenarios."""
    # Initialize metrics collector
    metrics = MetricsCollector()
    metrics.reset()
    
    # Record various errors
    metrics.record_error({
        "message": "API Connection Error",
        "code": "CONNECTION_ERROR",
        "source": "api_client",
        "service_id": "test_service"
    })
    
    metrics.record_error({
        "message": "Database Query Failed",
        "code": "DB_ERROR",
        "source": "repository",
        "query": "SELECT * FROM users"
    })
    
    metrics.record_error({
        "message": "Notification Failed",
        "code": "NOTIFICATION_ERROR",
        "source": "notification_manager",
        "user_id": 123
    })
    
    # Verify errors were recorded
    errors = metrics.get_errors()
    assert len(errors) == 3
    
    # Verify error details
    error_sources = [e["source"] for e in errors]
    assert "api_client" in error_sources
    assert "repository" in error_sources
    assert "notification_manager" in error_sources
    
    # Filter errors by timestamp
    recent_errors = metrics.get_errors(since=datetime.utcnow() - timedelta(minutes=5))
    assert len(recent_errors) == 3  # All errors are recent
    
    # Increment error counters
    metrics.increment("api_errors")
    metrics.increment("db_errors")
    metrics.increment("notification_errors")
    
    # Verify error counters
    assert metrics.get_counter("api_errors") == 1
    assert metrics.get_counter("db_errors") == 1
    assert metrics.get_counter("notification_errors") == 1

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
