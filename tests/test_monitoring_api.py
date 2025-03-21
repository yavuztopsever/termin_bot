"""Test monitoring API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST

def test_health_check_healthy(
    test_client: TestClient,
    mock_health_monitor,
    sample_metrics_data
):
    """Test health check endpoint when system is healthy."""
    # Setup mock
    mock_health_monitor.get_current_metrics.return_value = sample_metrics_data["healthy"]

    # Make request
    response = test_client.get("/monitoring/health")

    # Verify response
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "metrics" in response.json()

def test_health_check_degraded(
    test_client: TestClient,
    mock_health_monitor,
    sample_metrics_data
):
    """Test health check endpoint when system is degraded."""
    # Modify metrics to show degraded state
    mock_health_monitor.get_current_metrics.return_value = sample_metrics_data["warning"]

    # Make request
    response = test_client.get("/monitoring/health")

    # Verify response
    assert response.status_code == 200
    assert "metrics" in response.json()

def test_metrics_endpoint(test_client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = test_client.get("/monitoring/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST

def test_metrics_history(
    test_client: TestClient,
    mock_health_monitor,
    sample_metrics_data
):
    """Test metrics history endpoint."""
    # Create sample history data
    now = datetime.utcnow()
    history = [
        sample_metrics_data["healthy"]
        for _ in range(5)
    ]
    mock_health_monitor.get_metrics_history.return_value = history

    # Make request
    response = test_client.get("/monitoring/metrics/history")

    # Verify response
    assert response.status_code == 200
    assert "history" in response.json()
    assert len(response.json()["history"]) == 5

def test_detailed_status(
    test_client: TestClient,
    mock_health_monitor,
    mock_db,
    sample_metrics_data
):
    """Test detailed status endpoint."""
    # Setup mocks
    mock_health_monitor.get_detailed_status.return_value = {
        "metrics": sample_metrics_data["healthy"],
        "warnings": [],
        "system_info": {
            "total_users": 10,
            "active_subscriptions": 5,
            "total_appointments": 20
        }
    }

    # Make request
    response = test_client.get("/monitoring/status/detailed")

    # Verify response
    assert response.status_code == 200
    assert "metrics" in response.json()
    assert "warnings" in response.json()
    assert "system_info" in response.json()

def test_detailed_status_error_handling(
    test_client: TestClient,
    mock_health_monitor,
    mock_db
):
    """Test detailed status endpoint error handling."""
    # Setup mock to raise exception
    mock_health_monitor.get_detailed_status.side_effect = Exception("Test error")

    # Make request
    response = test_client.get("/monitoring/status/detailed")

    # Verify response
    assert response.status_code == 500
    assert "detail" in response.json()

def test_metrics_endpoint_content(test_client: TestClient):
    """Test Prometheus metrics endpoint content."""
    response = test_client.get("/monitoring/metrics")

    assert response.status_code == 200
    content = response.text

    # Check for expected metric types
    assert "# HELP" in content
    assert "# TYPE" in content

    # Check for specific metrics
    expected_metrics = [
        "mta_request_latency_seconds",
        "mta_request_total",
        "mta_appointment_checks_total",
        "mta_appointments_found_total",
        "mta_appointments_booked_total",
        "mta_active_tasks",
        "mta_cpu_usage_percent",
        "mta_memory_usage_percent",
        "mta_rate_limit_remaining",
        "mta_errors_total",
        "mta_function_latency_seconds",
        "mta_queue_size",
        "mta_queue_latency_seconds"
    ]

    for metric in expected_metrics:
        assert metric in content 