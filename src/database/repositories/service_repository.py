from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.service import Service
from src.database.base import BaseRepository

class ServiceRepository(BaseRepository):
    """Repository for service operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        super().__init__(session)
        
    async def create(self, service: Service) -> Service:
        """Create a new service."""
        self.session.add(service)
        await self.session.commit()
        await self.session.refresh(service)
        return service
        
    async def get_by_id(self, service_id: str) -> Optional[Service]:
        """Get service by ID."""
        query = select(Service).where(Service.id == service_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_category(self, category: str) -> List[Service]:
        """Get services by category."""
        query = select(Service).where(Service.category == category)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_active(self) -> List[Service]:
        """Get all active services."""
        query = select(Service).where(Service.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_all(self) -> List[Service]:
        """Get all services."""
        query = select(Service)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def update(self, service: Service) -> Service:
        """Update a service."""
        await self.session.commit()
        await self.session.refresh(service)
        return service
        
    async def delete(self, service: Service) -> None:
        """Delete a service."""
        await self.session.delete(service)
        await self.session.commit()
        
    async def get_with_appointments(self, service_id: str) -> Optional[Service]:
        """Get service with related appointments."""
        query = (
            select(Service)
            .options(selectinload(Service.appointments))
            .where(Service.id == service_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_duration_range(
        self,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[Service]:
        """Get services within a duration range."""
        query = select(Service)
        
        if min_duration is not None:
            query = query.where(Service.min_duration >= min_duration)
        if max_duration is not None:
            query = query.where(Service.max_duration <= max_duration)
            
        result = await self.session.execute(query)
        return result.scalars().all()

# Create singleton instance
service_repository = ServiceRepository(None)  # Session will be set when needed 