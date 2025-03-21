"""Retry utilities for API requests."""

import asyncio
import random
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast
from functools import wraps

from src.utils.logger import setup_logger, get_correlation_id, log_error

logger = setup_logger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.1,
        retry_on_exceptions: tuple = (Exception,),
        retry_on_status_codes: tuple = (429, 500, 502, 503, 504)
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add jitter to delay
            jitter_factor: Factor for jitter calculation (0.0-1.0)
            retry_on_exceptions: Tuple of exceptions to retry on
            retry_on_status_codes: Tuple of HTTP status codes to retry on
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.retry_on_exceptions = retry_on_exceptions
        self.retry_on_status_codes = retry_on_status_codes
        
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = min(
            self.max_delay,
            self.base_delay * (self.backoff_factor ** attempt)
        )
        
        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)
            
        return max(0, delay)  # Ensure delay is not negative

def async_retry(
    retry_config: Optional[RetryConfig] = None,
    retry_on_exceptions: Optional[tuple] = None,
    retry_on_status_codes: Optional[tuple] = None
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        retry_config: RetryConfig instance
        retry_on_exceptions: Tuple of exceptions to retry on (overrides config)
        retry_on_status_codes: Tuple of HTTP status codes to retry on (overrides config)
        
    Returns:
        Decorated function
    """
    config = retry_config or RetryConfig()
    
    if retry_on_exceptions is not None:
        config.retry_on_exceptions = retry_on_exceptions
        
    if retry_on_status_codes is not None:
        config.retry_on_status_codes = retry_on_status_codes
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            correlation_id = get_correlation_id()
            attempt = 0
            last_exception = None
            
            while attempt <= config.max_retries:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Check if result is a response with status code
                    status_code = getattr(result, 'status', None)
                    if status_code is not None and status_code in config.retry_on_status_codes:
                        if attempt < config.max_retries:
                            delay = config.calculate_delay(attempt)
                            logger.warning(
                                f"Retrying due to status code {status_code}",
                                attempt=attempt + 1,
                                max_retries=config.max_retries,
                                delay=delay,
                                request_id=correlation_id
                            )
                            await asyncio.sleep(delay)
                            attempt += 1
                            continue
                        else:
                            # Max retries reached, return the response anyway
                            return result
                    
                    # Success
                    return result
                    
                except config.retry_on_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Retrying due to exception: {str(e)}",
                            attempt=attempt + 1,
                            max_retries=config.max_retries,
                            delay=delay,
                            error=str(e),
                            request_id=correlation_id
                        )
                        await asyncio.sleep(delay)
                        attempt += 1
                    else:
                        # Max retries reached, re-raise the exception
                        log_error(
                            logger,
                            last_exception,
                            context={
                                "function": func.__name__,
                                "args": args,
                                "kwargs": kwargs,
                                "attempts": attempt
                            },
                            request_id=correlation_id
                        )
                        raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
            # This should also never be reached
            raise RuntimeError("Unexpected error in retry logic")
            
        return wrapper
    
    return decorator

async def retry_async_call(
    func: Callable[..., Any],
    *args: Any,
    retry_config: Optional[RetryConfig] = None,
    **kwargs: Any
) -> Any:
    """
    Retry an async function call with exponential backoff.
    
    Args:
        func: Async function to call
        *args: Arguments to pass to the function
        retry_config: RetryConfig instance
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call
    """
    config = retry_config or RetryConfig()
    correlation_id = get_correlation_id()
    
    attempt = 0
    last_exception = None
    
    while attempt <= config.max_retries:
        try:
            result = await func(*args, **kwargs)
            
            # Check if result is a response with status code
            status_code = getattr(result, 'status', None)
            if status_code is not None and status_code in config.retry_on_status_codes:
                if attempt < config.max_retries:
                    delay = config.calculate_delay(attempt)
                    logger.warning(
                        f"Retrying due to status code {status_code}",
                        attempt=attempt + 1,
                        max_retries=config.max_retries,
                        delay=delay,
                        request_id=correlation_id
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    # Max retries reached, return the response anyway
                    return result
            
            # Success
            return result
            
        except config.retry_on_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"Retrying due to exception: {str(e)}",
                    attempt=attempt + 1,
                    max_retries=config.max_retries,
                    delay=delay,
                    error=str(e),
                    request_id=correlation_id
                )
                await asyncio.sleep(delay)
                attempt += 1
            else:
                # Max retries reached, re-raise the exception
                log_error(
                    logger,
                    last_exception,
                    context={
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "attempts": attempt
                    },
                    request_id=correlation_id
                )
                raise
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
        
    # This should also never be reached
    raise RuntimeError("Unexpected error in retry logic")
