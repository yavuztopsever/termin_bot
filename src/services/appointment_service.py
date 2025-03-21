"""Appointment service for managing appointment operations."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.db import Appointment, db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AppointmentService:
    """Service for managing appointment operations."""
    
    @staticmethod
    async def create_appointment(appointment_data: Dict[str, Any]) -> Appointment:
        """Create a new appointment."""
        try:
            async with db.async_session() as session:
                appointment = Appointment(**appointment_data)
                session.add(appointment)
                await session.commit()
                logger.info(f"Created new appointment for service: {appointment.service_id}")
                return appointment
        except IntegrityError:
            logger.error(f"Failed to create appointment: Invalid data")
            raise
        except Exception as e:
            logger.error(f"Failed to create appointment: {e}")
            raise
            
    @staticmethod
    async def get_appointment(appointment_id: int) -> Optional[Appointment]:
        """Get an appointment by ID."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if appointment:
                    logger.info(f"Retrieved appointment: {appointment_id}")
                else:
                    logger.info(f"Appointment not found: {appointment_id}")
                return appointment
        except Exception as e:
            logger.error(f"Failed to get appointment: {e}")
            raise
            
    @staticmethod
    async def get_user_appointments(user_id: int) -> List[Appointment]:
        """Get all appointments for a user."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(Appointment.user_id == user_id)
                )
                appointments = result.scalars().all()
                logger.info(f"Retrieved {len(appointments)} appointments for user: {user_id}")
                return appointments
        except Exception as e:
            logger.error(f"Failed to get user appointments: {e}")
            raise
            
    @staticmethod
    async def get_available_appointments(service_id: str, location_id: Optional[str] = None) -> List[Appointment]:
        """Get all available appointments for a service and location."""
        try:
            async with db.async_session() as session:
                query = select(Appointment).where(
                    Appointment.service_id == service_id,
                    Appointment.status == 'available'
                )
                if location_id:
                    query = query.where(Appointment.location_id == location_id)
                    
                result = await session.execute(query)
                appointments = result.scalars().all()
                logger.info(f"Retrieved {len(appointments)} available appointments for service: {service_id}")
                return appointments
        except Exception as e:
            logger.error(f"Failed to get available appointments: {e}")
            raise
            
    @staticmethod
    async def update_appointment(appointment_id: int, update_data: Dict[str, Any]) -> bool:
        """Update appointment information."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    logger.info(f"Appointment not found for update: {appointment_id}")
                    return False
                    
                for key, value in update_data.items():
                    setattr(appointment, key, value)
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated appointment: {appointment_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update appointment: {e}")
            raise
            
    @staticmethod
    async def delete_appointment(appointment_id: int) -> bool:
        """Delete an appointment."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    logger.info(f"Appointment not found for deletion: {appointment_id}")
                    return False
                    
                await session.delete(appointment)
                await session.commit()
                logger.info(f"Deleted appointment: {appointment_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete appointment: {e}")
            raise
            
    @staticmethod
    async def book_appointment(appointment_id: int, user_id: int) -> bool:
        """Book an appointment for a user."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(
                        Appointment.id == appointment_id,
                        Appointment.status == 'available'
                    )
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    logger.info(f"Appointment not found or not available: {appointment_id}")
                    return False
                    
                appointment.user_id = user_id
                appointment.status = 'booked'
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Booked appointment {appointment_id} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to book appointment: {e}")
            raise
            
    @staticmethod
    async def cancel_appointment(appointment_id: int) -> bool:
        """Cancel a booked appointment."""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(Appointment).where(
                        Appointment.id == appointment_id,
                        Appointment.status == 'booked'
                    )
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    logger.info(f"Appointment not found or not booked: {appointment_id}")
                    return False
                    
                appointment.user_id = None
                appointment.status = 'available'
                appointment.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Cancelled appointment: {appointment_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to cancel appointment: {e}")
            raise 