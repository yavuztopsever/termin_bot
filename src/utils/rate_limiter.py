"""Rate limiting module."""

import time
from typing import Dict, Optional
from threading import Lock
from functools import wraps
import asyncio

from src.config.config import API_RATE_LIMITS
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager

logger = setup_logger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class RateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self):
        """Initialize rate limiter."""
        self.buckets = {}
        self.last_update = {}

    def allow_request(self, endpoint: str) -> bool:
        """Check if request should be allowed."""
        now = time.time()
        
        # Get endpoint config
        config = API_RATE_LIMITS.get('endpoints', {}).get(endpoint, API_RATE_LIMITS['default'])
        rate = config['rate']
        burst = config['burst']

        # Initialize bucket if needed
        if endpoint not in self.buckets:
            self.buckets[endpoint] = burst
            self.last_update[endpoint] = now
            return True

        # Calculate token refill
        time_passed = now - self.last_update[endpoint]
        self.last_update[endpoint] = now
        
        self.buckets[endpoint] = min(
            burst,
            self.buckets[endpoint] + time_passed * rate
        )

        # Check if we have enough tokens
        if self.buckets[endpoint] >= 1:
            self.buckets[endpoint] -= 1
            return True
            
        return False

def rate_limited(endpoint: str):
    """
    Decorator to rate limit function calls.
    
    Args:
        endpoint: API endpoint path
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Global rate limiter instance
rate_limiter = RateLimiter()