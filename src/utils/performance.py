"""Performance optimization utilities."""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime, timedelta
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from cachetools import TTLCache, LRUCache

from src.utils.logger import setup_logger
from src.monitoring.metrics import track_function_performance, metrics_manager

logger = setup_logger(__name__)

T = TypeVar('T')  # Generic type for function return values

class RequestsOptimizer:
    """Optimizes HTTP requests with connection pooling and retries."""
    
    def __init__(
        self,
        pool_connections: int = 100,
        pool_maxsize: int = 100,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (500, 502, 504)
    ):
        """
        Initialize request optimizer.
        
        Args:
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum size of each connection pool
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor between retries
            status_forcelist: Status codes that trigger a retry
        """
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )
        
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def request(self, *args, **kwargs) -> requests.Response:
        """Make an HTTP request using the optimized session."""
        return self.session.request(*args, **kwargs)
        
# Global request optimizer instance
request_optimizer = RequestsOptimizer()

class CacheManager:
    """Manages different types of caches."""
    
    def __init__(
        self,
        ttl_seconds: int = 300,  # 5 minutes
        max_size: int = 1000
    ):
        """
        Initialize cache manager.
        
        Args:
            ttl_seconds: Time-to-live for TTL cache entries
            max_size: Maximum size for LRU cache
        """
        self.ttl_cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.lru_cache = LRUCache(maxsize=max_size)
        self._lock = threading.Lock()
        
    def get_ttl(self, key: str) -> Optional[Any]:
        """Get value from TTL cache."""
        with self._lock:
            return self.ttl_cache.get(key)
            
    def set_ttl(self, key: str, value: Any) -> None:
        """Set value in TTL cache."""
        with self._lock:
            self.ttl_cache[key] = value
            
    def get_lru(self, key: str) -> Optional[Any]:
        """Get value from LRU cache."""
        with self._lock:
            return self.lru_cache.get(key)
            
    def set_lru(self, key: str, value: Any) -> None:
        """Set value in LRU cache."""
        with self._lock:
            self.lru_cache[key] = value
            
# Global cache manager instance
cache_manager = CacheManager()

class ThreadPoolManager:
    """Manages thread pools for concurrent operations."""
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize thread pool manager.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self.active_tasks = 0
        
    def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """Submit a task to the thread pool."""
        with self._lock:
            self.active_tasks += 1
            metrics_manager.update_active_tasks(self.active_tasks)
            
        try:
            future = self.executor.submit(fn, *args, **kwargs)
            return future.result()
        finally:
            with self._lock:
                self.active_tasks -= 1
                metrics_manager.update_active_tasks(self.active_tasks)
                
# Global thread pool manager instance
thread_pool = ThreadPoolManager()

def cache_result(
    ttl_seconds: Optional[int] = None,
    use_lru: bool = False
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time-to-live for cached results (None for LRU)
        use_lru: Whether to use LRU cache instead of TTL cache
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            if use_lru:
                result = cache_manager.get_lru(key)
            else:
                result = cache_manager.get_ttl(key)
                
            if result is not None:
                return result
                
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in cache
            if use_lru:
                cache_manager.set_lru(key, result)
            else:
                cache_manager.set_ttl(key, result)
                
            return result
        return wrapper
    return decorator

def run_in_threadpool(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to run a function in the thread pool."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        return thread_pool.submit(func, *args, **kwargs)
    return wrapper

@track_function_performance(func_name="optimize_batch_requests")
def optimize_batch_requests(
    requests_data: list[Dict[str, Any]],
    max_concurrent: int = 5
) -> list[Any]:
    """
    Optimize batch requests using connection pooling and concurrency.
    
    Args:
        requests_data: List of request data dictionaries
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        List of responses
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = []
        for data in requests_data:
            future = executor.submit(
                request_optimizer.request,
                **data
            )
            futures.append(future)
            
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                results.append(None)
                
    return results

# Example usage:
"""
@cache_result(ttl_seconds=300)
def get_available_slots(service_id: str) -> list:
    # Implementation
    pass

@run_in_threadpool
def process_booking(booking_data: dict) -> bool:
    # Implementation
    pass

# Batch request optimization
requests_data = [
    {"method": "GET", "url": "..."},
    {"method": "GET", "url": "..."}
]
responses = optimize_batch_requests(requests_data)
""" 