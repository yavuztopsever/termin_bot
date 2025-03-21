from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import json
import time

from src.config.config import config
from src.utils.logger import setup_logger
from src.monitoring.exceptions import (
    HealthCheckError,
    HealthCheckInitializationError,
    HealthCheckExecutionError,
    ComponentHealthError,
    HealthCheckTimeoutError,
    HealthCheckRetryError
)
from src.monitoring.manager import monitoring_manager
from src.monitoring.health_config import HealthCheckConfig, DEFAULT_CONFIG, ENVIRONMENT_CONFIGS

logger = setup_logger(__name__)

@dataclass
class HealthCheck:
    """Represents a health check."""
    name: str
    component: str
    check_func: callable
    interval: timedelta
    timeout: timedelta
    retries: int
    retry_delay: timedelta
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class HealthStatus:
    """Represents the health status of a component."""
    component: str
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthCheckManager:
    """Manager for component health checks."""
    
    def __init__(self):
        """Initialize the health check manager."""
        self._initialized = False
        self._health_checks: Dict[str, HealthCheck] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        self._check_tasks: Dict[str, asyncio.Task] = {}
        self._config: Optional[HealthCheckConfig] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self, environment: str = "development") -> None:
        """Initialize the health check manager.
        
        Args:
            environment: Environment to use for configuration
        """
        try:
            # Load configuration
            self._config = ENVIRONMENT_CONFIGS.get(environment, DEFAULT_CONFIG)
            
            if not self._config.enabled:
                logger.info("Health checks are disabled")
                return
                
            # Register default health checks
            await self._register_default_checks()
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_old_status())
            
            self._initialized = True
            logger.info("Health check manager initialized")
            
            # Record initialization metric
            monitoring_manager.record_metric(
                name="health_check_manager_initialized",
                value=1
            )
            
        except Exception as e:
            logger.error("Failed to initialize health check manager", error=str(e))
            monitoring_manager.record_metric(
                name="health_check_manager_initialization_error",
                value=1
            )
            raise HealthCheckInitializationError(f"Failed to initialize health check manager: {str(e)}")
            
    async def _register_default_checks(self) -> None:
        """Register default health checks."""
        # Database health check
        if self._config.database_check["enabled"]:
            await self.register_check(
                name="database",
                component="database",
                check_func=self._check_database,
                interval=self._config.database_check["interval"],
                timeout=self._config.database_check["timeout"],
                retries=self._config.database_check["retries"],
                retry_delay=self._config.database_check["retry_delay"],
                metadata={"checks": self._config.database_check}
            )
        
        # API health check
        if self._config.api_check["enabled"]:
            await self.register_check(
                name="api",
                component="api",
                check_func=self._check_api,
                interval=self._config.api_check["interval"],
                timeout=self._config.api_check["timeout"],
                retries=self._config.api_check["retries"],
                retry_delay=self._config.api_check["retry_delay"],
                metadata={"checks": self._config.api_check}
            )
        
        # Cache health check
        if self._config.cache_check["enabled"]:
            await self.register_check(
                name="cache",
                component="cache",
                check_func=self._check_cache,
                interval=self._config.cache_check["interval"],
                timeout=self._config.cache_check["timeout"],
                retries=self._config.cache_check["retries"],
                retry_delay=self._config.cache_check["retry_delay"],
                metadata={"checks": self._config.cache_check}
            )
            
    async def _cleanup_old_status(self) -> None:
        """Clean up old health status records."""
        while self._initialized:
            try:
                cutoff = datetime.utcnow() - self._config.status_retention
                
                # Remove old status records
                self._health_status = {
                    component: status
                    for component, status in self._health_status.items()
                    if status.timestamp > cutoff
                }
                
                await asyncio.sleep(self._config.cleanup_interval.total_seconds())
                
            except Exception as e:
                logger.error("Error cleaning up old status records", error=str(e))
                await asyncio.sleep(self._config.cleanup_interval.total_seconds())
                
    async def register_check(
        self,
        name: str,
        component: str,
        check_func: callable,
        interval: timedelta,
        timeout: timedelta,
        retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=1),
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a health check.
        
        Args:
            name: Name of the health check
            component: Component to check
            check_func: Function to perform the check
            interval: Interval between checks
            timeout: Timeout for each check
            retries: Number of retries on failure
            retry_delay: Delay between retries
            metadata: Optional metadata for the check
        """
        try:
            if not self._initialized:
                raise RuntimeError("Health check manager not initialized")
                
            # Create health check
            health_check = HealthCheck(
                name=name,
                component=component,
                check_func=check_func,
                interval=interval,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
                metadata=metadata
            )
            
            # Add to health checks
            self._health_checks[name] = health_check
            
            # Start check task
            self._check_tasks[name] = asyncio.create_task(
                self._run_check(name, health_check)
            )
            
            logger.info(f"Registered health check: {name}")
            
        except Exception as e:
            logger.error(f"Failed to register health check: {name}", error=str(e))
            raise HealthCheckError(f"Failed to register health check: {str(e)}")
            
    async def _run_check(self, name: str, health_check: HealthCheck) -> None:
        """Run a health check periodically.
        
        Args:
            name: Name of the health check
            health_check: Health check to run
        """
        while self._initialized:
            try:
                # Run check with timeout
                async with asyncio.timeout(health_check.timeout.total_seconds()):
                    await self._execute_check(name, health_check)
                    
                # Wait for next interval
                await asyncio.sleep(health_check.interval.total_seconds())
                
            except asyncio.TimeoutError:
                logger.error(f"Health check timed out: {name}")
                await self._update_status(
                    component=health_check.component,
                    status="error",
                    error=f"Health check timed out after {health_check.timeout}"
                )
                await asyncio.sleep(health_check.interval.total_seconds())
                
            except Exception as e:
                logger.error(f"Error running health check: {name}", error=str(e))
                await self._update_status(
                    component=health_check.component,
                    status="error",
                    error=str(e)
                )
                await asyncio.sleep(health_check.interval.total_seconds())
                
    async def _execute_check(self, name: str, health_check: HealthCheck) -> None:
        """Execute a health check with retries.
        
        Args:
            name: Name of the health check
            health_check: Health check to execute
        """
        for attempt in range(health_check.retries):
            try:
                # Run check
                result = await health_check.check_func()
                
                # Update status
                await self._update_status(
                    component=health_check.component,
                    status="healthy",
                    details=result
                )
                
                return
                
            except Exception as e:
                if attempt == health_check.retries - 1:
                    raise HealthCheckRetryError(f"Health check failed after {health_check.retries} attempts: {str(e)}")
                    
                logger.warning(f"Health check attempt {attempt + 1} failed: {name}", error=str(e))
                await asyncio.sleep(health_check.retry_delay.total_seconds())
                
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # TODO: Implement database health check
            return {"status": "healthy"}
            
        except Exception as e:
            raise ComponentHealthError(f"Database health check failed: {str(e)}")
            
    async def _check_api(self) -> Dict[str, Any]:
        """Check API health."""
        try:
            # TODO: Implement API health check
            return {"status": "healthy"}
            
        except Exception as e:
            raise ComponentHealthError(f"API health check failed: {str(e)}")
            
    async def _check_cache(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            # TODO: Implement cache health check
            return {"status": "healthy"}
            
        except Exception as e:
            raise ComponentHealthError(f"Cache health check failed: {str(e)}")
            
    async def _update_status(
        self,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Update component health status.
        
        Args:
            component: Component name
            status: Health status
            details: Optional status details
            error: Optional error message
        """
        try:
            # Get previous status
            prev_status = self._health_status.get(component)
            prev_status_value = prev_status.status if prev_status else None
            
            # Create status
            health_status = HealthStatus(
                component=component,
                status=status,
                timestamp=datetime.utcnow(),
                details=details,
                error=error
            )
            
            # Update status
            self._health_status[component] = health_status
            
            # Record metric
            monitoring_manager.record_metric(
                name=f"component_health_{component}",
                value=1 if status == "healthy" else 0,
                tags={"component": component, "status": status}
            )
            
            # Create alerts based on configuration
            if self._config.alert_on_failure and status != "healthy":
                await monitoring_manager.create_alert(
                    level="error",
                    component=component,
                    message=f"Component {component} is unhealthy: {error or 'Unknown error'}",
                    metadata=details
                )
                
            elif self._config.alert_on_recovery and prev_status_value != "healthy" and status == "healthy":
                await monitoring_manager.create_alert(
                    level="info",
                    component=component,
                    message=f"Component {component} has recovered",
                    metadata=details
                )
                
        except Exception as e:
            logger.error(f"Failed to update health status: {component}", error=str(e))
            
    def get_status(self, component: Optional[str] = None) -> Dict[str, HealthStatus]:
        """Get health status for components.
        
        Args:
            component: Optional component to get status for
            
        Returns:
            Dictionary of component health statuses
        """
        try:
            if not self._initialized:
                raise RuntimeError("Health check manager not initialized")
                
            if component:
                return {component: self._health_status.get(component)}
                
            return self._health_status.copy()
            
        except Exception as e:
            logger.error("Failed to get health status", error=str(e))
            return {}
            
    async def shutdown(self) -> None:
        """Shutdown the health check manager."""
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Cancel all check tasks
        for task in self._check_tasks.values():
            task.cancel()
            
        # Wait for tasks to complete
        if self._check_tasks:
            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)
            
        self._initialized = False
        logger.info("Health check manager shut down")
        
        # Record shutdown metric
        monitoring_manager.record_metric(
            name="health_check_manager_shutdown",
            value=1
        )
        
    @property
    def initialized(self) -> bool:
        """Check if the health check manager is initialized."""
        return self._initialized
        
    @property
    def config(self) -> Optional[HealthCheckConfig]:
        """Get the current configuration."""
        return self._config

# Create singleton instance
health_check_manager = HealthCheckManager() 