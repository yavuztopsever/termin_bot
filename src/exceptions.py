"""Custom exceptions for the application."""

class BaseError(Exception):
    """Base exception class for the application."""
    pass

class ConfigurationError(BaseError):
    """Raised when there is an error with configuration loading or validation."""
    pass

class RateLimitExceeded(BaseError):
    """Raised when API rate limit is exceeded."""
    pass

class APIRequestError(BaseError):
    """Raised when there is an error constructing or sending API requests."""
    pass

class CaptchaError(BaseError):
    """Raised when there is an error with captcha solving or verification."""
    pass

class DatabaseError(BaseError):
    """Raised when there is an error with database operations."""
    pass

class BookingError(BaseError):
    """Raised when there is an error during appointment booking."""
    pass

class ValidationError(BaseError):
    """Raised when there is an error validating input data."""
    pass

class AuthenticationError(BaseError):
    """Raised when there is an error with authentication."""
    pass

class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    pass
