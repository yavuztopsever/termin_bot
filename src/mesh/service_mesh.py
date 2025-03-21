"""
Service Mesh implementation for handling service-to-service communication.
"""

from typing import Dict, Any, Optional
import aiohttp
from .discovery import ServiceDiscovery
from .circuit_breaker import CircuitBreaker
from .load_balancer import LoadBalancer
from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)

class ServiceMesh:
    """Service Mesh for handling service-to-service communication."""
    
    def __init__(self):
        """Initialize the Service Mesh."""
        self.discovery = ServiceDiscovery()
        self.circuit_breaker = CircuitBreaker()
        self.load_balancer = LoadBalancer()
        self.session = None
        
    async def start(self):
        """Start the Service Mesh."""
        self.session = aiohttp.ClientSession()
        await self.discovery.start()
        await self.circuit_breaker.start()
        await self.load_balancer.start()
        
    async def stop(self):
        """Stop the Service Mesh."""
        if self.session:
            await self.session.close()
        await self.discovery.stop()
        await self.circuit_breaker.stop()
        await self.load_balancer.stop()
        
    async def call_service(
        self,
        service_name: str,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Call a service through the mesh."""
        try:
            # Get service instance
            service = await self.discovery.get_service(service_name)
            if not service:
                raise Exception(f"Service {service_name} not found")
                
            # Check circuit breaker
            if not await self.circuit_breaker.check_service(service_name):
                raise Exception(f"Circuit breaker open for service {service_name}")
                
            # Get load balanced endpoint
            endpoint = await self.load_balancer.get_endpoint(service)
            
            # Prepare request
            url = f"{endpoint}{path}"
            if headers is None:
                headers = {}
                
            # Add service mesh headers
            headers.update({
                "X-Service-Mesh": "true",
                "X-Source-Service": settings.SERVICE_NAME
            })
            
            # Make request
            async with self.session.request(
                method,
                url,
                json=data,
                headers=headers
            ) as response:
                # Check response
                if response.status >= 500:
                    await self.circuit_breaker.record_failure(service_name)
                    raise Exception(f"Service {service_name} returned error")
                    
                # Record success
                await self.circuit_breaker.record_success(service_name)
                
                # Return response
                return await response.json()
                
        except Exception as e:
            logger.error(f"Error calling service {service_name}: {str(e)}")
            raise
            
    async def register_service(
        self,
        service_name: str,
        endpoint: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a service in the mesh."""
        try:
            await self.discovery.register_service(
                service_name,
                endpoint,
                metadata
            )
            await self.load_balancer.add_endpoint(service_name, endpoint)
            
        except Exception as e:
            logger.error(f"Error registering service {service_name}: {str(e)}")
            raise
            
    async def deregister_service(self, service_name: str):
        """Deregister a service from the mesh."""
        try:
            await self.discovery.deregister_service(service_name)
            await self.load_balancer.remove_endpoint(service_name)
            
        except Exception as e:
            logger.error(f"Error deregistering service {service_name}: {str(e)}")
            raise 