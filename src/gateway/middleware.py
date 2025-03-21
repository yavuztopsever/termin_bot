"""
Middleware implementations for request processing.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.logger import get_logger
from ..control.rate_limiter import RateLimiter
from ..services.auth import AuthService

logger = get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request through authentication middleware."""
        try:
            # Skip auth for health check and login endpoints
            if request.url.path in ["/health", "/auth/login"]:
                return await call_next(request)
                
            # Get token from header
            token = request.headers.get("Authorization")
            if not token:
                return Response(
                    status_code=401,
                    content={"error": "No authorization token provided"}
                )
                
            # Validate token
            auth_service = AuthService()
            if not await auth_service.validate_token(token):
                return Response(
                    status_code=401,
                    content={"error": "Invalid token"}
                )
                
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Auth middleware error: {str(e)}")
            return Response(
                status_code=500,
                content={"error": "Internal server error"}
            )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for handling rate limiting."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request through rate limiting middleware."""
        try:
            # Get client identifier
            client_id = request.client.host
            
            # Check rate limit
            rate_limiter = RateLimiter()
            if not await rate_limiter.check_rate_limit(client_id):
                return Response(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
                
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            return Response(
                status_code=500,
                content={"error": "Internal server error"}
            )

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request through logging middleware."""
        try:
            # Log request
            logger.info(
                f"Request: {request.method} {request.url} "
                f"from {request.client.host}"
            )
            
            # Process request
            response = await call_next(request)
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"for {request.method} {request.url}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Logging middleware error: {str(e)}")
            return Response(
                status_code=500,
                content={"error": "Internal server error"}
            )

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request through error handling middleware."""
        try:
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return Response(
                status_code=500,
                content={"error": "Internal server error"}
            ) 