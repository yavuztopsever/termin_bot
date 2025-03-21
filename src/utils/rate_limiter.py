"""Rate limiting module."""

import time
from typing import Dict, Optional
from threading import Lock
from functools import wraps
import asyncio
from datetime import datetime, timedelta

from src.config.config import API_CONFIG
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.exceptions import RateLimitExceeded

logger = setup_logger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        self._limits: Dict[str, int] = {}
        self._last_requests: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        
    async def acquire(self, endpoint: str, tokens: int = 1) -> None:
        """Acquire tokens for an API request."""
        async with self._lock:
            # Get current time
            now = datetime.utcnow()
            
            # Get or initialize limit and last request time
            limit = self._limits.get(endpoint, API_CONFIG["rate_limit"])
            last_request = self._last_requests.get(endpoint, now - timedelta(minutes=1))
            
            # Calculate time since last request
            time_since_last = (now - last_request).total_seconds()
            
            # Refresh tokens if enough time has passed
            if time_since_last >= API_CONFIG["rate_limit_period"]:
                self._limits[endpoint] = API_CONFIG["rate_limit"]
                self._last_requests[endpoint] = now
                
            # Check if we have enough tokens
            if self._limits[endpoint] < tokens:
                # Calculate wait time
                wait_time = API_CONFIG["rate_limit_period"] - time_since_last
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit exceeded for {endpoint}. Waiting {wait_time:.2f} seconds."
                    )
                    await asyncio.sleep(wait_time)
                    # Refresh tokens after waiting
                    self._limits[endpoint] = API_CONFIG["rate_limit"]
                    self._last_requests[endpoint] = datetime.utcnow()
                else:
                    raise RateLimitExceeded(f"Rate limit exceeded for {endpoint}")
                    
            # Consume tokens
            self._limits[endpoint] -= tokens
            self._last_requests[endpoint] = now
            
    async def release(self, endpoint: str, tokens: int = 1) -> None:
        """Release tokens back to the limit."""
        async with self._lock:
            if endpoint in self._limits:
                self._limits[endpoint] = min(
                    self._limits[endpoint] + tokens,
                    API_CONFIG["rate_limit"]
                )
                
    def get_remaining_tokens(self, endpoint: str) -> int:
        """Get remaining tokens for an endpoint."""
        return self._limits.get(endpoint, API_CONFIG["rate_limit"])
        
    def get_next_refresh_time(self, endpoint: str) -> Optional[datetime]:
        """Get the next time tokens will be refreshed."""
        if endpoint in self._last_requests:
            return self._last_requests[endpoint] + timedelta(seconds=API_CONFIG["rate_limit_period"])
        return None

def rate_limited(endpoint: str):
    """
    Decorator to rate limit function calls.
    
    Args:
        endpoint: API endpoint path
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        # Create a rate limiter instance for this endpoint
        endpoint_rate_limiter = RateLimiter()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not endpoint_rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Re-raise any exceptions from the decorated function
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not endpoint_rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Re-raise any exceptions from the decorated function
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Create singleton instance
rate_limiter = RateLimiter()