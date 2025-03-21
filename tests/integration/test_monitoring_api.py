"""Integration tests for the monitoring API."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi.testclient import TestClient

from src.api.app import app
from src.monitoring.metrics import MetricsManager
from src.monitoring.health_check import HealthMonitor

@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def metrics_manager():
    """Metrics manager fixture."""
    return MetricsManager()

@pytest.fixture
def health_check():
    """Health check fixture."""
    return HealthMonitor()

@pytest.mark.asyncio
async def test_health_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "components" in data
    
    # Check component statuses
    components = data["components"]
    assert "database" in components
    assert "redis" in components
    assert "api" in components
    
    # All components should be healthy
    assert all(c["status"] == "healthy" for c in components.values())

@pytest.mark.asyncio
async def test_metrics_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the metrics endpoint."""
    # Generate some test data
    await mongodb.users.insert_many([
        {
            "telegram_id": str(i),
            "username": f"test_user_{i}",
            "created_at": datetime.now()
        }
        for i in range(5)
    ])
    
    await mongodb.subscriptions.insert_many([
        {
            "user_id": str(i),
            "service_id": "test_service",
            "created_at": datetime.now()
        }
        for i in range(3)
    ])
    
    # Test metrics endpoint
    response = test_client.get("/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamp" in data
    assert "metrics" in data
    
    metrics = data["metrics"]
    assert "user_count" in metrics
    assert "active_subscriptions" in metrics
    assert "request_count" in metrics
    assert "error_rate" in metrics
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    
    # Verify metrics values
    assert metrics["user_count"] == 5
    assert metrics["active_subscriptions"] == 3
    assert metrics["error_rate"] >= 0
    assert 0 <= metrics["cpu_usage"] <= 100
    assert 0 <= metrics["memory_usage"] <= 100

@pytest.mark.asyncio
async def test_error_logs_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the error logs endpoint."""
    # Insert test error logs
    test_errors = [
        {
            "timestamp": datetime.now() - timedelta(minutes=i),
            "level": "ERROR",
            "message": f"Test error {i}",
            "component": "test",
            "details": {"error": f"Details {i}"}
        }
        for i in range(5)
    ]
    
    await mongodb.error_logs.insert_many(test_errors)
    
    # Test error logs endpoint
    response = test_client.get("/errors")
    assert response.status_code == 200
    
    data = response.json()
    assert "errors" in data
    assert len(data["errors"]) == 5
    
    # Test error logs with filters
    response = test_client.get("/errors?component=test&limit=3")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["errors"]) == 3
    assert all(e["component"] == "test" for e in data["errors"])

@pytest.mark.asyncio
async def test_system_status_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the system status endpoint."""
    response = test_client.get("/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "uptime" in data
    assert "last_check" in data
    assert "components" in data
    
    # Check component details
    components = data["components"]
    assert "bot" in components
    assert "database" in components
    assert "redis" in components
    assert "api" in components
    
    # Check component fields
    for component in components.values():
        assert "status" in component
        assert "last_check" in component
        assert "details" in component

@pytest.mark.asyncio
async def test_performance_metrics_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the performance metrics endpoint."""
    # Insert test performance data
    test_metrics = [
        {
            "timestamp": datetime.now() - timedelta(minutes=i),
            "request_count": i * 10,
            "average_response_time": 0.1 + i * 0.01,
            "error_count": i,
            "cpu_usage": 50 + i,
            "memory_usage": 60 + i
        }
        for i in range(60)  # Last hour of data
    ]
    
    await mongodb.performance_metrics.insert_many(test_metrics)
    
    # Test performance metrics endpoint
    response = test_client.get("/performance")
    assert response.status_code == 200
    
    data = response.json()
    assert "metrics" in data
    assert "period" in data
    
    metrics = data["metrics"]
    assert "request_rate" in metrics
    assert "response_time" in metrics
    assert "error_rate" in metrics
    assert "resource_usage" in metrics
    
    # Test with time range
    response = test_client.get(
        "/performance?start_time=2024-03-21T00:00:00Z&end_time=2024-03-21T23:59:59Z"
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_alerts_endpoint(
    test_client: TestClient,
    mongodb,
    redis_client,
    clean_db
):
    """Test the alerts endpoint."""
    # Insert test alerts
    test_alerts = [
        {
            "timestamp": datetime.now() - timedelta(minutes=i),
            "level": "WARNING" if i % 2 == 0 else "CRITICAL",
            "message": f"Test alert {i}",
            "component": "test",
            "resolved": i % 3 == 0
        }
        for i in range(10)
    ]
    
    await mongodb.alerts.insert_many(test_alerts)
    
    # Test alerts endpoint
    response = test_client.get("/alerts")
    assert response.status_code == 200
    
    data = response.json()
    assert "alerts" in data
    assert len(data["alerts"]) == 10
    
    # Test active alerts
    response = test_client.get("/alerts/active")
    assert response.status_code == 200
    
    data = response.json()
    active_alerts = [a for a in test_alerts if not a["resolved"]]
    assert len(data["alerts"]) == len(active_alerts)
    
    # Test alerts by level
    response = test_client.get("/alerts?level=CRITICAL")
    assert response.status_code == 200
    
    data = response.json()
    critical_alerts = [a for a in test_alerts if a["level"] == "CRITICAL"]
    assert len(data["alerts"]) == len(critical_alerts) 