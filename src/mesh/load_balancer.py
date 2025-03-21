"""
Load Balancer implementation for distributing requests across service instances.
"""

from typing import Dict, Any, List, Optional
import random
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LoadBalancer:
    """Load Balancer for distributing requests across service instances."""
    
    def __init__(self):
        """Initialize the Load Balancer."""
        self.services: Dict[str, List[str]] = {}
        self.running = False
        
    async def start(self):
        """Start the Load Balancer."""
        self.running = True
        
    async def stop(self):
        """Stop the Load Balancer."""
        self.running = False
        
    async def add_endpoint(self, service_name: str, endpoint: str):
        """Add a service endpoint."""
        try:
            if service_name not in self.services:
                self.services[service_name] = []
                
            if endpoint not in self.services[service_name]:
                self.services[service_name].append(endpoint)
                logger.info(
                    f"Added endpoint {endpoint} "
                    f"for service {service_name}"
                )
                
        except Exception as e:
            logger.error(f"Error adding endpoint: {str(e)}")
            raise
            
    async def remove_endpoint(self, service_name: str):
        """Remove a service endpoint."""
        try:
            if service_name in self.services:
                del self.services[service_name]
                logger.info(f"Removed endpoints for service {service_name}")
                
        except Exception as e:
            logger.error(f"Error removing endpoint: {str(e)}")
            raise
            
    async def get_endpoint(self, service_name: str) -> Optional[str]:
        """Get a service endpoint using round-robin strategy."""
        try:
            if service_name not in self.services:
                return None
                
            endpoints = self.services[service_name]
            if not endpoints:
                return None
                
            # Simple round-robin implementation
            endpoint = endpoints.pop(0)
            endpoints.append(endpoint)
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Error getting endpoint: {str(e)}")
            return None
            
    async def get_random_endpoint(self, service_name: str) -> Optional[str]:
        """Get a random service endpoint."""
        try:
            if service_name not in self.services:
                return None
                
            endpoints = self.services[service_name]
            if not endpoints:
                return None
                
            return random.choice(endpoints)
            
        except Exception as e:
            logger.error(f"Error getting random endpoint: {str(e)}")
            return None
            
    async def get_least_connections_endpoint(
        self,
        service_name: str,
        connection_counts: Dict[str, int]
    ) -> Optional[str]:
        """Get service endpoint with least active connections."""
        try:
            if service_name not in self.services:
                return None
                
            endpoints = self.services[service_name]
            if not endpoints:
                return None
                
            # Find endpoint with least connections
            min_connections = float('inf')
            selected_endpoint = None
            
            for endpoint in endpoints:
                connections = connection_counts.get(endpoint, 0)
                if connections < min_connections:
                    min_connections = connections
                    selected_endpoint = endpoint
                    
            return selected_endpoint
            
        except Exception as e:
            logger.error(f"Error getting least connections endpoint: {str(e)}")
            return None 