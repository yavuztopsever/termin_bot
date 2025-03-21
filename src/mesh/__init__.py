"""
Service Mesh module for handling service-to-service communication.
"""

from .service_mesh import ServiceMesh
from .discovery import ServiceDiscovery
from .circuit_breaker import CircuitBreaker
from .load_balancer import LoadBalancer

__all__ = [
    'ServiceMesh',
    'ServiceDiscovery',
    'CircuitBreaker',
    'LoadBalancer'
] 