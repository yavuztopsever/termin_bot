from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from src.database.base import Base

class AppointmentStatus(enum.Enum):
    """Enum for appointment status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"

class Appointment(Base):
    """Model for appointments."""
    
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True)
    booking_id = Column(String, unique=True, nullable=False)
    service_id = Column(String, ForeignKey("services.id"), nullable=False)
    office_id = Column(String, ForeignKey("locations.id"), nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service = relationship("Service", back_populates="appointments")
    location = relationship("Location", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, booking_id={self.booking_id}, status={self.status})>"
        
    def to_dict(self) -> dict:
        """Convert appointment to dictionary."""
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "service_id": self.service_id,
            "office_id": self.office_id,
            "date": self.date,
            "time": self.time,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "Appointment":
        """Create appointment from dictionary."""
        return cls(
            id=data.get("id"),
            booking_id=data["booking_id"],
            service_id=data["service_id"],
            office_id=data["office_id"],
            date=data["date"],
            time=data["time"],
            status=AppointmentStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow()
        ) 