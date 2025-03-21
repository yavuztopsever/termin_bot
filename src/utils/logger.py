"""Logging utilities."""

import logging
import logging.handlers
import os
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import threading
from contextvars import ContextVar

from src.config.config import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)
from src.utils.json_encoder import CustomJSONEncoder

# Context variable to store correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one."""
    current_id = correlation_id.get()
    if not current_id:
        current_id = str(uuid.uuid4())
        correlation_id.set(current_id)
    return current_id

def set_correlation_id(new_id: str) -> None:
    """Set a new correlation ID."""
    correlation_id.set(new_id)

class StructuredLogger(logging.Logger):
    """Custom logger that supports structured logging."""

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        """Log with structured data."""
        if extra is None:
            extra = {}
        if kwargs:
            extra.update(kwargs)

        # Add correlation ID to log data
        log_data = {
            "message": msg,
            "log_timestamp": datetime.utcnow().isoformat(),
            "process_id": os.getpid(),
            "thread_name": threading.current_thread().name,
            "correlation_id": get_correlation_id()
        }

        if extra:
            log_data.update(extra)

        json_msg = json.dumps(log_data, cls=CustomJSONEncoder)
        super()._log(level, json_msg, args, exc_info, extra, stack_info)

def setup_logger(name: str) -> logging.Logger:
    """Set up logger with structured logging."""
    # Register custom logger class
    logging.setLoggerClass(StructuredLogger)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    return logger

class JsonFormatter(logging.Formatter):
    """JSON formatter for logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }

        if hasattr(record, "error"):
            log_data["error"] = str(record.error)

        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data, cls=CustomJSONEncoder)

# Create default logger instance
logger = setup_logger(__name__)

def log_api_request(
    logger: logging.Logger,
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        headers: Request headers
        body: Request body
        request_id: Optional request ID, if not provided a new correlation ID will be used
        
    Returns:
        The correlation ID used for this request
    """
    # Generate or use provided request ID
    req_id = request_id or get_correlation_id()
    
    # Set correlation ID for this context
    set_correlation_id(req_id)
    
    # Add X-Request-ID header if not present
    safe_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
    if "X-Request-ID" not in safe_headers:
        safe_headers["X-Request-ID"] = req_id
    
    logger.debug(
        "API Request",
        method=method,
        url=url,
        headers=safe_headers,
        body=body,
        request_id=req_id,
        **kwargs
    )
    
    return req_id
    
def log_api_response(
    logger: logging.Logger,
    status_code: int,
    response_body: Any,
    elapsed: float,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log API response details.
    
    Args:
        logger: Logger instance
        status_code: HTTP status code
        response_body: Response body
        elapsed: Request duration in seconds
        request_id: Optional request ID to correlate with the request
    """
    # Use provided request ID or get current correlation ID
    req_id = request_id or get_correlation_id()
    
    logger.debug(
        "API Response",
        status_code=status_code,
        response_body=response_body,
        elapsed_ms=int(elapsed * 1000),
        request_id=req_id,
        **kwargs
    )
    
def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log error details with context.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context information
        request_id: Optional request ID to correlate with the request
    """
    # Use provided request ID or get current correlation ID
    req_id = request_id or get_correlation_id()
    
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "request_id": req_id,
        "stack_trace": getattr(error, "__traceback__", None)
    }
    error_details.update(kwargs)
    
    logger.error(error_details)
    
def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Any,
    tags: Optional[Dict[str, str]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log metric data.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        tags: Optional tags for the metric
        request_id: Optional request ID to correlate with the request
    """
    # Use provided request ID or get current correlation ID
    req_id = request_id or get_correlation_id()
    
    metric_data = {
        "metric": metric_name,
        "value": value,
        "tags": tags or {},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": req_id
    }
    metric_data.update(kwargs)
    
    logger.info(metric_data)
