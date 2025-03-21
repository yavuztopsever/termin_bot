class AppointmentError(Exception):
    """Base exception for appointment-related errors."""
    pass

class AppointmentNotFoundError(AppointmentError):
    """Raised when an appointment is not found."""
    pass

class AppointmentAlreadyBookedError(AppointmentError):
    """Raised when trying to book an already booked appointment."""
    pass

class AppointmentInvalidError(AppointmentError):
    """Raised when an appointment is invalid."""
    pass

class AppointmentServiceError(AppointmentError):
    """Raised when there's an error with the appointment service."""
    pass

class AppointmentValidationError(AppointmentError):
    """Raised when appointment data validation fails."""
    pass

class AppointmentStorageError(AppointmentError):
    """Raised when there's an error storing or retrieving appointments."""
    pass

class AppointmentInitializationError(AppointmentError):
    """Raised when there's an error initializing the appointment manager."""
    pass

class AppointmentProcessingError(AppointmentError):
    """Raised when there's an error processing an appointment."""
    pass 