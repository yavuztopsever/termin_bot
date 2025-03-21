from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship

from src.database.base import Base

class Service(Base):
    """Model for services."""
    
    __tablename__ = "services"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    is_active = Column(Boolean, default=True)
    max_duration = Column(Integer)  # in minutes
    min_duration = Column(Integer)  # in minutes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="service")
    
    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name}, category={self.category})>"
        
    def to_dict(self) -> dict:
        """Convert service to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "max_duration": self.max_duration,
            "min_duration": self.min_duration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        """Create service from dictionary."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            is_active=data.get("is_active", True),
            max_duration=data.get("max_duration"),
            min_duration=data.get("min_duration"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow()
        ) 