from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.appointment import Appointment
from src.database.base import BaseRepository

class AppointmentRepository(BaseRepository):
    """Repository for appointment operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        super().__init__(session)
        
    async def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment."""
        self.session.add(appointment)
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment
        
    async def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_booking_id(self, booking_id: str) -> Optional[Appointment]:
        """Get appointment by booking ID."""
        query = select(Appointment).where(Appointment.booking_id == booking_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_service_id(self, service_id: str) -> List[Appointment]:
        """Get appointments by service ID."""
        query = select(Appointment).where(Appointment.service_id == service_id)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_by_office_id(self, office_id: str) -> List[Appointment]:
        """Get appointments by office ID."""
        query = select(Appointment).where(Appointment.office_id == office_id)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_by_status(self, status: str) -> List[Appointment]:
        """Get appointments by status."""
        query = select(Appointment).where(Appointment.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def get_all(self) -> List[Appointment]:
        """Get all appointments."""
        query = select(Appointment)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def update(self, appointment: Appointment) -> Appointment:
        """Update an appointment."""
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment
        
    async def delete(self, appointment: Appointment) -> None:
        """Delete an appointment."""
        await self.session.delete(appointment)
        await self.session.commit()
        
    async def get_with_relations(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment with related service and location."""
        query = (
            select(Appointment)
            .options(
                selectinload(Appointment.service),
                selectinload(Appointment.location)
            )
            .where(Appointment.id == appointment_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_date_range(
        self,
        start_date: str,
        end_date: str,
        service_id: Optional[str] = None,
        office_id: Optional[str] = None
    ) -> List[Appointment]:
        """Get appointments within a date range."""
        query = select(Appointment).where(
            Appointment.date >= start_date,
            Appointment.date <= end_date
        )
        
        if service_id:
            query = query.where(Appointment.service_id == service_id)
        if office_id:
            query = query.where(Appointment.office_id == office_id)
            
        result = await self.session.execute(query)
        return result.scalars().all()

# Create singleton instance
appointment_repository = AppointmentRepository(None)  # Session will be set when needed 