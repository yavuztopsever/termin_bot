from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError

from src.gateway.api_config import APIConfig
from src.utils.logger import setup_logger
from src.exceptions import (
    APIRequestError,
    RateLimitExceeded,
    ConfigurationError,
    AppointmentError
)
from src.models import Appointment, Service, Location
from src.database.repositories import (
    appointment_repository,
    service_repository,
    location_repository
)

logger = setup_logger(__name__)

class AppointmentService:
    """Service for handling appointment-related operations."""
    
    def __init__(self):
        """Initialize the appointment service."""
        self.api_config = APIConfig()
        self._session: Optional[ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        try:
            # Initialize API configuration
            await self.api_config.initialize()
            
            # Create aiohttp session
            self._session = ClientSession()
            
        except Exception as e:
            logger.error("Failed to initialize AppointmentService", error=str(e))
            raise ConfigurationError(f"Initialization failed: {str(e)}")
            
    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
        await self.api_config.close()
        
    async def check_availability(
        self,
        service_id: str,
        location_id: Optional[str] = None,
        date_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Check availability for appointments."""
        try:
            # Get request configuration
            request_config = await self.api_config.get_check_availability_request(
                service_id=service_id,
                location_id=location_id,
                date_preferences=date_preferences
            )
            
            # Make the request
            async with self._session.post(
                request_config["url"],
                headers=request_config["headers"],
                json=request_config["body"]
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIRequestError(
                        f"Failed to check availability: {error_text}"
                    )
                    
                response_data = await response.json()
                
            # Parse and validate response
            available_slots = self.api_config.parse_availability_response(response_data)
            
            # Log the results
            logger.info(
                "Checked appointment availability",
                service_id=service_id,
                location_id=location_id,
                available_slots=len(available_slots)
            )
            
            return available_slots
            
        except ClientError as e:
            logger.error(
                "Network error checking availability",
                error=str(e),
                service_id=service_id,
                location_id=location_id
            )
            raise APIRequestError(f"Network error: {str(e)}")
            
        except Exception as e:
            logger.error(
                "Error checking availability",
                error=str(e),
                service_id=service_id,
                location_id=location_id
            )
            raise AppointmentError(f"Failed to check availability: {str(e)}")
            
    async def get_available_days(
        self,
        service_id: str,
        office_id: str,
        start_date: str,
        end_date: str,
        service_count: int = 1
    ) -> Dict[str, Any]:
        """Get available days for appointments."""
        try:
            return await self.api_config.get_available_days(
                service_id=service_id,
                office_id=office_id,
                start_date=start_date,
                end_date=end_date,
                service_count=service_count
            )
            
        except Exception as e:
            logger.error(
                "Error getting available days",
                error=str(e),
                service_id=service_id,
                office_id=office_id
            )
            raise AppointmentError(f"Failed to get available days: {str(e)}")
            
    async def book_appointment(
        self,
        service_id: str,
        office_id: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """Book an appointment."""
        try:
            # Get request configuration
            request_config = await self.api_config.get_book_appointment_request({
                "serviceID": service_id,
                "officeID": office_id,
                "date": date,
                "time": time
            })
            
            # Make the request
            async with self._session.post(
                request_config["url"],
                headers=request_config["headers"],
                json=request_config["body"]
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIRequestError(
                        f"Failed to book appointment: {error_text}"
                    )
                    
                response_data = await response.json()
                
            # Parse and validate response
            booking_result = self.api_config.parse_booking_response(response_data)
            
            # Create appointment record
            appointment = Appointment(
                service_id=service_id,
                office_id=office_id,
                date=date,
                time=time,
                booking_id=booking_result.get("booking_id"),
                status="confirmed",
                created_at=datetime.utcnow()
            )
            
            # Save to database
            await appointment_repository.create(appointment)
            
            # Log the booking
            logger.info(
                "Booked appointment",
                service_id=service_id,
                office_id=office_id,
                date=date,
                time=time,
                booking_id=booking_result.get("booking_id")
            )
            
            return booking_result
            
        except ClientError as e:
            logger.error(
                "Network error booking appointment",
                error=str(e),
                service_id=service_id,
                office_id=office_id
            )
            raise APIRequestError(f"Network error: {str(e)}")
            
        except Exception as e:
            logger.error(
                "Error booking appointment",
                error=str(e),
                service_id=service_id,
                office_id=office_id
            )
            raise AppointmentError(f"Failed to book appointment: {str(e)}")
            
    async def get_service_details(self, service_id: str) -> Service:
        """Get service details by ID."""
        try:
            service = await service_repository.get_by_id(service_id)
            if not service:
                raise AppointmentError(f"Service not found: {service_id}")
            return service
            
        except Exception as e:
            logger.error(
                "Error getting service details",
                error=str(e),
                service_id=service_id
            )
            raise AppointmentError(f"Failed to get service details: {str(e)}")
            
    async def get_location_details(self, location_id: str) -> Location:
        """Get location details by ID."""
        try:
            location = await location_repository.get_by_id(location_id)
            if not location:
                raise AppointmentError(f"Location not found: {location_id}")
            return location
            
        except Exception as e:
            logger.error(
                "Error getting location details",
                error=str(e),
                location_id=location_id
            )
            raise AppointmentError(f"Failed to get location details: {str(e)}")
            
    async def get_appointment_status(self, booking_id: str) -> Dict[str, Any]:
        """Get the status of a booked appointment."""
        try:
            appointment = await appointment_repository.get_by_booking_id(booking_id)
            if not appointment:
                raise AppointmentError(f"Appointment not found: {booking_id}")
                
            return {
                "booking_id": appointment.booking_id,
                "status": appointment.status,
                "date": appointment.date,
                "time": appointment.time,
                "service_id": appointment.service_id,
                "office_id": appointment.office_id,
                "created_at": appointment.created_at
            }
            
        except Exception as e:
            logger.error(
                "Error getting appointment status",
                error=str(e),
                booking_id=booking_id
            )
            raise AppointmentError(f"Failed to get appointment status: {str(e)}")
            
    async def cancel_appointment(self, booking_id: str) -> bool:
        """Cancel a booked appointment."""
        try:
            appointment = await appointment_repository.get_by_booking_id(booking_id)
            if not appointment:
                raise AppointmentError(f"Appointment not found: {booking_id}")
                
            # Update appointment status
            appointment.status = "cancelled"
            await appointment_repository.update(appointment)
            
            # Log the cancellation
            logger.info(
                "Cancelled appointment",
                booking_id=booking_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error cancelling appointment",
                error=str(e),
                booking_id=booking_id
            )
            raise AppointmentError(f"Failed to cancel appointment: {str(e)}")

# Create singleton instance
appointment_service = AppointmentService() 