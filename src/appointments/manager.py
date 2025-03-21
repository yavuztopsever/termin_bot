from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

from src.config.config import config
from src.utils.logger import setup_logger
from src.utils.api_client import api_client, APIError
from src.monitoring.metrics import metrics_manager
from src.monitoring.alerts import alert_manager

logger = setup_logger(__name__)

@dataclass
class Appointment:
    """Represents an appointment."""
    id: str
    service_id: str
    service_name: str
    date: datetime
    time: str
    location: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class AppointmentManager:
    """Manager for appointment operations."""
    
    def __init__(self):
        """Initialize the appointment manager."""
        self._initialized = False
        self._appointments: Dict[str, Appointment] = {}
        self._last_check: Optional[datetime] = None
        self._check_interval = timedelta(minutes=5)
        
    async def initialize(self) -> None:
        """Initialize the appointment manager."""
        try:
            # Load existing appointments
            await self._load_appointments()
            
            # Start background tasks
            asyncio.create_task(self._check_appointments())
            
            self._initialized = True
            logger.info("Appointment manager initialized")
            
        except Exception as e:
            logger.error("Failed to initialize appointment manager", error=str(e))
            await alert_manager.create_alert(
                level="critical",
                component="appointment_manager",
                message=f"Failed to initialize appointment manager: {str(e)}"
            )
            
    async def _load_appointments(self) -> None:
        """Load existing appointments from storage."""
        try:
            # TODO: Implement loading from database
            # For now, we'll start with an empty list
            self._appointments = {}
            logger.info("Loaded appointments from storage")
            
        except Exception as e:
            logger.error("Failed to load appointments", error=str(e))
            raise
            
    async def _check_appointments(self) -> None:
        """Background task to check for new appointments."""
        while self._initialized:
            try:
                # Check if enough time has passed since last check
                if self._last_check and datetime.utcnow() - self._last_check < self._check_interval:
                    await asyncio.sleep(1)
                    continue
                    
                # Check for new appointments
                await self._fetch_new_appointments()
                
                # Update last check time
                self._last_check = datetime.utcnow()
                
                # Wait for next check
                await asyncio.sleep(self._check_interval.total_seconds())
                
            except Exception as e:
                logger.error("Error checking appointments", error=str(e))
                await asyncio.sleep(1)  # Wait before retrying
                
    async def _fetch_new_appointments(self) -> None:
        """Fetch new appointments from the API."""
        try:
            # Get available services
            services = await self._get_available_services()
            
            # Check each service for appointments
            for service in services:
                try:
                    appointments = await self._get_service_appointments(service["id"])
                    
                    # Process new appointments
                    for appointment in appointments:
                        if appointment["id"] not in self._appointments:
                            await self._process_new_appointment(appointment)
                            
                except Exception as e:
                    logger.error(f"Failed to fetch appointments for service {service['id']}", error=str(e))
                    continue
                    
        except Exception as e:
            logger.error("Failed to fetch new appointments", error=str(e))
            await alert_manager.create_alert(
                level="warning",
                component="appointment_manager",
                message=f"Failed to fetch new appointments: {str(e)}"
            )
            
    async def _get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available services."""
        try:
            response = await api_client.get("/services")
            return response["services"]
            
        except APIError as e:
            logger.error("Failed to get available services", error=str(e))
            raise
            
    async def _get_service_appointments(self, service_id: str) -> List[Dict[str, Any]]:
        """Get appointments for a specific service."""
        try:
            response = await api_client.get(f"/services/{service_id}/appointments")
            return response["appointments"]
            
        except APIError as e:
            logger.error(f"Failed to get appointments for service {service_id}", error=str(e))
            raise
            
    async def _process_new_appointment(self, appointment_data: Dict[str, Any]) -> None:
        """Process a new appointment."""
        try:
            # Create appointment object
            appointment = Appointment(
                id=appointment_data["id"],
                service_id=appointment_data["service_id"],
                service_name=appointment_data["service_name"],
                date=datetime.fromisoformat(appointment_data["date"]),
                time=appointment_data["time"],
                location=appointment_data["location"],
                status=appointment_data["status"],
                created_at=datetime.fromisoformat(appointment_data["created_at"]),
                updated_at=datetime.fromisoformat(appointment_data["updated_at"]),
                metadata=appointment_data.get("metadata")
            )
            
            # Store appointment
            self._appointments[appointment.id] = appointment
            
            # Record metrics
            metrics_manager.record_appointment("new", None)
            
            # Create alert
            await alert_manager.create_alert(
                level="info",
                component="appointment_manager",
                message=f"New appointment available: {appointment.service_name} on {appointment.date} at {appointment.time}",
                metadata={
                    "appointment_id": appointment.id,
                    "service_name": appointment.service_name,
                    "date": appointment.date.isoformat(),
                    "time": appointment.time,
                    "location": appointment.location
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process new appointment {appointment_data['id']}", error=str(e))
            raise
            
    async def book_appointment(self, appointment_id: str) -> bool:
        """Book an appointment."""
        try:
            if appointment_id not in self._appointments:
                raise ValueError(f"Appointment not found: {appointment_id}")
                
            # Start timing
            start_time = datetime.utcnow()
            
            # Book appointment through API
            response = await api_client.post(f"/appointments/{appointment_id}/book")
            
            # Update appointment status
            appointment = self._appointments[appointment_id]
            appointment.status = "booked"
            appointment.updated_at = datetime.utcnow()
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics_manager.record_appointment("booked", duration)
            
            # Create alert
            await alert_manager.create_alert(
                level="success",
                component="appointment_manager",
                message=f"Successfully booked appointment: {appointment.service_name} on {appointment.date} at {appointment.time}",
                metadata={
                    "appointment_id": appointment.id,
                    "service_name": appointment.service_name,
                    "date": appointment.date.isoformat(),
                    "time": appointment.time,
                    "location": appointment.location
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to book appointment {appointment_id}", error=str(e))
            await alert_manager.create_alert(
                level="error",
                component="appointment_manager",
                message=f"Failed to book appointment: {str(e)}",
                metadata={"appointment_id": appointment_id}
            )
            return False
            
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get an appointment by ID."""
        return self._appointments.get(appointment_id)
        
    def get_all_appointments(self) -> List[Appointment]:
        """Get all appointments."""
        return list(self._appointments.values())
        
    def get_available_appointments(self) -> List[Appointment]:
        """Get all available appointments."""
        return [
            appointment for appointment in self._appointments.values()
            if appointment.status == "available"
        ]
        
    def get_booked_appointments(self) -> List[Appointment]:
        """Get all booked appointments."""
        return [
            appointment for appointment in self._appointments.values()
            if appointment.status == "booked"
        ]

# Create singleton instance
appointment_manager = AppointmentManager() 