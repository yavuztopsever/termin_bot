from typing import Optional
from contextlib import asynccontextmanager
from .manager import MonitoringManager
from .config import MonitoringConfig, DEFAULT_CONFIG, ENVIRONMENT_CONFIGS
from .exceptions import MonitoringInitializationError
from src.utils.logger import get_logger
from src.utils.metrics import record_metric

logger = get_logger(__name__)

class MonitoringSystem:
    """Manages the lifecycle of the monitoring system."""
    
    def __init__(self):
        """Initialize the monitoring system."""
        self._manager: Optional[MonitoringManager] = None
        self._config: Optional[MonitoringConfig] = None
        self._initialized = False
        
    async def initialize(self, environment: str = "development") -> None:
        """Initialize the monitoring system.
        
        Args:
            environment: The environment to use for configuration.
            
        Raises:
            MonitoringInitializationError: If initialization fails.
        """
        try:
            # Get environment-specific configuration
            env_config = ENVIRONMENT_CONFIGS.get(environment, {})
            
            # Create configuration from defaults and environment settings
            self._config = MonitoringConfig.from_dict(env_config)
            
            # Initialize monitoring manager
            self._manager = MonitoringManager()
            await self._manager.initialize()
            
            self._initialized = True
            logger.info("Monitoring system initialized successfully")
            
            # Record initialization metric
            record_metric("monitoring_system_initialized", 1)
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring system: {str(e)}")
            record_metric("monitoring_system_initialization_error", 1)
            raise MonitoringInitializationError(f"Failed to initialize monitoring system: {str(e)}")
            
    async def shutdown(self) -> None:
        """Shutdown the monitoring system."""
        if self._manager:
            try:
                await self._manager.shutdown()
                self._initialized = False
                logger.info("Monitoring system shut down successfully")
                record_metric("monitoring_system_shutdown", 1)
            except Exception as e:
                logger.error(f"Failed to shutdown monitoring system: {str(e)}")
                record_metric("monitoring_system_shutdown_error", 1)
                raise
                
    @property
    def initialized(self) -> bool:
        """Check if the monitoring system is initialized."""
        return self._initialized
        
    @property
    def config(self) -> Optional[MonitoringConfig]:
        """Get the current configuration."""
        return self._config
        
    async def update_config(self, new_config: dict) -> None:
        """Update the monitoring system configuration.
        
        Args:
            new_config: New configuration values to apply.
            
        Raises:
            MonitoringInitializationError: If the system is not initialized.
        """
        if not self._initialized:
            raise MonitoringInitializationError("Monitoring system is not initialized")
            
        try:
            # Update configuration
            self._config.update(new_config)
            
            # Reinitialize manager with new config
            if self._manager:
                await self._manager.shutdown()
                await self._manager.initialize()
                
            logger.info("Monitoring system configuration updated successfully")
            record_metric("monitoring_system_config_updated", 1)
            
        except Exception as e:
            logger.error(f"Failed to update monitoring system configuration: {str(e)}")
            record_metric("monitoring_system_config_update_error", 1)
            raise MonitoringInitializationError(f"Failed to update monitoring system configuration: {str(e)}")

# Create singleton instance
monitoring_system = MonitoringSystem()

@asynccontextmanager
async def monitoring_context(environment: str = "development"):
    """Context manager for monitoring system lifecycle.
    
    Args:
        environment: The environment to use for configuration.
        
    Yields:
        MonitoringSystem: The initialized monitoring system.
    """
    try:
        await monitoring_system.initialize(environment)
        yield monitoring_system
    finally:
        await monitoring_system.shutdown() 