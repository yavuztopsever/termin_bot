from typing import Optional
from contextlib import asynccontextmanager

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager
from src.notifications.manager import notification_manager
from src.notifications.config import NotificationConfig, DEFAULT_CONFIG, ENVIRONMENT_CONFIGS
from src.notifications.exceptions import NotificationInitializationError

logger = setup_logger(__name__)

class NotificationSystem:
    """Manager for the notification system."""
    
    def __init__(self):
        """Initialize the notification system."""
        self._initialized = False
        self._config: Optional[NotificationConfig] = None
        
    async def initialize(self) -> None:
        """Initialize the notification system."""
        try:
            # Get environment-specific configuration
            env_config = ENVIRONMENT_CONFIGS.get(config.environment, {})
            
            # Create configuration
            self._config = NotificationConfig.from_dict({
                **DEFAULT_CONFIG.to_dict(),
                **env_config
            })
            
            # Initialize notification manager
            await notification_manager.initialize()
            
            self._initialized = True
            logger.info("Notification system initialized")
            
        except Exception as e:
            logger.error("Failed to initialize notification system", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="notification_system",
                message=f"Failed to initialize notification system: {str(e)}"
            )
            raise NotificationInitializationError(f"Failed to initialize notification system: {str(e)}")
            
    async def shutdown(self) -> None:
        """Shutdown the notification system."""
        try:
            # Shutdown notification manager
            await notification_manager.shutdown()
            
            self._initialized = False
            logger.info("Notification system shut down")
            
        except Exception as e:
            logger.error("Failed to shutdown notification system", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="notification_system",
                message=f"Failed to shutdown notification system: {str(e)}"
            )
            raise
            
    @property
    def initialized(self) -> bool:
        """Check if the notification system is initialized."""
        return self._initialized
        
    @property
    def config(self) -> Optional[NotificationConfig]:
        """Get the current configuration."""
        return self._config
        
    async def update_config(self, new_config: dict) -> None:
        """Update the notification system configuration."""
        try:
            if not self._config:
                raise RuntimeError("Notification system not initialized")
                
            # Update configuration
            self._config.update(new_config)
            
            logger.info("Notification system configuration updated")
            
        except Exception as e:
            logger.error("Failed to update notification system configuration", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="notification_system",
                message=f"Failed to update notification system configuration: {str(e)}"
            )
            raise

# Create singleton instance
notification_system = NotificationSystem()

@asynccontextmanager
async def notification_context():
    """Context manager for notification system lifecycle."""
    try:
        await notification_system.initialize()
        yield notification_system
    finally:
        await notification_system.shutdown() 