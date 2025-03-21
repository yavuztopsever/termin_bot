from typing import Dict, Any, Optional
import aiohttp
from aiohttp import ClientSession, ClientTimeout
import asyncio
from datetime import datetime, timedelta

from src.config.config import (
    BASE_URL,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    USER_CREDENTIALS
)
from src.exceptions import (
    APIRequestError,
    RateLimitExceeded,
    AuthenticationError,
    ResourceTimeoutError
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class APIClient:
    """Client for making requests to the Munich Termin API."""
    
    def __init__(self):
        """Initialize the API client."""
        self.base_url = BASE_URL
        self.timeout = ClientTimeout(total=API_TIMEOUT)
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self._session: Optional[ClientSession] = None
        self._rate_limit_tokens = 20  # Initial rate limit tokens
        self._last_token_refresh = datetime.utcnow()
        self._token_refresh_rate = 1  # tokens per second
        
    async def initialize(self) -> None:
        """Initialize the client and create session."""
        try:
            self._session = ClientSession(
                timeout=self.timeout,
                headers=self._get_default_headers()
            )
        except Exception as e:
            logger.error("Failed to initialize APIClient", error=str(e))
            raise APIRequestError(f"Failed to initialize client: {str(e)}")
            
    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()
            
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MunichTerminBot/1.0"
        }
        
    async def _refresh_rate_limit_tokens(self) -> None:
        """Refresh rate limit tokens based on time elapsed."""
        now = datetime.utcnow()
        time_elapsed = (now - self._last_token_refresh).total_seconds()
        new_tokens = int(time_elapsed * self._token_refresh_rate)
        
        if new_tokens > 0:
            self._rate_limit_tokens = min(20, self._rate_limit_tokens + new_tokens)
            self._last_token_refresh = now
            
    async def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit is exceeded."""
        await self._refresh_rate_limit_tokens()
        
        if self._rate_limit_tokens <= 0:
            wait_time = (1 / self._token_refresh_rate) * 2
            await asyncio.sleep(wait_time)
            await self._refresh_rate_limit_tokens()
            
        if self._rate_limit_tokens <= 0:
            raise RateLimitExceeded("Rate limit exceeded")
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with retries and rate limiting."""
        if not self._session:
            raise APIRequestError("Client not initialized")
            
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
            
        for attempt in range(self.max_retries):
            try:
                await self._wait_for_rate_limit()
                
                async with self._session.request(
                    method,
                    url,
                    json=data,
                    headers=request_headers
                ) as response:
                    self._rate_limit_tokens -= 1
                    
                    if response.status == 401:
                        raise AuthenticationError("Invalid credentials")
                    elif response.status == 429:
                        raise RateLimitExceeded("Rate limit exceeded")
                    elif response.status >= 400:
                        error_text = await response.text()
                        raise APIRequestError(
                            f"Request failed with status {response.status}: {error_text}"
                        )
                        
                    return await response.json()
                    
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise ResourceTimeoutError("Request timed out")
                await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise APIRequestError(f"Request failed: {str(e)}")
                await asyncio.sleep(self.retry_delay)
                
    async def check_availability(
        self,
        service_id: str,
        location_id: Optional[str] = None,
        date_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check appointment availability."""
        endpoint = "/api/v1/availability/check"
        data = {
            "serviceID": service_id,
            "locationID": location_id,
            "datePreferences": date_preferences or {}
        }
        
        return await self._make_request("POST", endpoint, data=data)
        
    async def get_available_days(
        self,
        service_id: str,
        office_id: str,
        start_date: str,
        end_date: str,
        service_count: int = 1
    ) -> Dict[str, Any]:
        """Get available days for appointments."""
        endpoint = "/api/v1/availability/days"
        data = {
            "serviceID": service_id,
            "officeID": office_id,
            "startDate": start_date,
            "endDate": end_date,
            "serviceCount": service_count
        }
        
        return await self._make_request("POST", endpoint, data=data)
        
    async def book_appointment(
        self,
        service_id: str,
        office_id: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """Book an appointment."""
        endpoint = "/api/v1/appointments/book"
        data = {
            "serviceID": service_id,
            "officeID": office_id,
            "date": date,
            "time": time
        }
        
        return await self._make_request("POST", endpoint, data=data)
        
    async def get_appointment_status(self, booking_id: str) -> Dict[str, Any]:
        """Get the status of a booked appointment."""
        endpoint = f"/api/v1/appointments/{booking_id}/status"
        return await self._make_request("GET", endpoint)
        
    async def cancel_appointment(self, booking_id: str) -> Dict[str, Any]:
        """Cancel a booked appointment."""
        endpoint = f"/api/v1/appointments/{booking_id}/cancel"
        return await self._make_request("POST", endpoint)
        
    async def get_services(self) -> Dict[str, Any]:
        """Get available services."""
        endpoint = "/api/v1/services"
        return await self._make_request("GET", endpoint)
        
    async def get_locations(self) -> Dict[str, Any]:
        """Get available locations."""
        endpoint = "/api/v1/locations"
        return await self._make_request("GET", endpoint)
        
    async def get_location_details(self, location_id: str) -> Dict[str, Any]:
        """Get details for a specific location."""
        endpoint = f"/api/v1/locations/{location_id}"
        return await self._make_request("GET", endpoint)
        
    async def get_service_details(self, service_id: str) -> Dict[str, Any]:
        """Get details for a specific service."""
        endpoint = f"/api/v1/services/{service_id}"
        return await self._make_request("GET", endpoint)

# Create singleton instance
api_client = APIClient() 