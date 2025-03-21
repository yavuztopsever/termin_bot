"""
API Gateway implementation for handling incoming requests and routing them to appropriate services.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .router import Router
from .middleware import (
    AuthMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
    ErrorHandlerMiddleware
)
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class APIGateway:
    """API Gateway for handling incoming requests and routing them to appropriate services."""
    
    def __init__(self):
        """Initialize the API Gateway."""
        self.app = FastAPI(
            title="Munich Termin Automator API",
            description="API Gateway for Munich Termin Automator",
            version="1.0.0"
        )
        self.router = Router()
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """Set up middleware for request processing."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Custom middleware
        self.app.add_middleware(LoggingMiddleware)
        self.app.add_middleware(AuthMiddleware)
        self.app.add_middleware(RateLimitMiddleware)
        self.app.add_middleware(ErrorHandlerMiddleware)
        
    def _setup_routes(self):
        """Set up API routes."""
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
            
        # Service routes
        self.app.include_router(
            self.router.auth_router,
            prefix="/auth",
            tags=["Authentication"]
        )
        self.app.include_router(
            self.router.appointment_router,
            prefix="/appointments",
            tags=["Appointments"]
        )
        self.app.include_router(
            self.router.notification_router,
            prefix="/notifications",
            tags=["Notifications"]
        )
        
    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request and route to appropriate service."""
        try:
            # Log incoming request
            logger.info(f"Incoming request: {request.method} {request.url}")
            
            # Process request through middleware
            response = await self.app(request)
            
            # Log response
            logger.info(f"Response status: {response.status_code}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            raise
            
    def start(self):
        """Start the API Gateway server."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level=settings.LOG_LEVEL
        ) 