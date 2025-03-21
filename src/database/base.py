from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, DateTime
from datetime import datetime

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        self.session = session
        
    def set_session(self, session: AsyncSession) -> None:
        """Set the database session."""
        self.session = session
        
    async def get(self, model: Type[T], id: str) -> Optional[T]:
        """Get an entity by ID."""
        query = select(model).where(model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all(self, model: Type[T]) -> List[T]:
        """Get all entities."""
        query = select(model)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
        
    async def update(self, entity: T) -> T:
        """Update an entity."""
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
        
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.commit()
        
    async def get_with_relations(
        self,
        model: Type[T],
        id: str,
        relations: List[str]
    ) -> Optional[T]:
        """Get an entity with its relations."""
        query = select(model)
        
        # Add relations to the query
        for relation in relations:
            query = query.options(selectinload(getattr(model, relation)))
            
        query = query.where(model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_field(
        self,
        model: Type[T],
        field: str,
        value: any
    ) -> List[T]:
        """Get entities by field value."""
        query = select(model).where(getattr(model, field) == value)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_by_field_range(
        self,
        model: Type[T],
        field: str,
        min_value: Optional[any] = None,
        max_value: Optional[any] = None
    ) -> List[T]:
        """Get entities within a field value range."""
        query = select(model)
        
        if min_value is not None:
            query = query.where(getattr(model, field) >= min_value)
        if max_value is not None:
            query = query.where(getattr(model, field) <= max_value)
            
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_active(self, model: Type[T]) -> List[T]:
        """Get all active entities."""
        return await self.get_by_field(model, "is_active", True)
        
    async def get_inactive(self, model: Type[T]) -> List[T]:
        """Get all inactive entities."""
        return await self.get_by_field(model, "is_active", False)
        
    async def count(self, model: Type[T]) -> int:
        """Get total count of entities."""
        query = select(model)
        result = await self.session.execute(query)
        return len(result.scalars().all())
        
    async def exists(self, model: Type[T], id: str) -> bool:
        """Check if an entity exists."""
        entity = await self.get(model, id)
        return entity is not None 

Base = declarative_base()

class BaseModel(Base):
    """Base model for all database models."""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
        
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model from dictionary."""
        return cls(**data)
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update model with dictionary data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>" 