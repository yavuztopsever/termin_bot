class NotificationError(Exception):
    """Base exception for notification-related errors."""
    pass

class NotificationInitializationError(NotificationError):
    """Raised when there's an error initializing the notification manager."""
    pass

class NotificationSendError(NotificationError):
    """Raised when there's an error sending a notification."""
    pass

class NotificationChannelError(NotificationError):
    """Raised when there's an error with a notification channel."""
    pass

class NotificationValidationError(NotificationError):
    """Raised when notification data validation fails."""
    pass

class NotificationStorageError(NotificationError):
    """Raised when there's an error storing or retrieving notifications."""
    pass

class NotificationProcessingError(NotificationError):
    """Raised when there's an error processing a notification."""
    pass

class NotificationQueueError(NotificationError):
    """Raised when there's an error with the notification queue."""
    pass

class NotificationTimeoutError(NotificationError):
    """Raised when a notification operation times out."""
    pass

class NotificationRateLimitError(NotificationError):
    """Raised when notification rate limit is exceeded."""
    pass

class NotificationTemplateError(NotificationError):
    """Raised when there's an error with notification templates."""
    pass

class NotificationRecipientError(NotificationError):
    """Raised when there's an error with notification recipients."""
    pass

class NotificationConfigurationError(NotificationError):
    """Raised when there's an error with notification configuration."""
    pass 