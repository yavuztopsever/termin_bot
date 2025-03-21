class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class CacheInitializationError(CacheError):
    """Raised when there is an error initializing the cache manager."""
    pass

class CacheBackendError(CacheError):
    """Raised when there is an error with the cache backend."""
    pass

class CacheKeyError(CacheError):
    """Raised when there is an error with a cache key."""
    pass

class CacheValueError(CacheError):
    """Raised when there is an error with a cache value."""
    pass

class CacheSerializationError(CacheError):
    """Raised when there is an error serializing/deserializing cache values."""
    pass

class CacheStorageError(CacheError):
    """Raised when there is an error storing or retrieving cache values."""
    pass

class CacheExpirationError(CacheError):
    """Raised when there is an error with cache expiration."""
    pass

class CacheSizeError(CacheError):
    """Raised when the cache size limit is exceeded."""
    pass

class CacheTimeoutError(CacheError):
    """Raised when a cache operation times out."""
    pass

class CacheConfigurationError(CacheError):
    """Raised when there is an error with cache configuration."""
    pass

class CacheBackendNotImplementedError(CacheError):
    """Raised when a cache backend method is not implemented."""
    pass

class CacheBackendConnectionError(CacheError):
    """Raised when there is an error connecting to the cache backend."""
    pass

class CacheBackendOperationError(CacheError):
    """Raised when there is an error performing a cache backend operation."""
    pass 