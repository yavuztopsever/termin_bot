"""
Redis-based Rate Limiter implementation.
"""

from typing import Dict, Any, Optional
import asyncio
import aioredis
from ...utils.logger import get_logger

logger = get_logger(__name__)

class RedisRateLimiter:
    """Redis-based Rate Limiter implementation."""
    
    def __init__(
        self,
        redis_url: str,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        """Initialize the Redis Rate Limiter."""
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.redis = None
        
    async def start(self):
        """Start the Redis Rate Limiter."""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis Rate Limiter started")
            
        except Exception as e:
            logger.error(f"Error starting Redis Rate Limiter: {str(e)}")
            raise
            
    async def stop(self):
        """Stop the Redis Rate Limiter."""
        try:
            if self.redis:
                await self.redis.close()
                logger.info("Redis Rate Limiter stopped")
                
        except Exception as e:
            logger.error(f"Error stopping Redis Rate Limiter: {str(e)}")
            
    async def acquire(self, client_id: str) -> bool:
        """Acquire a token for the client."""
        try:
            if not self.redis:
                raise Exception("Redis Rate Limiter not started")
                
            # Get current tokens
            current = await self.redis.get(f"rate_limit:{client_id}")
            if current is None:
                # Initialize with burst size
                await self.redis.setex(
                    f"rate_limit:{client_id}",
                    60,  # 1 minute expiry
                    self.burst_size
                )
                return True
                
            current = int(current)
            if current <= 0:
                return False
                
            # Decrement tokens
            await self.redis.decr(f"rate_limit:{client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acquiring token: {str(e)}")
            return False
            
    async def get_info(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit information for client."""
        try:
            if not self.redis:
                raise Exception("Redis Rate Limiter not started")
                
            current = await self.redis.get(f"rate_limit:{client_id}")
            if current is None:
                return {
                    "rate": self.requests_per_minute,
                    "burst": self.burst_size,
                    "remaining": self.burst_size
                }
                
            return {
                "rate": self.requests_per_minute,
                "burst": self.burst_size,
                "remaining": int(current)
            }
            
        except Exception as e:
            logger.error(f"Error getting info: {str(e)}")
            return {}
            
    async def reset(self, client_id: str):
        """Reset rate limit for client."""
        try:
            if not self.redis:
                raise Exception("Redis Rate Limiter not started")
                
            await self.redis.setex(
                f"rate_limit:{client_id}",
                60,  # 1 minute expiry
                self.burst_size
            )
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {str(e)}")
            
    async def update(
        self,
        client_id: str,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None
    ):
        """Update rate limit for client."""
        try:
            if not self.redis:
                raise Exception("Redis Rate Limiter not started")
                
            if requests_per_minute is not None:
                self.requests_per_minute = requests_per_minute
                
            if burst_size is not None:
                self.burst_size = burst_size
                # Reset current tokens to new burst size
                await self.reset(client_id)
                
        except Exception as e:
            logger.error(f"Error updating rate limit: {str(e)}") 