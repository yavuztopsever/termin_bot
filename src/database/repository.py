"""Base repository for database operations."""

import asyncio
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, Tuple, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select, delete, insert, update
from sqlalchemy.sql.expression import BinaryExpression
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from src.database.db_pool import db_pool
from src.utils.logger import setup_logger, log_error, get_correlation_id

logger = setup_logger(__name__)

T = TypeVar('T')

class Repository(Generic[T]):
    """Base repository for database operations."""
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize repository.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        
    @db_pool.with_retry()
    async def find_by_id(self, id: int) -> Optional[T]:
        """
        Find entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        async with db_pool.session() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            return result.scalar_one_or_none()
            
    @db_pool.with_retry()
    async def find_one(self, *filters: BinaryExpression) -> Optional[T]:
        """
        Find one entity by filters.
        
        Args:
            *filters: SQLAlchemy filter expressions
            
        Returns:
            Entity or None if not found
        """
        async with db_pool.session() as session:
            query = select(self.model_class)
            for filter_expr in filters:
                query = query.where(filter_expr)
                
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
    @db_pool.with_retry()
    async def find_all(self, *filters: BinaryExpression) -> List[T]:
        """
        Find all entities matching filters.
        
        Args:
            *filters: SQLAlchemy filter expressions
            
        Returns:
            List of entities
        """
        async with db_pool.session() as session:
            query = select(self.model_class)
            for filter_expr in filters:
                query = query.where(filter_expr)
                
            result = await session.execute(query)
            return list(result.scalars().all())
            
    @db_pool.with_retry()
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            Created entity
        """
        async with db_pool.transaction() as session:
            entity = self.model_class(**data)
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity
            
    @db_pool.with_retry()
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            id: Entity ID
            data: Updated data
            
        Returns:
            Updated entity or None if not found
        """
        async with db_pool.transaction() as session:
            # Get entity
            entity = await session.get(self.model_class, id)
            if not entity:
                return None
                
            # Update entity
            for key, value in data.items():
                setattr(entity, key, value)
                
            await session.flush()
            await session.refresh(entity)
            return entity
            
    @db_pool.with_retry()
    async def delete(self, id: int) -> bool:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False if not found
        """
        async with db_pool.transaction() as session:
            # Get entity
            entity = await session.get(self.model_class, id)
            if not entity:
                return False
                
            # Delete entity
            await session.delete(entity)
            return True
            
    @db_pool.with_retry()
    async def count(self, *filters: BinaryExpression) -> int:
        """
        Count entities matching filters.
        
        Args:
            *filters: SQLAlchemy filter expressions
            
        Returns:
            Number of entities
        """
        async with db_pool.session() as session:
            query = select(self.model_class)
            for filter_expr in filters:
                query = query.where(filter_expr)
                
            result = await session.execute(query)
            return len(result.scalars().all())
            
    @db_pool.with_retry()
    async def exists(self, *filters: BinaryExpression) -> bool:
        """
        Check if entity exists.
        
        Args:
            *filters: SQLAlchemy filter expressions
            
        Returns:
            True if entity exists, False otherwise
        """
        async with db_pool.session() as session:
            query = select(self.model_class)
            for filter_expr in filters:
                query = query.where(filter_expr)
                
            result = await session.execute(query)
            return result.first() is not None
            
    @db_pool.with_retry()
    async def execute_query(self, query: Select) -> List[T]:
        """
        Execute a custom query.
        
        Args:
            query: SQLAlchemy query
            
        Returns:
            Query results
        """
        async with db_pool.session() as session:
            result = await session.execute(query)
            return list(result.scalars().all())
            
    @db_pool.with_retry()
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query results
        """
        async with db_pool.session() as session:
            result = await session.execute(query, params or {})
            return list(result.fetchall())
            
    @db_pool.with_retry()
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple entities.
        
        Args:
            data_list: List of entity data
            
        Returns:
            List of created entities
        """
        async with db_pool.transaction() as session:
            entities = [self.model_class(**data) for data in data_list]
            session.add_all(entities)
            await session.flush()
            
            # Refresh entities
            for entity in entities:
                await session.refresh(entity)
                
            return entities
            
    @db_pool.with_retry()
    async def bulk_update(self, updates: List[Tuple[int, Dict[str, Any]]]) -> List[Optional[T]]:
        """
        Update multiple entities.
        
        Args:
            updates: List of (id, data) tuples
            
        Returns:
            List of updated entities
        """
        async with db_pool.transaction() as session:
            results = []
            
            for id, data in updates:
                # Get entity
                entity = await session.get(self.model_class, id)
                if not entity:
                    results.append(None)
                    continue
                    
                # Update entity
                for key, value in data.items():
                    setattr(entity, key, value)
                    
                results.append(entity)
                
            await session.flush()
            
            # Refresh entities
            for entity in results:
                if entity:
                    await session.refresh(entity)
                    
            return results
            
    @db_pool.with_retry()
    async def bulk_delete(self, ids: List[int]) -> int:
        """
        Delete multiple entities.
        
        Args:
            ids: List of entity IDs
            
        Returns:
            Number of deleted entities
        """
        async with db_pool.transaction() as session:
            stmt = delete(self.model_class).where(self.model_class.id.in_(ids))
            result = await session.execute(stmt)
            return result.rowcount
            
    async def transaction(self, func: Callable[[AsyncSession], Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function within a transaction.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        async with db_pool.transaction() as session:
            return await func(session, *args, **kwargs)
