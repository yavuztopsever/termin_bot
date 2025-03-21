"""Appointment service module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database import get_database
from src.models import Appointment, User
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AppointmentService:
    """Service for managing appointments."""
    
    def __init__(self):
        """Initialize the appointment service."""
        self.logger = logger
        
    async def create_appointment(self, user_id: int, appointment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new appointment."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                # Check if user exists
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                if not user:
                    self.logger.error(f"User {user_id} not found")
                    return None
                    
                # Create appointment
                appointment = Appointment(
                    user_id=user_id,
                    service_type=appointment_data.get("service_type"),
                    location=appointment_data.get("location"),
                    appointment_time=appointment_data.get("appointment_time"),
                    status="scheduled",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(appointment)
                await session.commit()
                
                return {
                    "id": appointment.id,
                    "user_id": appointment.user_id,
                    "service_type": appointment.service_type,
                    "location": appointment.location,
                    "appointment_time": appointment.appointment_time.isoformat(),
                    "status": appointment.status,
                    "created_at": appointment.created_at.isoformat(),
                    "updated_at": appointment.updated_at.isoformat()
                }
                
        except IntegrityError as e:
            self.logger.error(f"Failed to create appointment: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating appointment: {e}")
            return None
            
    async def get_appointment(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        """Get an appointment by ID."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                appointment = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = appointment.scalar_one_or_none()
                
                if not appointment:
                    return None
                    
                return {
                    "id": appointment.id,
                    "user_id": appointment.user_id,
                    "service_type": appointment.service_type,
                    "location": appointment.location,
                    "appointment_time": appointment.appointment_time.isoformat(),
                    "status": appointment.status,
                    "created_at": appointment.created_at.isoformat(),
                    "updated_at": appointment.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting appointment: {e}")
            return None
            
    async def get_user_appointments(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all appointments for a user."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                appointments = await session.execute(
                    select(Appointment).where(Appointment.user_id == user_id)
                )
                appointments = appointments.scalars().all()
                
                return [{
                    "id": appt.id,
                    "user_id": appt.user_id,
                    "service_type": appt.service_type,
                    "location": appt.location,
                    "appointment_time": appt.appointment_time.isoformat(),
                    "status": appt.status,
                    "created_at": appt.created_at.isoformat(),
                    "updated_at": appt.updated_at.isoformat()
                } for appt in appointments]
                
        except Exception as e:
            self.logger.error(f"Error getting user appointments: {e}")
            return []
            
    async def update_appointment(self, appointment_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an appointment."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                appointment = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = appointment.scalar_one_or_none()
                
                if not appointment:
                    return None
                    
                for key, value in update_data.items():
                    if hasattr(appointment, key):
                        setattr(appointment, key, value)
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "id": appointment.id,
                    "user_id": appointment.user_id,
                    "service_type": appointment.service_type,
                    "location": appointment.location,
                    "appointment_time": appointment.appointment_time.isoformat(),
                    "status": appointment.status,
                    "created_at": appointment.created_at.isoformat(),
                    "updated_at": appointment.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error updating appointment: {e}")
            return None
            
    async def delete_appointment(self, appointment_id: int) -> bool:
        """Delete an appointment."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                appointment = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = appointment.scalar_one_or_none()
                
                if not appointment:
                    return False
                    
                await session.delete(appointment)
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting appointment: {e}")
            return False 