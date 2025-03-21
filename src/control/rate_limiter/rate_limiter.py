"""
Rate Limiter implementation for controlling request rates.
"""

from typing import Dict, Any, Optional
import asyncio
from ..redis_rate_limiter import RedisRateLimiter
from ..token_bucket import TokenBucket
from ...utils.logger import get_logger
from ...config import settings

logger = get_logger(__name__)

class RateLimiter:
    """Rate Limiter for controlling request rates."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        use_redis: bool = True
    ):
        """Initialize the Rate Limiter."""
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.use_redis = use_redis
        
        if use_redis:
            self.limiter = RedisRateLimiter(
                redis_url=settings.REDIS_URL,
                requests_per_minute=requests_per_minute,
                burst_size=burst_size
            )
        else:
            self.limiter = TokenBucket(
                rate=requests_per_minute / 60,  # Convert to requests per second
                burst=burst_size
            )
            
    async def start(self):
        """Start the Rate Limiter."""
        if self.use_redis:
            await self.limiter.start()
            
    async def stop(self):
        """Stop the Rate Limiter."""
        if self.use_redis:
            await self.limiter.stop()
            
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        try:
            return await self.limiter.acquire(client_id)
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False
            
    async def get_rate_limit_info(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit information for client."""
        try:
            if self.use_redis:
                return await self.limiter.get_info(client_id)
            else:
                return {
                    "rate": self.requests_per_minute,
                    "burst": self.burst_size,
                    "remaining": self.limiter.get_remaining_tokens(client_id)
                }
                
        except Exception as e:
            logger.error(f"Error getting rate limit info: {str(e)}")
            return {}
            
    async def reset_rate_limit(self, client_id: str):
        """Reset rate limit for client."""
        try:
            if self.use_redis:
                await self.limiter.reset(client_id)
            else:
                self.limiter.reset_tokens(client_id)
                
        except Exception as e:
            logger.error(f"Error resetting rate limit: {str(e)}")
            
    async def update_rate_limit(
        self,
        client_id: str,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None
    ):
        """Update rate limit for client."""
        try:
            if requests_per_minute is not None:
                self.requests_per_minute = requests_per_minute
                
            if burst_size is not None:
                self.burst_size = burst_size
                
            if self.use_redis:
                await self.limiter.update(
                    client_id,
                    requests_per_minute,
                    burst_size
                )
            else:
                self.limiter.update_rate(
                    rate=requests_per_minute / 60 if requests_per_minute else None,
                    burst=burst_size
                )
                
        except Exception as e:
            logger.error(f"Error updating rate limit: {str(e)}") 