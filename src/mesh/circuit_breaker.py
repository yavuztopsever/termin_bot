"""
Circuit Breaker implementation for handling service failures.
"""

from typing import Dict, Any
import asyncio
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CircuitState:
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered

class CircuitBreaker:
    """Circuit Breaker for handling service failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        """Initialize the Circuit Breaker."""
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        
        self.services: Dict[str, Dict[str, Any]] = {}
        self.running = False
        
    async def start(self):
        """Start the Circuit Breaker."""
        self.running = True
        asyncio.create_task(self._monitor_loop())
        
    async def stop(self):
        """Stop the Circuit Breaker."""
        self.running = False
        
    async def check_service(self, service_name: str) -> bool:
        """Check if service circuit is closed."""
        try:
            if service_name not in self.services:
                self.services[service_name] = {
                    "state": CircuitState.CLOSED,
                    "failures": 0,
                    "last_failure": 0,
                    "last_success": 0
                }
                
            service = self.services[service_name]
            current_time = asyncio.get_event_loop().time()
            
            # Check if circuit is open
            if service["state"] == CircuitState.OPEN:
                # Check if reset timeout has passed
                if current_time - service["last_failure"] > self.reset_timeout:
                    service["state"] = CircuitState.HALF_OPEN
                    service["failures"] = 0
                    logger.info(
                        f"Circuit breaker for {service_name} "
                        f"moved to half-open state"
                    )
                    return True
                return False
                
            # Check if circuit is half-open
            if service["state"] == CircuitState.HALF_OPEN:
                # Check if half-open timeout has passed
                if current_time - service["last_failure"] > self.half_open_timeout:
                    service["state"] = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker for {service_name} "
                        f"moved back to open state"
                    )
                    return False
                return True
                
            # Circuit is closed
            return True
            
        except Exception as e:
            logger.error(f"Error checking service circuit: {str(e)}")
            return False
            
    async def record_failure(self, service_name: str):
        """Record a service failure."""
        try:
            if service_name not in self.services:
                self.services[service_name] = {
                    "state": CircuitState.CLOSED,
                    "failures": 0,
                    "last_failure": 0,
                    "last_success": 0
                }
                
            service = self.services[service_name]
            service["failures"] += 1
            service["last_failure"] = asyncio.get_event_loop().time()
            
            # Check if threshold exceeded
            if service["failures"] >= self.failure_threshold:
                service["state"] = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker for {service_name} "
                    f"opened after {service['failures']} failures"
                )
                
        except Exception as e:
            logger.error(f"Error recording failure: {str(e)}")
            
    async def record_success(self, service_name: str):
        """Record a service success."""
        try:
            if service_name not in self.services:
                return
                
            service = self.services[service_name]
            service["last_success"] = asyncio.get_event_loop().time()
            
            # Reset circuit if half-open
            if service["state"] == CircuitState.HALF_OPEN:
                service["state"] = CircuitState.CLOSED
                service["failures"] = 0
                logger.info(
                    f"Circuit breaker for {service_name} "
                    f"closed after successful request"
                )
                
        except Exception as e:
            logger.error(f"Error recording success: {str(e)}")
            
    async def _monitor_loop(self):
        """Monitor loop for circuit breaker state."""
        while self.running:
            try:
                current_time = asyncio.get_event_loop().time()
                
                for service_name, service in self.services.items():
                    # Check if circuit should be reset
                    if service["state"] == CircuitState.OPEN:
                        if current_time - service["last_failure"] > self.reset_timeout:
                            service["state"] = CircuitState.HALF_OPEN
                            service["failures"] = 0
                            logger.info(
                                f"Circuit breaker for {service_name} "
                                f"moved to half-open state"
                            )
                            
                    # Check if half-open circuit should be closed
                    elif service["state"] == CircuitState.HALF_OPEN:
                        if current_time - service["last_failure"] > self.half_open_timeout:
                            service["state"] = CircuitState.OPEN
                            logger.warning(
                                f"Circuit breaker for {service_name} "
                                f"moved back to open state"
                            )
                            
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                await asyncio.sleep(1) 