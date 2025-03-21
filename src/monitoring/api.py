"""Monitoring API endpoints."""

from fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import Response
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram
)

from src.monitoring.health_check import health_monitor
from src.utils.logger import logger

# Create FastAPI app
app = FastAPI(title="Monitoring API", description="API for monitoring system health and metrics")

# Create router
router = APIRouter()

# Include router in app
app.include_router(router)

# Define Prometheus metrics
REQUEST_LATENCY = Histogram(
    'mta_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)
REQUEST_COUNT = Counter(
    'mta_request_total',
    'Total requests',
    ['endpoint', 'status']
)
APPOINTMENT_CHECKS = Counter(
    'mta_appointment_checks_total',
    'Total appointment availability checks'
)
APPOINTMENTS_FOUND = Counter(
    'mta_appointments_found_total',
    'Total appointments found'
)
APPOINTMENTS_BOOKED = Counter(
    'mta_appointments_booked_total',
    'Total appointments booked'
)
ACTIVE_TASKS = Gauge(
    'mta_active_tasks',
    'Number of active tasks'
)
CPU_USAGE = Gauge(
    'mta_cpu_usage_percent',
    'CPU usage percentage'
)
MEMORY_USAGE = Gauge(
    'mta_memory_usage_percent',
    'Memory usage percentage'
)
RATE_LIMIT_REMAINING = Gauge(
    'mta_rate_limit_remaining',
    'Remaining rate limit',
    ['endpoint']
)
ERROR_COUNT = Counter(
    'mta_errors_total',
    'Total errors',
    ['type']
)
FUNCTION_LATENCY = Histogram(
    'mta_function_latency_seconds',
    'Function execution time in seconds',
    ['function']
)
QUEUE_SIZE = Gauge(
    'mta_queue_size',
    'Current queue size',
    ['queue']
)
QUEUE_LATENCY = Histogram(
    'mta_queue_latency_seconds',
    'Time spent in queue',
    ['queue']
)

@router.get("/health")
async def health_check():
    """Check system health."""
    try:
        metrics = await health_monitor.get_current_metrics()
        if not metrics:
            raise HTTPException(status_code=500, detail="Health check failed")

        # Update Prometheus metrics
        CPU_USAGE.set(metrics.cpu_usage)
        MEMORY_USAGE.set(metrics.memory_usage)
        ACTIVE_TASKS.set(metrics.active_tasks)

        return {"status": "healthy", "metrics": metrics}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/metrics")
async def metrics():
    """Get Prometheus metrics."""
    try:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/metrics/history")
async def metrics_history():
    """Get metrics history."""
    try:
        history = await health_monitor.get_metrics_history()
        return {"history": history}
    except Exception as e:
        logger.error("Failed to get metrics history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics history")

@router.get("/status/detailed")
async def detailed_status():
    """Get detailed system status."""
    try:
        status = await health_monitor.get_detailed_status()
        return status
    except Exception as e:
        logger.error("Failed to get detailed status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get detailed status")
