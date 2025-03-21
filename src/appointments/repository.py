from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.appointments.models import Appointment, Service, Booking, AppointmentStatus
from src.appointments.exceptions import AppointmentNotFoundError, AppointmentStorageError

class AppointmentRepository:
    """Repository for appointment-related database operations."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        self.session = session
        
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Appointment:
        """Create a new appointment."""
        try:
            appointment = Appointment.from_dict(appointment_data)
            self.session.add(appointment)
            self.session.commit()
            return appointment
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to create appointment: {str(e)}")
            
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get an appointment by ID."""
        try:
            return self.session.query(Appointment).filter(Appointment.id == appointment_id).first()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get appointment: {str(e)}")
            
    def get_appointments(
        self,
        service_id: Optional[str] = None,
        status: Optional[AppointmentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Appointment]:
        """Get appointments with optional filters."""
        try:
            query = self.session.query(Appointment)
            
            if service_id:
                query = query.filter(Appointment.service_id == service_id)
                
            if status:
                query = query.filter(Appointment.status == status)
                
            if start_date:
                query = query.filter(Appointment.date >= start_date)
                
            if end_date:
                query = query.filter(Appointment.date <= end_date)
                
            return query.all()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get appointments: {str(e)}")
            
    def update_appointment(self, appointment_id: str, update_data: Dict[str, Any]) -> Appointment:
        """Update an appointment."""
        try:
            appointment = self.get_appointment(appointment_id)
            if not appointment:
                raise AppointmentNotFoundError(f"Appointment not found: {appointment_id}")
                
            for key, value in update_data.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)
                    
            self.session.commit()
            return appointment
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to update appointment: {str(e)}")
            
    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete an appointment."""
        try:
            appointment = self.get_appointment(appointment_id)
            if not appointment:
                raise AppointmentNotFoundError(f"Appointment not found: {appointment_id}")
                
            self.session.delete(appointment)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to delete appointment: {str(e)}")
            
    def create_service(self, service_data: Dict[str, Any]) -> Service:
        """Create a new service."""
        try:
            service = Service.from_dict(service_data)
            self.session.add(service)
            self.session.commit()
            return service
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to create service: {str(e)}")
            
    def get_service(self, service_id: str) -> Optional[Service]:
        """Get a service by ID."""
        try:
            return self.session.query(Service).filter(Service.id == service_id).first()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get service: {str(e)}")
            
    def get_services(self) -> List[Service]:
        """Get all services."""
        try:
            return self.session.query(Service).all()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get services: {str(e)}")
            
    def create_booking(self, booking_data: Dict[str, Any]) -> Booking:
        """Create a new booking."""
        try:
            booking = Booking.from_dict(booking_data)
            self.session.add(booking)
            self.session.commit()
            return booking
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to create booking: {str(e)}")
            
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get a booking by ID."""
        try:
            return self.session.query(Booking).filter(Booking.id == booking_id).first()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get booking: {str(e)}")
            
    def get_user_bookings(self, user_id: str) -> List[Booking]:
        """Get all bookings for a user."""
        try:
            return self.session.query(Booking).filter(Booking.user_id == user_id).all()
        except Exception as e:
            raise AppointmentStorageError(f"Failed to get user bookings: {str(e)}")
            
    def update_booking(self, booking_id: str, update_data: Dict[str, Any]) -> Booking:
        """Update a booking."""
        try:
            booking = self.get_booking(booking_id)
            if not booking:
                raise AppointmentNotFoundError(f"Booking not found: {booking_id}")
                
            for key, value in update_data.items():
                if hasattr(booking, key):
                    setattr(booking, key, value)
                    
            self.session.commit()
            return booking
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to update booking: {str(e)}")
            
    def delete_booking(self, booking_id: str) -> bool:
        """Delete a booking."""
        try:
            booking = self.get_booking(booking_id)
            if not booking:
                raise AppointmentNotFoundError(f"Booking not found: {booking_id}")
                
            self.session.delete(booking)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise AppointmentStorageError(f"Failed to delete booking: {str(e)}") 