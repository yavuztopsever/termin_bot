from typing import Optional
from contextlib import asynccontextmanager
from .manager import CacheManager
from .config import CacheConfig, DEFAULT_CONFIG, ENVIRONMENT_CONFIGS
from .exceptions import CacheInitializationError
from src.utils.logger import get_logger
from src.utils.metrics import record_metric

logger = get_logger(__name__)

class CacheSystem:
    """Manages the lifecycle of the caching system."""
    
    def __init__(self):
        """Initialize the cache system."""
        self._manager: Optional[CacheManager] = None
        self._config: Optional[CacheConfig] = None
        self._initialized = False
        
    async def initialize(self, environment: str = "development") -> None:
        """Initialize the cache system.
        
        Args:
            environment: The environment to use for configuration.
            
        Raises:
            CacheInitializationError: If initialization fails.
        """
        try:
            # Get environment-specific configuration
            env_config = ENVIRONMENT_CONFIGS.get(environment, {})
            
            # Create configuration from defaults and environment settings
            self._config = CacheConfig.from_dict(env_config)
            
            # Initialize cache manager
            self._manager = CacheManager()
            await self._manager.initialize(self._config)
            
            self._initialized = True
            logger.info("Cache system initialized successfully")
            
            # Record initialization metric
            record_metric("cache_system_initialized", 1)
            
        except Exception as e:
            logger.error(f"Failed to initialize cache system: {str(e)}")
            record_metric("cache_system_initialization_error", 1)
            raise CacheInitializationError(f"Failed to initialize cache system: {str(e)}")
            
    async def shutdown(self) -> None:
        """Shutdown the cache system."""
        if self._manager:
            try:
                await self._manager.shutdown()
                self._initialized = False
                logger.info("Cache system shut down successfully")
                record_metric("cache_system_shutdown", 1)
            except Exception as e:
                logger.error(f"Failed to shutdown cache system: {str(e)}")
                record_metric("cache_system_shutdown_error", 1)
                raise
                
    @property
    def initialized(self) -> bool:
        """Check if the cache system is initialized."""
        return self._initialized
        
    @property
    def config(self) -> Optional[CacheConfig]:
        """Get the current configuration."""
        return self._config
        
    async def update_config(self, new_config: dict) -> None:
        """Update the cache system configuration.
        
        Args:
            new_config: New configuration values to apply.
            
        Raises:
            CacheInitializationError: If the system is not initialized.
        """
        if not self._initialized:
            raise CacheInitializationError("Cache system is not initialized")
            
        try:
            # Update configuration
            self._config.update(new_config)
            
            # Reinitialize manager with new config
            if self._manager:
                await self._manager.shutdown()
                await self._manager.initialize(self._config)
                
            logger.info("Cache system configuration updated successfully")
            record_metric("cache_system_config_updated", 1)
            
        except Exception as e:
            logger.error(f"Failed to update cache system configuration: {str(e)}")
            record_metric("cache_system_config_update_error", 1)
            raise CacheInitializationError(f"Failed to update cache system configuration: {str(e)}")

# Create singleton instance
cache_system = CacheSystem()

@asynccontextmanager
async def cache_context(environment: str = "development"):
    """Context manager for cache system lifecycle.
    
    Args:
        environment: The environment to use for configuration.
        
    Yields:
        CacheSystem: The initialized cache system.
    """
    try:
        await cache_system.initialize(environment)
        yield cache_system
    finally:
        await cache_system.shutdown() 