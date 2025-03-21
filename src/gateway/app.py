"""FastAPI application setup."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.api.routes import router
from src.monitoring.metrics import metrics_collector
from src.utils.json_encoder import CustomJSONEncoder
from src.config.config import CORS_ORIGINS
from src.monitoring.api import router as monitoring_router

app = FastAPI(
    title="MTA Appointment Bot API",
    description="API for managing MTA appointment bookings",
    version="1.0.0",
    default_response_class=JSONResponse
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use custom JSON encoder
app.json_encoder = CustomJSONEncoder

# Include API routes
app.include_router(router)

# Include monitoring routes
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

@app.get("/metrics")
async def metrics():
    """Endpoint for Prometheus metrics."""
    return Response(
        content=metrics_collector.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 