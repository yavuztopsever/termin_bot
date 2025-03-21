"""Metrics collector for monitoring application performance."""

import time
import os
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import threading
import logging
from collections import defaultdict, deque

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MetricsCollector:
    """Collects and exposes metrics for monitoring."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one metrics collector instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        """Initialize metrics collector."""
        if self._initialized:
            return
            
        self._initialized = True
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = {}
        self._histograms = defaultdict(list)
        self._timers = {}
        
        # Store recent values for time series metrics
        self._time_series = defaultdict(lambda: deque(maxlen=1000))
        
        # Store recent errors
        self._errors = deque(maxlen=100)
        
        # Store recent API requests
        self._api_requests = deque(maxlen=1000)
        
        # Store recent notifications
        self._notifications = deque(maxlen=100)
        
        # Store recent booking attempts
        self._booking_attempts = deque(maxlen=100)
        
        # Initialize common metrics
        self._counters["total_requests"] = 0
        self._counters["successful_requests"] = 0
        self._counters["failed_requests"] = 0
        self._counters["total_bookings"] = 0
        self._counters["successful_bookings"] = 0
        self._counters["failed_bookings"] = 0
        self._counters["timeout_bookings"] = 0
        self._counters["total_notifications"] = 0
        self._counters["successful_notifications"] = 0
        self._counters["failed_notifications"] = 0
        
        # Initialize gauges
        self._gauges["active_tasks"] = 0
        self._gauges["active_bookings"] = 0
        self._gauges["active_notifications"] = 0
        
        logger.info("Initialized metrics collector")
        
    def increment(self, name: str, value: int = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by (default: 1)
        """
        with self._lock:
            self._counters[name] += value
            
    def decrement(self, name: str, value: int = 1) -> None:
        """
        Decrement a counter metric.
        
        Args:
            name: Metric name
            value: Value to decrement by (default: 1)
        """
        with self._lock:
            self._counters[name] -= value
            
    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
        """
        with self._lock:
            self._gauges[name] = value
            
    def observe(self, name: str, value: float) -> None:
        """
        Observe a value for a histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
        """
        with self._lock:
            self._histograms[name].append(value)
            # Keep only the last 1000 observations
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]
                
    def start_timer(self, name: str) -> None:
        """
        Start a timer for measuring durations.
        
        Args:
            name: Timer name
        """
        self._timers[name] = time.time()
        
    def stop_timer(self, name: str) -> Optional[float]:
        """
        Stop a timer and return the elapsed time.
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds, or None if timer not found
        """
        if name not in self._timers:
            return None
            
        elapsed = time.time() - self._timers[name]
        del self._timers[name]
        
        # Store in histogram
        self.observe(f"{name}_duration", elapsed)
        
        return elapsed
        
    def record_time_series(self, name: str, value: float) -> None:
        """
        Record a value for a time series metric.
        
        Args:
            name: Metric name
            value: Observed value
        """
        with self._lock:
            self._time_series[name].append((datetime.utcnow(), value))
            
    def record_error(self, error: Dict[str, Any]) -> None:
        """
        Record an error.
        
        Args:
            error: Error details
        """
        with self._lock:
            self._errors.append({
                "timestamp": datetime.utcnow(),
                **error
            })
            
    def record_api_request(self, request: Dict[str, Any]) -> None:
        """
        Record an API request.
        
        Args:
            request: API request details
        """
        with self._lock:
            self._api_requests.append({
                "timestamp": datetime.utcnow(),
                **request
            })
            
    def record_notification(self, notification: Dict[str, Any]) -> None:
        """
        Record a notification.
        
        Args:
            notification: Notification details
        """
        with self._lock:
            self._notifications.append({
                "timestamp": datetime.utcnow(),
                **notification
            })
            
    def record_booking_attempt(self, booking: Dict[str, Any]) -> None:
        """
        Record a booking attempt.
        
        Args:
            booking: Booking attempt details
        """
        with self._lock:
            self._booking_attempts.append({
                "timestamp": datetime.utcnow(),
                **booking
            })
            
    def get_counter(self, name: str) -> int:
        """
        Get the value of a counter metric.
        
        Args:
            name: Metric name
            
        Returns:
            Counter value
        """
        return self._counters.get(name, 0)
        
    def get_gauge(self, name: str) -> float:
        """
        Get the value of a gauge metric.
        
        Args:
            name: Metric name
            
        Returns:
            Gauge value
        """
        return self._gauges.get(name, 0.0)
        
    def get_histogram(self, name: str) -> List[float]:
        """
        Get the values of a histogram metric.
        
        Args:
            name: Metric name
            
        Returns:
            List of observed values
        """
        return self._histograms.get(name, [])
        
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a histogram metric.
        
        Args:
            name: Metric name
            
        Returns:
            Dictionary with min, max, avg, p50, p90, p95, p99 statistics
        """
        values = self.get_histogram(name)
        if not values:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        values.sort()
        return {
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / len(values),
            "p50": values[int(len(values) * 0.5)],
            "p90": values[int(len(values) * 0.9)],
            "p95": values[int(len(values) * 0.95)],
            "p99": values[int(len(values) * 0.99)]
        }
        
    def get_time_series(self, name: str, since: Optional[datetime] = None) -> List[tuple]:
        """
        Get time series data for a metric.
        
        Args:
            name: Metric name
            since: Optional timestamp to filter data
            
        Returns:
            List of (timestamp, value) tuples
        """
        data = list(self._time_series.get(name, []))
        if since:
            data = [(ts, val) for ts, val in data if ts >= since]
        return data
        
    def get_errors(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get recorded errors.
        
        Args:
            since: Optional timestamp to filter errors
            
        Returns:
            List of error records
        """
        errors = list(self._errors)
        if since:
            errors = [e for e in errors if e["timestamp"] >= since]
        return errors
        
    def get_api_requests(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get recorded API requests.
        
        Args:
            since: Optional timestamp to filter requests
            
        Returns:
            List of API request records
        """
        requests = list(self._api_requests)
        if since:
            requests = [r for r in requests if r["timestamp"] >= since]
        return requests
        
    def get_notifications(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get recorded notifications.
        
        Args:
            since: Optional timestamp to filter notifications
            
        Returns:
            List of notification records
        """
        notifications = list(self._notifications)
        if since:
            notifications = [n for n in notifications if n["timestamp"] >= since]
        return notifications
        
    def get_booking_attempts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get recorded booking attempts.
        
        Args:
            since: Optional timestamp to filter booking attempts
            
        Returns:
            List of booking attempt records
        """
        bookings = list(self._booking_attempts)
        if since:
            bookings = [b for b in bookings if b["timestamp"] >= since]
        return bookings
        
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.
        
        Returns:
            Dictionary with all metrics
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name)
                    for name in self._histograms
                },
                "errors_count": len(self._errors),
                "api_requests_count": len(self._api_requests),
                "notifications_count": len(self._notifications),
                "booking_attempts_count": len(self._booking_attempts)
            }
            
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters = defaultdict(int)
            self._gauges = {}
            self._histograms = defaultdict(list)
            self._timers = {}
            self._time_series = defaultdict(lambda: deque(maxlen=1000))
            self._errors = deque(maxlen=100)
            self._api_requests = deque(maxlen=1000)
            self._notifications = deque(maxlen=100)
            self._booking_attempts = deque(maxlen=100)

