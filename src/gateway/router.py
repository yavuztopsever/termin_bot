"""
Router implementation for handling service-specific routes.
"""

from fastapi import APIRouter
from ..services.auth import AuthService
from ..services.appointment import AppointmentService
from ..services.notification import NotificationService
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Router:
    """Router for handling service-specific routes."""
    
    def __init__(self):
        """Initialize the router with service instances."""
        self.auth_service = AuthService()
        self.appointment_service = AppointmentService()
        self.notification_service = NotificationService()
        
        # Initialize routers
        self.auth_router = self._create_auth_router()
        self.appointment_router = self._create_appointment_router()
        self.notification_router = self._create_notification_router()
        
    def _create_auth_router(self) -> APIRouter:
        """Create authentication router."""
        router = APIRouter()
        
        @router.post("/login")
        async def login(username: str, password: str):
            """Handle user login."""
            return await self.auth_service.login(username, password)
            
        @router.post("/logout")
        async def logout(token: str):
            """Handle user logout."""
            return await self.auth_service.logout(token)
            
        @router.post("/refresh")
        async def refresh_token(token: str):
            """Handle token refresh."""
            return await self.auth_service.refresh_token(token)
            
        return router
        
    def _create_appointment_router(self) -> APIRouter:
        """Create appointment router."""
        router = APIRouter()
        
        @router.get("/check")
        async def check_appointments(service_id: str, location_id: str):
            """Check available appointments."""
            return await self.appointment_service.check_availability(
                service_id,
                location_id
            )
            
        @router.post("/book")
        async def book_appointment(
            service_id: str,
            location_id: str,
            date: str,
            time: str
        ):
            """Book an appointment."""
            return await self.appointment_service.book_appointment(
                service_id,
                location_id,
                date,
                time
            )
            
        @router.get("/status/{appointment_id}")
        async def get_appointment_status(appointment_id: str):
            """Get appointment status."""
            return await self.appointment_service.get_status(appointment_id)
            
        return router
        
    def _create_notification_router(self) -> APIRouter:
        """Create notification router."""
        router = APIRouter()
        
        @router.post("/send")
        async def send_notification(
            user_id: str,
            message: str,
            notification_type: str
        ):
            """Send a notification."""
            return await self.notification_service.send_notification(
                user_id,
                message,
                notification_type
            )
            
        @router.get("/status/{notification_id}")
        async def get_notification_status(notification_id: str):
            """Get notification status."""
            return await self.notification_service.get_status(notification_id)
            
        return router 