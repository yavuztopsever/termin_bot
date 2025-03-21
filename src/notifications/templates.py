from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class NotificationTemplate:
    """Base class for notification templates."""
    subject: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class AppointmentTemplates:
    """Templates for appointment-related notifications."""
    
    @staticmethod
    def appointment_available(
        service_name: str,
        date: datetime,
        time: str,
        location: str,
        booking_url: str
    ) -> NotificationTemplate:
        """Template for when an appointment becomes available."""
        return NotificationTemplate(
            subject=f"Appointment Available: {service_name}",
            message=(
                f"A new appointment is available for {service_name}!\n\n"
                f"Date: {date.strftime('%Y-%m-%d')}\n"
                f"Time: {time}\n"
                f"Location: {location}\n\n"
                f"Click here to book: {booking_url}"
            ),
            metadata={
                "service_name": service_name,
                "date": date.isoformat(),
                "time": time,
                "location": location,
                "booking_url": booking_url
            }
        )
        
    @staticmethod
    def appointment_booked(
        service_name: str,
        date: datetime,
        time: str,
        location: str,
        booking_id: str
    ) -> NotificationTemplate:
        """Template for when an appointment is booked."""
        return NotificationTemplate(
            subject=f"Appointment Booked: {service_name}",
            message=(
                f"Your appointment has been successfully booked!\n\n"
                f"Service: {service_name}\n"
                f"Date: {date.strftime('%Y-%m-%d')}\n"
                f"Time: {time}\n"
                f"Location: {location}\n"
                f"Booking ID: {booking_id}"
            ),
            metadata={
                "service_name": service_name,
                "date": date.isoformat(),
                "time": time,
                "location": location,
                "booking_id": booking_id
            }
        )
        
    @staticmethod
    def appointment_cancelled(
        service_name: str,
        date: datetime,
        time: str,
        reason: Optional[str] = None
    ) -> NotificationTemplate:
        """Template for when an appointment is cancelled."""
        return NotificationTemplate(
            subject=f"Appointment Cancelled: {service_name}",
            message=(
                f"Your appointment has been cancelled.\n\n"
                f"Service: {service_name}\n"
                f"Date: {date.strftime('%Y-%m-%d')}\n"
                f"Time: {time}\n"
                f"Reason: {reason or 'No reason provided'}"
            ),
            metadata={
                "service_name": service_name,
                "date": date.isoformat(),
                "time": time,
                "reason": reason
            }
        )
        
    @staticmethod
    def appointment_reminder(
        service_name: str,
        date: datetime,
        time: str,
        location: str,
        booking_id: str
    ) -> NotificationTemplate:
        """Template for appointment reminders."""
        return NotificationTemplate(
            subject=f"Appointment Reminder: {service_name}",
            message=(
                f"This is a reminder for your upcoming appointment.\n\n"
                f"Service: {service_name}\n"
                f"Date: {date.strftime('%Y-%m-%d')}\n"
                f"Time: {time}\n"
                f"Location: {location}\n"
                f"Booking ID: {booking_id}"
            ),
            metadata={
                "service_name": service_name,
                "date": date.isoformat(),
                "time": time,
                "location": location,
                "booking_id": booking_id
            }
        )

class SystemTemplates:
    """Templates for system-related notifications."""
    
    @staticmethod
    def system_error(
        component: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> NotificationTemplate:
        """Template for system errors."""
        return NotificationTemplate(
            subject=f"System Error: {component}",
            message=(
                f"A system error has occurred in the {component} component.\n\n"
                f"Error: {error}\n"
                f"Details: {details or 'No additional details'}"
            ),
            metadata={
                "component": component,
                "error": error,
                "details": details
            }
        )
        
    @staticmethod
    def system_warning(
        component: str,
        warning: str,
        details: Optional[Dict[str, Any]] = None
    ) -> NotificationTemplate:
        """Template for system warnings."""
        return NotificationTemplate(
            subject=f"System Warning: {component}",
            message=(
                f"A system warning has been detected in the {component} component.\n\n"
                f"Warning: {warning}\n"
                f"Details: {details or 'No additional details'}"
            ),
            metadata={
                "component": component,
                "warning": warning,
                "details": details
            }
        )
        
    @staticmethod
    def system_status(
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> NotificationTemplate:
        """Template for system status updates."""
        return NotificationTemplate(
            subject=f"System Status: {component}",
            message=(
                f"The status of the {component} component has changed.\n\n"
                f"Status: {status}\n"
                f"Details: {details or 'No additional details'}"
            ),
            metadata={
                "component": component,
                "status": status,
                "details": details
            }
        )

class UserTemplates:
    """Templates for user-related notifications."""
    
    @staticmethod
    def user_registered(
        user_id: str,
        email: str,
        verification_url: Optional[str] = None
    ) -> NotificationTemplate:
        """Template for user registration."""
        return NotificationTemplate(
            subject="Welcome to Termin Bot!",
            message=(
                f"Thank you for registering with Termin Bot!\n\n"
                f"Your account has been created successfully.\n"
                f"User ID: {user_id}\n"
                f"Email: {email}\n\n"
                f"{f'Click here to verify your email: {verification_url}' if verification_url else ''}"
            ),
            metadata={
                "user_id": user_id,
                "email": email,
                "verification_url": verification_url
            }
        )
        
    @staticmethod
    def user_verified(
        user_id: str,
        email: str
    ) -> NotificationTemplate:
        """Template for user email verification."""
        return NotificationTemplate(
            subject="Email Verified - Termin Bot",
            message=(
                f"Your email has been verified successfully!\n\n"
                f"User ID: {user_id}\n"
                f"Email: {email}\n\n"
                f"You can now use all features of Termin Bot."
            ),
            metadata={
                "user_id": user_id,
                "email": email
            }
        )
        
    @staticmethod
    def user_password_reset(
        user_id: str,
        reset_url: str,
        expiry_hours: int
    ) -> NotificationTemplate:
        """Template for password reset requests."""
        return NotificationTemplate(
            subject="Password Reset Request - Termin Bot",
            message=(
                f"You have requested to reset your password.\n\n"
                f"Click the link below to reset your password. "
                f"This link will expire in {expiry_hours} hours.\n\n"
                f"Reset Link: {reset_url}\n\n"
                f"If you did not request this reset, please ignore this email."
            ),
            metadata={
                "user_id": user_id,
                "reset_url": reset_url,
                "expiry_hours": expiry_hours
            }
        ) 