from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from src.database.base import Base

class AppointmentStatus(enum.Enum):
    """Enum for appointment status."""
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Appointment(Base):
    """SQLAlchemy model for appointments."""
    __tablename__ = "appointments"

    id = Column(String, primary_key=True)
    service_id = Column(String, ForeignKey("services.id"), nullable=False)
    service_name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.AVAILABLE)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="appointments")
    booking = relationship("Booking", back_populates="appointment", uselist=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert appointment to dictionary."""
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "date": self.date.isoformat(),
            "time": self.time,
            "location": self.location,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Appointment':
        """Create appointment from dictionary."""
        return cls(
            id=data["id"],
            service_id=data["service_id"],
            service_name=data["service_name"],
            date=datetime.fromisoformat(data["date"]),
            time=data["time"],
            location=data["location"],
            status=AppointmentStatus(data["status"]),
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

class Service(Base):
    """SQLAlchemy model for services."""
    __tablename__ = "services"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    location = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="service")

    def to_dict(self) -> Dict[str, Any]:
        """Convert service to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """Create service from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            location=data["location"],
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

class Booking(Base):
    """SQLAlchemy model for bookings."""
    __tablename__ = "bookings"

    id = Column(String, primary_key=True)
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=False)
    user_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="confirmed")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointment = relationship("Appointment", back_populates="booking")

    def to_dict(self) -> Dict[str, Any]:
        """Convert booking to dictionary."""
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "user_id": self.user_id,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Booking':
        """Create booking from dictionary."""
        return cls(
            id=data["id"],
            appointment_id=data["appointment_id"],
            user_id=data["user_id"],
            status=data["status"],
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        ) 