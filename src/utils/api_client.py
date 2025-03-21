from typing import Dict, Any, Optional, Union
import aiohttp
import json
from datetime import datetime

from src.config.config import API_CONFIG
from src.utils.logger import setup_logger
from src.utils.rate_limiter import rate_limiter, RateLimitExceeded
from src.monitoring.metrics import metrics_manager

logger = setup_logger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    pass

class APIClient:
    """Client for making API requests with rate limiting and error handling."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize the API client."""
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Create session when entering context."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session when exiting context."""
        if self.session:
            await self.session.close()
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make an API request with rate limiting and error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Get session
        session = self.session or aiohttp.ClientSession(headers=self.headers)
        
        try:
            # Acquire rate limit tokens
            await rate_limiter.acquire(endpoint)
            
            # Prepare request
            request_headers = {**self.headers, **(headers or {})}
            timeout = timeout or API_CONFIG["timeout"]
            
            # Start timing
            start_time = datetime.utcnow()
            
            # Make request
            async with session.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=timeout
            ) as response:
                # Record metrics
                duration = (datetime.utcnow() - start_time).total_seconds()
                metrics_manager.record_api_request(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status,
                    duration=duration
                )
                
                # Handle response
                if response.status >= 400:
                    error_text = await response.text()
                    try:
                        error_data = json.loads(error_text)
                    except json.JSONDecodeError:
                        error_data = {"message": error_text}
                        
                    raise APIError(
                        f"API request failed: {error_data.get('message', 'Unknown error')}"
                    )
                    
                return await response.json()
                
        except aiohttp.ClientError as e:
            metrics_manager.record_api_error(endpoint, str(e))
            raise APIError(f"API request failed: {str(e)}")
            
        finally:
            # Release rate limit tokens
            await rate_limiter.release(endpoint)
            
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            timeout=timeout
        )
        
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request(
            "POST",
            endpoint,
            data=data,
            json_data=json_data,
            headers=headers,
            timeout=timeout
        )
        
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request(
            "PUT",
            endpoint,
            data=data,
            json_data=json_data,
            headers=headers,
            timeout=timeout
        )
        
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request(
            "DELETE",
            endpoint,
            headers=headers,
            timeout=timeout
        )

# Create singleton instance
api_client = APIClient(API_CONFIG["base_url"]) 