from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

class DatabaseManager:
    """Manager for database connections and sessions."""
    
    def __init__(self):
        """Initialize the database manager."""
        self._initialized = False
        self._engine = None
        self._session_factory = None
        
    async def initialize(self) -> None:
        """Initialize the database connection."""
        try:
            # Create database URL
            db_url = (
                f"postgresql://{config.database.user}:{config.database.password}"
                f"@{config.database.host}:{config.database.port}/{config.database.database}"
            )
            
            # Create engine
            self._engine = create_engine(
                db_url,
                pool_size=config.database.pool_size,
                pool_timeout=config.database.pool_timeout,
                pool_pre_ping=True,
                echo=False  # Set to True for SQL query logging
            )
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Test connection
            with self.get_session() as session:
                session.execute("SELECT 1")
                
            self._initialized = True
            logger.info("Database manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize database manager", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="database_manager",
                message=f"Failed to initialize database manager: {str(e)}"
            )
            raise
            
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
            
        session = self._session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("Database error", error=str(e))
            metrics_manager.record_database_error()
            await alert_manager.create_alert(
                level="error",
                component="database_manager",
                message=f"Database error: {str(e)}"
            )
            raise
        finally:
            session.close()
            
    async def shutdown(self) -> None:
        """Shutdown the database connection."""
        if self._engine:
            self._engine.dispose()
            self._initialized = False
            logger.info("Database manager shut down")
            
    @property
    def initialized(self) -> bool:
        """Check if the database manager is initialized."""
        return self._initialized

# Create singleton instance
db_manager = DatabaseManager() 