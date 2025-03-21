from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float
from sqlalchemy.orm import relationship

from src.database.base import Base

class Location(Base):
    """Model for locations/offices."""
    
    __tablename__ = "locations"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    postal_code = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)
    max_capacity = Column(Integer)
    current_capacity = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="location")
    
    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name}, city={self.city})>"
        
    def to_dict(self) -> dict:
        """Convert location to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_active": self.is_active,
            "max_capacity": self.max_capacity,
            "current_capacity": self.current_capacity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "Location":
        """Create location from dictionary."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            address=data.get("address"),
            city=data.get("city"),
            postal_code=data.get("postal_code"),
            country=data.get("country"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            is_active=data.get("is_active", True),
            max_capacity=data.get("max_capacity"),
            current_capacity=data.get("current_capacity"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow()
        ) 