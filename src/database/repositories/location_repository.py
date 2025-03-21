from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.location import Location
from src.database.base import BaseRepository

class LocationRepository(BaseRepository):
    """Repository for location operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        super().__init__(session)
        
    async def create(self, location: Location) -> Location:
        """Create a new location."""
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
        
    async def get_by_id(self, location_id: str) -> Optional[Location]:
        """Get location by ID."""
        query = select(Location).where(Location.id == location_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_city(self, city: str) -> List[Location]:
        """Get locations by city."""
        query = select(Location).where(Location.city == city)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_active(self) -> List[Location]:
        """Get all active locations."""
        query = select(Location).where(Location.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_all(self) -> List[Location]:
        """Get all locations."""
        query = select(Location)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def update(self, location: Location) -> Location:
        """Update a location."""
        await self.session.commit()
        await self.session.refresh(location)
        return location
        
    async def delete(self, location: Location) -> None:
        """Delete a location."""
        await self.session.delete(location)
        await self.session.commit()
        
    async def get_with_appointments(self, location_id: str) -> Optional[Location]:
        """Get location with related appointments."""
        query = (
            select(Location)
            .options(selectinload(Location.appointments))
            .where(Location.id == location_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_capacity_range(
        self,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None
    ) -> List[Location]:
        """Get locations within a capacity range."""
        query = select(Location)
        
        if min_capacity is not None:
            query = query.where(Location.current_capacity >= min_capacity)
        if max_capacity is not None:
            query = query.where(Location.current_capacity <= max_capacity)
            
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def update_capacity(self, location_id: str, new_capacity: int) -> Optional[Location]:
        """Update location capacity."""
        location = await self.get_by_id(location_id)
        if location:
            location.current_capacity = new_capacity
            await self.update(location)
        return location

# Create singleton instance
location_repository = LocationRepository(None)  # Session will be set when needed 