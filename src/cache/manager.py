from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import pickle
import hashlib
from dataclasses import dataclass
import asyncio
from abc import ABC, abstractmethod

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        pass
        
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set a value in the cache."""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        pass
        
    @abstractmethod
    async def get_size(self) -> int:
        """Get the current size of the cache."""
        pass

class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize the memory cache backend."""
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        entry = self._cache.get(key)
        if entry and entry.expires_at and entry.expires_at < datetime.utcnow():
            await self.delete(key)
            return None
        return entry
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set a value in the cache."""
        # Check cache size
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            oldest_key = min(
                self._cache.items(),
                key=lambda x: x[1].created_at
            )[0]
            await self.delete(oldest_key)
            
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + ttl if ttl else None,
            metadata=metadata
        )
        
        self._cache[key] = entry
        
    async def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        self._cache.pop(key, None)
        
    async def clear(self) -> None:
        """Clear all values from the cache."""
        self._cache.clear()
        
    async def get_size(self) -> int:
        """Get the current size of the cache."""
        return len(self._cache)

class CacheManager:
    """Manager for caching API responses and other data."""
    
    def __init__(self):
        """Initialize the cache manager."""
        self._initialized = False
        self._backend: Optional[CacheBackend] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize the cache manager."""
        try:
            # Create cache backend
            self._backend = MemoryCacheBackend(
                max_size=config.cache.max_size
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
            
            self._initialized = True
            logger.info("Cache manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="cache_manager",
                message=f"Failed to initialize cache manager: {str(e)}"
            )
            raise
            
    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired cache entries."""
        while self._initialized:
            try:
                # Get all cache entries
                entries = await self._backend.get_all()
                
                # Remove expired entries
                for entry in entries:
                    if entry.expires_at and entry.expires_at < datetime.utcnow():
                        await self._backend.delete(entry.key)
                        
                await asyncio.sleep(config.cache.cleanup_interval.total_seconds())
                
            except Exception as e:
                logger.error("Error cleaning up expired cache entries", error=str(e))
                await asyncio.sleep(1)  # Wait before retrying
                
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Convert arguments to string
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
        
        # Create key
        key = f"{prefix}:{args_str}:{kwargs_str}"
        
        # Hash key if too long
        if len(key) > 255:
            key = hashlib.sha256(key.encode()).hexdigest()
            
        return key
        
    async def get(
        self,
        prefix: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Get a value from the cache."""
        try:
            if not self._initialized:
                raise RuntimeError("Cache manager not initialized")
                
            # Generate cache key
            key = self._generate_key(prefix, *args, **kwargs)
            
            # Get from cache
            entry = await self._backend.get(key)
            if entry:
                # Record metrics
                metrics_manager.record_cache("hit", None)
                return entry.value
                
            # Record metrics
            metrics_manager.record_cache("miss", None)
            return None
            
        except Exception as e:
            logger.error("Failed to get value from cache", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="cache_manager",
                message=f"Failed to get value from cache: {str(e)}"
            )
            raise
            
    async def set(
        self,
        prefix: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ) -> None:
        """Set a value in the cache."""
        try:
            if not self._initialized:
                raise RuntimeError("Cache manager not initialized")
                
            # Generate cache key
            key = self._generate_key(prefix, *args, **kwargs)
            
            # Set in cache
            await self._backend.set(
                key=key,
                value=value,
                ttl=ttl or config.cache.default_ttl,
                metadata=metadata
            )
            
            # Record metrics
            metrics_manager.record_cache("set", None)
            
        except Exception as e:
            logger.error("Failed to set value in cache", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="cache_manager",
                message=f"Failed to set value in cache: {str(e)}"
            )
            raise
            
    async def delete(
        self,
        prefix: str,
        *args,
        **kwargs
    ) -> None:
        """Delete a value from the cache."""
        try:
            if not self._initialized:
                raise RuntimeError("Cache manager not initialized")
                
            # Generate cache key
            key = self._generate_key(prefix, *args, **kwargs)
            
            # Delete from cache
            await self._backend.delete(key)
            
            # Record metrics
            metrics_manager.record_cache("delete", None)
            
        except Exception as e:
            logger.error("Failed to delete value from cache", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="cache_manager",
                message=f"Failed to delete value from cache: {str(e)}"
            )
            raise
            
    async def clear(self) -> None:
        """Clear all values from the cache."""
        try:
            if not self._initialized:
                raise RuntimeError("Cache manager not initialized")
                
            # Clear cache
            await self._backend.clear()
            
            # Record metrics
            metrics_manager.record_cache("clear", None)
            
        except Exception as e:
            logger.error("Failed to clear cache", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="cache_manager",
                message=f"Failed to clear cache: {str(e)}"
            )
            raise
            
    async def shutdown(self) -> None:
        """Shutdown the cache manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        self._initialized = False
        logger.info("Cache manager shut down")
        
    @property
    def initialized(self) -> bool:
        """Check if the cache manager is initialized."""
        return self._initialized

# Create singleton instance
cache_manager = CacheManager() 