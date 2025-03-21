"""Unit tests for metrics collector."""

import pytest
from unittest.mock import patch, MagicMock
import time
from datetime import datetime, timedelta

from src.monitoring.metrics import MetricsCollector

class TestMetricsCollector:
    """Tests for MetricsCollector class."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create a metrics collector instance for testing."""
        # Reset the singleton instance for each test
        MetricsCollector._instance = None
        return MetricsCollector()
        
    def test_singleton(self):
        """Test that MetricsCollector is a singleton."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        assert collector1 is collector2
        
    def test_increment(self, metrics_collector):
        """Test increment method."""
        # Increment a counter
        metrics_collector.increment("test_counter")
        assert metrics_collector.get_counter("test_counter") == 1
        
        # Increment by a specific value
        metrics_collector.increment("test_counter", 5)
        assert metrics_collector.get_counter("test_counter") == 6
        
    def test_decrement(self, metrics_collector):
        """Test decrement method."""
        # Set initial value
        metrics_collector.increment("test_counter", 10)
        
        # Decrement a counter
        metrics_collector.decrement("test_counter")
        assert metrics_collector.get_counter("test_counter") == 9
        
        # Decrement by a specific value
        metrics_collector.decrement("test_counter", 5)
        assert metrics_collector.get_counter("test_counter") == 4
        
    def test_set_gauge(self, metrics_collector):
        """Test set_gauge method."""
        # Set a gauge
        metrics_collector.set_gauge("test_gauge", 42.5)
        assert metrics_collector.get_gauge("test_gauge") == 42.5
        
        # Update a gauge
        metrics_collector.set_gauge("test_gauge", 37.2)
        assert metrics_collector.get_gauge("test_gauge") == 37.2
        
    def test_observe(self, metrics_collector):
        """Test observe method."""
        # Observe values
        metrics_collector.observe("test_histogram", 1.0)
        metrics_collector.observe("test_histogram", 2.0)
        metrics_collector.observe("test_histogram", 3.0)
        
        # Check histogram values
        assert metrics_collector.get_histogram("test_histogram") == [1.0, 2.0, 3.0]
        
    def test_histogram_stats(self, metrics_collector):
        """Test get_histogram_stats method."""
        # Observe values
        metrics_collector.observe("test_histogram", 1.0)
        metrics_collector.observe("test_histogram", 2.0)
        metrics_collector.observe("test_histogram", 3.0)
        metrics_collector.observe("test_histogram", 4.0)
        metrics_collector.observe("test_histogram", 5.0)
        
        # Get histogram stats
        stats = metrics_collector.get_histogram_stats("test_histogram")
        
        # Check stats
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["avg"] == 3.0
        assert stats["p50"] == 3.0
        assert stats["p90"] == 5.0
        assert stats["p95"] == 5.0
        assert stats["p99"] == 5.0
        
    def test_timer(self, metrics_collector):
        """Test timer methods."""
        # Start a timer
        metrics_collector.start_timer("test_timer")
        
        # Wait a bit
        time.sleep(0.1)
        
        # Stop the timer
        elapsed = metrics_collector.stop_timer("test_timer")
        
        # Check elapsed time
        assert elapsed >= 0.1
        
        # Check that timer was removed
        assert "test_timer" not in metrics_collector._timers
        
        # Check that duration was recorded in histogram
        assert len(metrics_collector.get_histogram("test_timer_duration")) == 1
        
    def test_record_time_series(self, metrics_collector):
        """Test record_time_series method."""
        # Record time series data
        metrics_collector.record_time_series("test_series", 1.0)
        metrics_collector.record_time_series("test_series", 2.0)
        
        # Get time series data
        data = metrics_collector.get_time_series("test_series")
        
        # Check data
        assert len(data) == 2
        assert isinstance(data[0][0], datetime)
        assert data[0][1] == 1.0
        assert isinstance(data[1][0], datetime)
        assert data[1][1] == 2.0
        
    def test_record_error(self, metrics_collector):
        """Test record_error method."""
        # Record an error
        metrics_collector.record_error({
            "message": "Test error",
            "code": 500,
            "source": "test"
        })
        
        # Get errors
        errors = metrics_collector.get_errors()
        
        # Check errors
        assert len(errors) == 1
        assert isinstance(errors[0]["timestamp"], datetime)
        assert errors[0]["message"] == "Test error"
        assert errors[0]["code"] == 500
        assert errors[0]["source"] == "test"
        
    def test_record_api_request(self, metrics_collector):
        """Test record_api_request method."""
        # Record an API request
        metrics_collector.record_api_request({
            "method": "GET",
            "url": "/api/test",
            "status_code": 200,
            "duration": 0.1
        })
        
        # Get API requests
        requests = metrics_collector.get_api_requests()
        
        # Check requests
        assert len(requests) == 1
        assert isinstance(requests[0]["timestamp"], datetime)
        assert requests[0]["method"] == "GET"
        assert requests[0]["url"] == "/api/test"
        assert requests[0]["status_code"] == 200
        assert requests[0]["duration"] == 0.1
        
    def test_record_notification(self, metrics_collector):
        """Test record_notification method."""
        # Record a notification
        metrics_collector.record_notification({
            "user_id": 123,
            "type": "test",
            "status": "sent"
        })
        
        # Get notifications
        notifications = metrics_collector.get_notifications()
        
        # Check notifications
        assert len(notifications) == 1
        assert isinstance(notifications[0]["timestamp"], datetime)
        assert notifications[0]["user_id"] == 123
        assert notifications[0]["type"] == "test"
        assert notifications[0]["status"] == "sent"
        
    def test_record_booking_attempt(self, metrics_collector):
        """Test record_booking_attempt method."""
        # Record a booking attempt
        metrics_collector.record_booking_attempt({
            "service_id": "service1",
            "location_id": "location1",
            "date": "2025-04-01",
            "time": "10:00",
            "status": "success"
        })
        
        # Get booking attempts
        bookings = metrics_collector.get_booking_attempts()
        
        # Check bookings
        assert len(bookings) == 1
        assert isinstance(bookings[0]["timestamp"], datetime)
        assert bookings[0]["service_id"] == "service1"
        assert bookings[0]["location_id"] == "location1"
        assert bookings[0]["date"] == "2025-04-01"
        assert bookings[0]["time"] == "10:00"
        assert bookings[0]["status"] == "success"
        
    def test_get_all_metrics(self, metrics_collector):
        """Test get_all_metrics method."""
        # Set up some metrics
        metrics_collector.increment("test_counter", 5)
        metrics_collector.set_gauge("test_gauge", 42.5)
        metrics_collector.observe("test_histogram", 1.0)
        metrics_collector.observe("test_histogram", 2.0)
        metrics_collector.record_error({"message": "Test error"})
        metrics_collector.record_api_request({"url": "/api/test"})
        metrics_collector.record_notification({"user_id": 123})
        metrics_collector.record_booking_attempt({"service_id": "service1"})
        
        # Get all metrics
        metrics = metrics_collector.get_all_metrics()
        
        # Check metrics
        assert metrics["counters"]["test_counter"] == 5
        assert metrics["gauges"]["test_gauge"] == 42.5
        assert "test_histogram" in metrics["histograms"]
        assert metrics["errors_count"] == 1
        assert metrics["api_requests_count"] == 1
        assert metrics["notifications_count"] == 1
        assert metrics["booking_attempts_count"] == 1
        
    def test_reset(self, metrics_collector):
        """Test reset method."""
        # Set up some metrics
        metrics_collector.increment("test_counter", 5)
        metrics_collector.set_gauge("test_gauge", 42.5)
        metrics_collector.observe("test_histogram", 1.0)
        metrics_collector.record_error({"message": "Test error"})
        
        # Reset metrics
        metrics_collector.reset()
        
        # Check that metrics were reset
        assert metrics_collector.get_counter("test_counter") == 0
        assert metrics_collector.get_gauge("test_gauge") == 0.0
        assert metrics_collector.get_histogram("test_histogram") == []
        assert metrics_collector.get_errors() == []
        
    def test_filtering_by_timestamp(self, metrics_collector):
        """Test filtering by timestamp."""
        # Record time series data
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Mock datetime.utcnow to return specific timestamps
        with patch('src.monitoring.metrics.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = one_hour_ago
            
            # Record old data
            metrics_collector.record_time_series("test_series", 1.0)
            metrics_collector.record_error({"message": "Old error"})
            metrics_collector.record_api_request({"url": "/api/old"})
            metrics_collector.record_notification({"user_id": 123, "message": "Old"})
            metrics_collector.record_booking_attempt({"service_id": "old"})
            
            # Update mock to return current time
            mock_datetime.utcnow.return_value = now
            
            # Record new data
            metrics_collector.record_time_series("test_series", 2.0)
            metrics_collector.record_error({"message": "New error"})
            metrics_collector.record_api_request({"url": "/api/new"})
            metrics_collector.record_notification({"user_id": 123, "message": "New"})
            metrics_collector.record_booking_attempt({"service_id": "new"})
            
            # Filter by timestamp
            thirty_mins_ago = now - timedelta(minutes=30)
            
            # Get filtered data
            time_series = metrics_collector.get_time_series("test_series", since=thirty_mins_ago)
            errors = metrics_collector.get_errors(since=thirty_mins_ago)
            requests = metrics_collector.get_api_requests(since=thirty_mins_ago)
            notifications = metrics_collector.get_notifications(since=thirty_mins_ago)
            bookings = metrics_collector.get_booking_attempts(since=thirty_mins_ago)
            
            # Check filtered data
            assert len(time_series) == 1
            assert time_series[0][1] == 2.0
            
            assert len(errors) == 1
            assert errors[0]["message"] == "New error"
            
            assert len(requests) == 1
            assert requests[0]["url"] == "/api/new"
            
            assert len(notifications) == 1
            assert notifications[0]["message"] == "New"
            
            assert len(bookings) == 1
            assert bookings[0]["service_id"] == "new"
