"""Health monitoring module for system status checks."""

import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from src.utils.logger import setup_logger
from src.database import get_database, get_redis

logger = setup_logger(__name__)

class HealthMonitor:
    """Monitor system health and resources."""
    
    def __init__(self, check_interval: int = 60):
        """Initialize the health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds.
        """
        self.check_interval = check_interval
        self.logger = logger
        self._last_check: Optional[datetime] = None
        self._is_running = False
        
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent
        }
        
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            db = await get_database()
            async with db.async_session() as session:
                # Try a simple query
                await session.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "message": "Database is responding",
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database is not responding: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def check_redis_health(self, redis_uri: str) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            redis = await get_redis(redis_uri)
            await redis.ping()
            await redis.close()
            return {
                "status": "healthy",
                "message": "Redis is responding",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis is not responding: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def check_system_health(self, redis_uri: str) -> Dict[str, Any]:
        """Check overall system health."""
        db_health = await self.check_database_health()
        redis_health = await self.check_redis_health(redis_uri)
        
        system_healthy = all(
            check["status"] == "healthy"
            for check in [db_health, redis_health]
        )
        
        return {
            "status": "healthy" if system_healthy else "unhealthy",
            "database": db_health,
            "redis": redis_health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform a complete health check."""
        self._last_check = datetime.utcnow()
        
        # Gather all health metrics
        resources = await self.check_system_resources()
        health_status = await self.check_system_health("")
        
        health_data = {
            "timestamp": self._last_check,
            "system_resources": resources,
            "health_status": health_status,
            "status": "healthy" if health_status["status"] == "healthy" else "unhealthy"
        }
        
        # Log health status
        if health_data["status"] == "unhealthy":
            self.logger.warning(f"System health check failed: {health_data}")
        else:
            self.logger.info("System health check passed")
            
        return health_data
        
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        self._is_running = True
        self.logger.info("Starting health monitoring")
        
        while self._is_running:
            try:
                await self.perform_health_check()
            except Exception as e:
                self.logger.error(f"Error during health check: {str(e)}")
                
            await asyncio.sleep(self.check_interval)
            
    def stop_monitoring(self):
        """Stop health monitoring."""
        self._is_running = False
        self.logger.info("Stopping health monitoring")
        
    @property
    def last_check_time(self) -> Optional[datetime]:
        """Get the timestamp of the last health check."""
        return self._last_check 