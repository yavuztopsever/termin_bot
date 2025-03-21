"""
Service Discovery implementation for managing service instances.
"""

from typing import Dict, Any, Optional, List
import asyncio
from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)

class ServiceInstance:
    """Service instance information."""
    
    def __init__(
        self,
        name: str,
        endpoint: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize service instance."""
        self.name = name
        self.endpoint = endpoint
        self.metadata = metadata or {}
        self.healthy = True
        self.last_heartbeat = 0
        
    def update_heartbeat(self):
        """Update service heartbeat."""
        self.last_heartbeat = asyncio.get_event_loop().time()
        
    def mark_unhealthy(self):
        """Mark service as unhealthy."""
        self.healthy = False
        
    def mark_healthy(self):
        """Mark service as healthy."""
        self.healthy = True

class ServiceDiscovery:
    """Service Discovery for managing service instances."""
    
    def __init__(self):
        """Initialize the Service Discovery."""
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.running = False
        self.heartbeat_interval = 30  # seconds
        self.health_check_interval = 60  # seconds
        
    async def start(self):
        """Start the Service Discovery."""
        self.running = True
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._health_check_loop())
        
    async def stop(self):
        """Stop the Service Discovery."""
        self.running = False
        
    async def register_service(
        self,
        service_name: str,
        endpoint: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a service instance."""
        try:
            if service_name not in self.services:
                self.services[service_name] = []
                
            instance = ServiceInstance(service_name, endpoint, metadata)
            self.services[service_name].append(instance)
            
            logger.info(
                f"Registered service {service_name} "
                f"at endpoint {endpoint}"
            )
            
        except Exception as e:
            logger.error(f"Error registering service: {str(e)}")
            raise
            
    async def deregister_service(self, service_name: str):
        """Deregister a service instance."""
        try:
            if service_name in self.services:
                del self.services[service_name]
                logger.info(f"Deregistered service {service_name}")
                
        except Exception as e:
            logger.error(f"Error deregistering service: {str(e)}")
            raise
            
    async def get_service(self, service_name: str) -> Optional[ServiceInstance]:
        """Get a healthy service instance."""
        try:
            if service_name not in self.services:
                return None
                
            instances = self.services[service_name]
            healthy_instances = [
                instance for instance in instances
                if instance.healthy
            ]
            
            if not healthy_instances:
                return None
                
            # Return first healthy instance
            return healthy_instances[0]
            
        except Exception as e:
            logger.error(f"Error getting service: {str(e)}")
            return None
            
    async def _heartbeat_loop(self):
        """Heartbeat loop for service instances."""
        while self.running:
            try:
                for service_name, instances in self.services.items():
                    for instance in instances:
                        instance.update_heartbeat()
                        
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
                await asyncio.sleep(1)
                
    async def _health_check_loop(self):
        """Health check loop for service instances."""
        while self.running:
            try:
                for service_name, instances in self.services.items():
                    for instance in instances:
                        # Check if instance is stale
                        current_time = asyncio.get_event_loop().time()
                        if current_time - instance.last_heartbeat > self.health_check_interval:
                            instance.mark_unhealthy()
                            logger.warning(
                                f"Service {service_name} at {instance.endpoint} "
                                f"marked as unhealthy"
                            )
                            
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {str(e)}")
                await asyncio.sleep(1) 