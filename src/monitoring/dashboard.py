from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timedelta
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pathlib import Path

from src.config.config import DASHBOARD_CONFIG
from src.utils.logger import setup_logger
from src.monitoring.exceptions import (
    DashboardError,
    DashboardInitializationError,
    DashboardConnectionError
)
from src.monitoring.metrics import metrics_manager
from src.monitoring.health import health_check
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

class DashboardManager:
    """Manager for the monitoring dashboard."""
    
    def __init__(self):
        """Initialize the dashboard manager."""
        self._initialized = False
        self._app = FastAPI()
        self._active_connections: List[WebSocket] = []
        self._templates = Jinja2Templates(directory="templates")
        
    async def initialize(self) -> None:
        """Initialize the dashboard."""
        try:
            # Mount static files
            static_path = Path(__file__).parent / "static"
            self._app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
            
            # Setup routes
            self._app.get("/", response_class=HTMLResponse)(self._dashboard_page)
            self._app.get("/api/health")(self._health_status)
            self._app.get("/api/metrics")(self._metrics_status)
            self._app.get("/api/alerts")(self._alerts_status)
            self._app.websocket("/ws")(self._websocket_endpoint)
            
            # Start background tasks
            asyncio.create_task(self._broadcast_updates())
            
            self._initialized = True
            logger.info("Dashboard initialized")
            
        except Exception as e:
            logger.error("Failed to initialize dashboard", error=str(e))
            raise DashboardInitializationError(f"Failed to initialize dashboard: {str(e)}")
            
    async def close(self) -> None:
        """Close the dashboard."""
        # Close all WebSocket connections
        for connection in self._active_connections:
            await connection.close()
        self._active_connections.clear()
        self._initialized = False
        
    async def _dashboard_page(self, request: Request) -> HTMLResponse:
        """Render the dashboard page."""
        return self._templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "System Dashboard",
                "refresh_interval": DASHBOARD_CONFIG["refresh_interval"]
            }
        )
        
    async def _health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "status": "healthy" if health_check.is_healthy() else "unhealthy",
            "components": health_check.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def _metrics_status(self) -> Dict[str, Any]:
        """Get current metrics status."""
        return {
            "metrics": metrics_manager.get_all_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def _alerts_status(self) -> Dict[str, Any]:
        """Get current alerts status."""
        return {
            "active_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level,
                    "component": alert.component,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in alert_manager.get_active_alerts()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        await websocket.accept()
        self._active_connections.append(websocket)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            self._active_connections.remove(websocket)
            
    async def _broadcast_updates(self) -> None:
        """Broadcast updates to connected clients."""
        while self._initialized:
            try:
                # Get current status
                health = await self._health_status()
                metrics = await self._metrics_status()
                alerts = await self._alerts_status()
                
                # Prepare update message
                message = {
                    "type": "update",
                    "data": {
                        "health": health,
                        "metrics": metrics,
                        "alerts": alerts
                    }
                }
                
                # Broadcast to all connected clients
                for connection in self._active_connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error("Failed to send update to client", error=str(e))
                        self._active_connections.remove(connection)
                        
                # Wait for next update
                await asyncio.sleep(DASHBOARD_CONFIG["refresh_interval"])
                
            except Exception as e:
                logger.error("Failed to broadcast updates", error=str(e))
                await asyncio.sleep(1)  # Wait before retrying
                
    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        return self._app

# Create singleton instance
dashboard_manager = DashboardManager() 