class MetricsManager(MetricsCollector):
    """Extended metrics collector with system metrics functionality."""
    
    def __init__(self):
        """Initialize metrics manager."""
        super().__init__()
        self._process = psutil.Process(os.getpid())
        self._health_metrics = {}
        
    def update_health_metrics(self, metrics):
        """
        Update health metrics from the health monitor.
        
        Args:
            metrics: Health metrics object
        """
        try:
            if hasattr(metrics, 'to_dict'):
                self._health_metrics = metrics.to_dict()
            elif isinstance(metrics, dict):
                self._health_metrics = metrics
            else:
                self._health_metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Invalid metrics format"
                }
                
            # Update gauges based on health metrics
            if isinstance(self._health_metrics, dict):
                if "cpu_usage" in self._health_metrics:
                    self.set_gauge("cpu_usage", self._health_metrics["cpu_usage"])
                if "memory_usage" in self._health_metrics:
                    self.set_gauge("memory_usage", self._health_metrics["memory_usage"])
                if "disk_usage" in self._health_metrics:
                    self.set_gauge("disk_usage", self._health_metrics["disk_usage"])
                if "request_rate" in self._health_metrics:
                    self.set_gauge("request_rate", self._health_metrics["request_rate"])
                if "error_rate" in self._health_metrics:
                    self.set_gauge("error_rate", self._health_metrics["error_rate"])
                    
        except Exception as e:
            logger.error(f"Error updating health metrics: {str(e)}")
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics including CPU, memory, and application metrics.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            # Get CPU and memory usage
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            process_cpu = self._process.cpu_percent()
            process_memory = self._process.memory_percent()
            
            # Get application metrics
            app_metrics = self.get_all_metrics()
            
            # Calculate error rate
            total_requests = self.get_counter("total_requests")
            failed_requests = self.get_counter("failed_requests")
            error_rate = (failed_requests / total_requests) if total_requests > 0 else 0
            
            # Combine metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "process_cpu": process_cpu,
                "process_memory": process_memory,
                "request_count": total_requests,
                "error_count": failed_requests,
                "error_rate": error_rate,
                "active_users": self.get_gauge("active_users"),
                "subscription_count": self.get_gauge("active_subscriptions"),
                "booking_success_rate": self.get_gauge("booking_success_rate"),
                "response_times": {
                    name: stats for name, stats in app_metrics.get("histograms", {}).items()
                    if name.endswith("_duration")
                }
            }
            
            # Add health metrics if available
            if self._health_metrics:
                metrics["health"] = self._health_metrics
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": 0,
                "memory_usage": 0,
                "error_rate": 0,
                "error": str(e)
            }

# Create the metrics manager instance
metrics_manager = MetricsManager()
metrics_collector = metrics_manager  # Alias for backward compatibility
