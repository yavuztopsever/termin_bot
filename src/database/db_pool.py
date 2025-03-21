"""Database connection pool and transaction management."""

import asyncio
import contextlib
import functools
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TypeVar, cast
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_scoped_session
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from src.config.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    DB_POOL_PRE_PING,
    MAX_RETRIES,
    RETRY_DELAY
)
from src.utils.logger import setup_logger, log_error, get_correlation_id
from src.utils.retry import RetryConfig, async_retry

logger = setup_logger(__name__)

T = TypeVar('T')

class DatabasePool:
    """Database connection pool manager."""
    
    def __init__(self, test_mode: bool = False):
        """
        Initialize database connection pool.
        
        Args:
            test_mode: Whether to use test database
        """
        self.url = DATABASE_URL if not test_mode else "sqlite+aiosqlite:///test.db"
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.scoped_session: Optional[async_scoped_session] = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                # Create engine with appropriate pooling based on database type
                if self.url.startswith('sqlite'):
                    # SQLite doesn't support connection pooling with aiosqlite
                    self.engine = create_async_engine(
                        self.url,
                        echo=False,
                        poolclass=NullPool
                    )
                else:
                    # Use connection pooling for other databases
                    self.engine = create_async_engine(
                        self.url,
                        echo=False,
                        pool_size=DB_POOL_SIZE,
                        max_overflow=DB_MAX_OVERFLOW,
                        pool_timeout=DB_POOL_TIMEOUT,
                        pool_recycle=DB_POOL_RECYCLE,
                        pool_pre_ping=DB_POOL_PRE_PING
                    )
                
                # Create session factory
                self.session_factory = sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False
                )
                
                # Create scoped session
                self.scoped_session = async_scoped_session(
                    self.session_factory,
                    scopefunc=asyncio.current_task
                )
                
                self._initialized = True
                logger.info("Database connection pool initialized")
                
            except Exception as e:
                log_error(
                    logger,
                    e,
                    context={"url": self.url},
                    request_id=get_correlation_id()
                )
                raise
                
    async def close(self) -> None:
        """Close the database engine and connection pool."""
        if not self._initialized or not self.engine:
            return
            
        try:
            if self.scoped_session:
                await self.scoped_session.remove()
                
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection pool closed")
            
        except Exception as e:
            log_error(
                logger,
                e,
                context={"url": self.url},
                request_id=get_correlation_id()
            )
            raise
            
    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session from the pool.
        
        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()
            
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized")
            
        session = self.session_factory()
        try:
            yield session
        finally:
            await session.close()
            
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Start a database transaction.
        
        Yields:
            AsyncSession: Database session with active transaction
        """
        if not self._initialized:
            await self.initialize()
            
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized")
            
        session = self.session_factory()
        try:
            async with session.begin():
                yield session
        except Exception as e:
            log_error(
                logger,
                e,
                context={"transaction": True},
                request_id=get_correlation_id()
            )
            raise
        finally:
            await session.close()
            
    def with_retry(
        self,
        retry_config: Optional[RetryConfig] = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator for retrying database operations.
        
        Args:
            retry_config: Retry configuration
            
        Returns:
            Decorated function
        """
        # Default retry configuration for database operations
        config = retry_config or RetryConfig(
            max_retries=MAX_RETRIES,
            base_delay=RETRY_DELAY,
            max_delay=RETRY_DELAY * 10,
            backoff_factor=2.0,
            jitter=True,
            jitter_factor=0.1,
            retry_on_exceptions=(SQLAlchemyError, DBAPIError),
            retry_on_status_codes=()
        )
        
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                @async_retry(retry_config=config)
                async def _execute():
                    return await func(*args, **kwargs)
                    
                return await _execute()
                
            return wrapper
            
        return decorator
        
# Create a global database pool instance
db_pool = DatabasePool()
