from typing import List, Optional
from pathlib import Path
import os
from datetime import datetime
from alembic import command
from alembic.config import Config as AlembicConfig

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

class MigrationsManager:
    """Manager for database migrations."""
    
    def __init__(self):
        """Initialize the migrations manager."""
        self._initialized = False
        self._alembic_cfg = None
        self._migrations_dir = Path("migrations")
        
    async def initialize(self) -> None:
        """Initialize the migrations manager."""
        try:
            # Create migrations directory if it doesn't exist
            self._migrations_dir.mkdir(exist_ok=True)
            
            # Create alembic configuration
            self._alembic_cfg = AlembicConfig("alembic.ini")
            self._alembic_cfg.set_main_option("script_location", str(self._migrations_dir))
            self._alembic_cfg.set_main_option(
                "sqlalchemy.url",
                f"postgresql://{config.database.user}:{config.database.password}"
                f"@{config.database.host}:{config.database.port}/{config.database.database}"
            )
            
            # Initialize alembic if not already initialized
            if not (self._migrations_dir / "versions").exists():
                command.init(self._alembic_cfg, str(self._migrations_dir))
                
            self._initialized = True
            logger.info("Migrations manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize migrations manager", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="migrations_manager",
                message=f"Failed to initialize migrations manager: {str(e)}"
            )
            raise
            
    async def create_migration(self, message: str) -> Optional[str]:
        """Create a new migration."""
        try:
            if not self._initialized:
                raise RuntimeError("Migrations manager not initialized")
                
            # Create migration
            command.revision(self._alembic_cfg, message=message, autogenerate=True)
            
            logger.info(f"Created migration: {message}")
            return message
            
        except Exception as e:
            logger.error("Failed to create migration", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="migrations_manager",
                message=f"Failed to create migration: {str(e)}"
            )
            return None
            
    async def upgrade(self, revision: str = "head") -> bool:
        """Upgrade database to specified revision."""
        try:
            if not self._initialized:
                raise RuntimeError("Migrations manager not initialized")
                
            # Start timing
            start_time = datetime.utcnow()
            
            # Upgrade database
            command.upgrade(self._alembic_cfg, revision)
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics_manager.record_migration("upgrade", duration)
            
            logger.info(f"Upgraded database to revision: {revision}")
            return True
            
        except Exception as e:
            logger.error("Failed to upgrade database", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="migrations_manager",
                message=f"Failed to upgrade database: {str(e)}"
            )
            return False
            
    async def downgrade(self, revision: str) -> bool:
        """Downgrade database to specified revision."""
        try:
            if not self._initialized:
                raise RuntimeError("Migrations manager not initialized")
                
            # Start timing
            start_time = datetime.utcnow()
            
            # Downgrade database
            command.downgrade(self._alembic_cfg, revision)
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics_manager.record_migration("downgrade", duration)
            
            logger.info(f"Downgraded database to revision: {revision}")
            return True
            
        except Exception as e:
            logger.error("Failed to downgrade database", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="migrations_manager",
                message=f"Failed to downgrade database: {str(e)}"
            )
            return False
            
    async def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        try:
            if not self._initialized:
                raise RuntimeError("Migrations manager not initialized")
                
            return command.current(self._alembic_cfg)
            
        except Exception as e:
            logger.error("Failed to get current revision", error=str(e))
            return None
            
    async def get_history(self) -> List[str]:
        """Get migration history."""
        try:
            if not self._initialized:
                raise RuntimeError("Migrations manager not initialized")
                
            return command.history(self._alembic_cfg)
            
        except Exception as e:
            logger.error("Failed to get migration history", error=str(e))
            return []
            
    @property
    def initialized(self) -> bool:
        """Check if the migrations manager is initialized."""
        return self._initialized

# Create singleton instance
migrations_manager = MigrationsManager() 