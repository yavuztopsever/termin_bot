"""Tests for the monitoring API."""

import pytest
from fastapi.testclient import TestClient
from src.control.health.health_monitor import HealthMonitor
from src.data.metrics.metrics_client import MetricsClient
from src.config import settings

@pytest.fixture
def test_client():
    """Create a test client."""
    from src.control.health.health_api import app
    return TestClient(app)

def test_health_endpoint(test_client, health_monitor):
    """Test the health endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "metrics" in data
    
    metrics = data["metrics"]
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "disk_usage" in metrics
    assert "request_count" in metrics
    assert "error_count" in metrics

def test_metrics_endpoint(test_client, metrics):
    """Test the metrics endpoint."""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    
    # Verify Prometheus format
    content = response.text
    assert "# HELP" in content
    assert "# TYPE" in content
    assert "appointment_requests_total" in content
    assert "appointment_request_latency_seconds" in content
    assert "system_cpu_usage_percent" in content
    assert "system_memory_usage_bytes" in content
    assert "system_disk_usage_bytes" in content
    assert "appointments_total" in content
    assert "notifications_total" in content
    assert "errors_total" in content

def test_health_history_endpoint(test_client, health_monitor):
    """Test the health history endpoint."""
    response = test_client.get("/health/history")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    if len(data) > 0:
        assert "timestamp" in data[0]
        assert "cpu_usage" in data[0]
        assert "memory_usage" in data[0]
        assert "disk_usage" in data[0]
        assert "healthy" in data[0]

def test_health_history_limit(test_client, health_monitor):
    """Test the health history endpoint with limit."""
    limit = 5
    response = test_client.get(f"/health/history?limit={limit}")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) <= limit
    if len(data) > 0:
        assert "timestamp" in data[0]
        assert "cpu_usage" in data[0]
        assert "memory_usage" in data[0]
        assert "disk_usage" in data[0]
        assert "healthy" in data[0]

def test_metrics_reset_endpoint(test_client, metrics):
    """Test the metrics reset endpoint."""
    # Record some metrics first
    metrics.record_request("test_client", "success", "test_operation", 0.5)
    metrics.record_error("test_type", "test_component")
    
    # Reset metrics
    response = test_client.post("/metrics/reset")
    assert response.status_code == 200
    
    # Verify metrics were reset
    assert metrics.request_counter._value.get() == 0
    assert metrics.error_counter._value.get() == 0 