from typing import Optional
from contextlib import asynccontextmanager

from src.monitoring.health import health_check_manager
from src.monitoring.health_config import HealthCheckConfig
from src.monitoring.health_exceptions import (
    HealthCheckInitializationError,
    HealthCheckShutdownError
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HealthCheckSystem:
    """Manages the lifecycle of the health check system."""
    
    def __init__(self):
        """Initialize the health check system."""
        self._initialized = False
        self._config: Optional[HealthCheckConfig] = None
        
    async def initialize(self, environment: str = "development") -> None:
        """Initialize the health check system.
        
        Args:
            environment: Environment to use for configuration
            
        Raises:
            HealthCheckInitializationError: If initialization fails
        """
        try:
            if self._initialized:
                logger.warning("Health check system already initialized")
                return
                
            # Initialize health check manager
            await health_check_manager.initialize(environment)
            
            # Store configuration
            self._config = health_check_manager.config
            
            self._initialized = True
            logger.info("Health check system initialized")
            
        except Exception as e:
            logger.error("Failed to initialize health check system", error=str(e))
            raise HealthCheckInitializationError(f"Failed to initialize health check system: {str(e)}")
            
    async def shutdown(self) -> None:
        """Shutdown the health check system.
        
        Raises:
            HealthCheckShutdownError: If shutdown fails
        """
        try:
            if not self._initialized:
                logger.warning("Health check system not initialized")
                return
                
            # Shutdown health check manager
            await health_check_manager.shutdown()
            
            self._initialized = False
            self._config = None
            logger.info("Health check system shut down")
            
        except Exception as e:
            logger.error("Failed to shutdown health check system", error=str(e))
            raise HealthCheckShutdownError(f"Failed to shutdown health check system: {str(e)}")
            
    @property
    def initialized(self) -> bool:
        """Check if the health check system is initialized."""
        return self._initialized
        
    @property
    def config(self) -> Optional[HealthCheckConfig]:
        """Get the current configuration."""
        return self._config

# Create singleton instance
health_check_system = HealthCheckSystem()

@asynccontextmanager
async def health_check_context(environment: str = "development"):
    """Context manager for health check system lifecycle.
    
    Args:
        environment: Environment to use for configuration
        
    Yields:
        HealthCheckSystem: The health check system instance
    """
    try:
        await health_check_system.initialize(environment)
        yield health_check_system
        
    finally:
        await health_check_system.shutdown() 