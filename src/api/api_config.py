from typing import Dict, List, Any, Optional, Tuple
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import json
import asyncio
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError
from asyncio import Lock
import time

from src.config.config import (
    BASE_URL,
    API_RATE_LIMITS,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    CAPTCHA_CONFIG,
    USER_CREDENTIALS
)
from src.utils.logger import setup_logger
from src.database.db import db
from src.models import WebsiteConfig, ApiRequest
from src.exceptions import (
    ConfigurationError,
    RateLimitExceeded,
    APIRequestError,
    CaptchaError
)
from src.utils.rate_limiter import rate_limiter
from src.services.captcha_service import captcha_service

logger = setup_logger(__name__)

class APIConfig:
    """Handles API configuration, request construction, and response parsing."""
    
    def __init__(self):
        """Initialize API configuration."""
        self.ua = UserAgent()
        self.config = None
        self._refresh_task = None
        self._session: Optional[ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize async components and load initial configuration."""
        try:
            # Create aiohttp session
            timeout = ClientTimeout(total=API_TIMEOUT)
            self._session = ClientSession(timeout=timeout)
            
            # Load initial configuration
            await self._load_config()
            
            # Start config refresh task
            self._refresh_task = asyncio.create_task(self._refresh_config_periodically())
            
        except Exception as e:
            logger.error("Failed to initialize APIConfig", error=str(e))
            raise ConfigurationError(f"Initialization failed: {str(e)}")
            
    async def close(self) -> None:
        """Clean up resources."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
                
        if self._session:
            await self._session.close()
            
    async def _load_config(self, retries: int = MAX_RETRIES) -> None:
        """Load API configuration from database with retries."""
        attempt = 0
        while attempt < retries:
            try:
                config_data = await db.website_config.find_one()
                if config_data:
                    self.config = WebsiteConfig(**config_data)
                    logger.info("Loaded API configuration from database")
                    return
                else:
                    logger.warning("No API configuration found in database")
                    self.config = None
                    return
                    
            except Exception as e:
                attempt += 1
                if attempt < retries:
                    await asyncio.sleep(RETRY_DELAY * attempt)
                else:
                    logger.error("Failed to load API configuration", error=str(e))
                    self.config = None
                    raise ConfigurationError(f"Failed to load configuration: {str(e)}")
                    
    async def _refresh_config_periodically(self) -> None:
        """Periodically refresh the configuration."""
        while True:
            try:
                await asyncio.sleep(300)  # Refresh every 5 minutes
                await self._load_config()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error refreshing configuration", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying on error
                
    async def _check_rate_limit(self, endpoint: str) -> bool:
        """Check and update rate limit for an endpoint."""
        return rate_limiter.allow_request(endpoint)
    
    async def _get_captcha_token(self) -> Optional[str]:
        """Get a valid captcha token."""
        if not self.config or not self.config.captcha_enabled:
            return None
            
        if not self.config.captcha_site_key or not self.config.captcha_endpoint:
            logger.warning("Captcha is enabled but site key or endpoint is missing")
            return None
            
        try:
            # Get puzzle endpoint
            puzzle_endpoint = f"{BASE_URL}{CAPTCHA_CONFIG['endpoints']['puzzle']}"
            verify_endpoint = f"{BASE_URL}{CAPTCHA_CONFIG['endpoints']['verify']}"
            
            # Get token from captcha service
            token = await captcha_service.get_captcha_token(
                self.config.captcha_site_key,
                puzzle_endpoint,
                verify_endpoint
            )
            
            if not token:
                logger.warning("Failed to get captcha token")
                
            return token
            
        except Exception as e:
            logger.error(f"Error getting captcha token: {e}")
            return None
            
    def _get_base_headers(self) -> Dict[str, str]:
        """Get base headers for API requests."""
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/buergerservice/terminvereinbarung.html",
            "Origin": BASE_URL
        }
        
    async def _track_api_request(
        self, 
        endpoint: str, 
        method: str, 
        parameters: Dict[str, Any],
        status_code: Optional[int] = None,
        success: bool = False,
        error_message: Optional[str] = None,
        response_time: Optional[float] = None
    ) -> None:
        """Track API request history."""
        try:
            api_request = ApiRequest(
                endpoint=endpoint,
                method=method,
                parameters=parameters,
                status_code=status_code,
                success=success,
                error_message=error_message,
                response_time=response_time
            )
            
            # Store in database
            await db.api_requests.insert_one(api_request.__dict__)
            
        except Exception as e:
            logger.error(f"Failed to track API request: {e}")
        
    async def get_check_availability_request(
        self,
        service_id: str,
        location_id: Optional[str] = None,
        date_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Construct request for checking appointment availability."""
        try:
            if not self.config:
                raise ConfigurationError("API configuration not loaded")
                
            await self._check_rate_limit("/api/v1/check")
            
            headers = {
                **self._get_base_headers(),
                **self.config.headers
            }
            
            body = {
                "serviceID": service_id
            }
            
            if location_id:
                body["locationID"] = location_id
                
            if date_preferences:
                body["datePreferences"] = date_preferences
                
            return {
                "url": f"{self.config.base_url}{self.config.check_availability_endpoint}",
                "method": "POST",
                "headers": headers,
                "body": body
            }
            
        except Exception as e:
            logger.error(
                "Failed to construct availability request",
                error=str(e),
                service_id=service_id,
                location_id=location_id
            )
            raise APIRequestError(f"Failed to construct availability request: {str(e)}")
            
    async def get_book_appointment_request(
        self,
        appointment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construct request for booking an appointment."""
        try:
            if not self.config:
                raise ConfigurationError("API configuration not loaded")
                
            await self._check_rate_limit("/api/v1/book")
            
            headers = {
                **self._get_base_headers(),
                **self.config.headers
            }
            
            body = {
                "serviceID": appointment_details["service_id"],
                "date": appointment_details["date"],
                "time": appointment_details["time"]
            }
            
            if appointment_details.get("location_id"):
                body["locationID"] = appointment_details["location_id"]
                
            return {
                "url": f"{self.config.base_url}{self.config.book_appointment_endpoint}",
                "method": "POST",
                "headers": headers,
                "body": body
            }
            
        except Exception as e:
            logger.error(
                "Failed to construct booking request",
                error=str(e),
                appointment_details=appointment_details
            )
            raise APIRequestError(f"Failed to construct booking request: {str(e)}")
            
    def parse_availability_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the availability check response."""
        try:
            slots = []
            raw_slots = response_data.get("slots", [])
            
            for slot in raw_slots:
                try:
                    parsed_slot = {
                        "date": slot["date"],
                        "time": slot["time"],
                        "location_id": slot.get("locationId"),
                        "service_id": slot.get("serviceId")
                    }
                    slots.append(parsed_slot)
                except KeyError as e:
                    logger.warning(f"Invalid slot data: {e}", slot=slot)
                    continue
                    
            return slots
            
        except Exception as e:
            logger.error("Failed to parse availability response", error=str(e))
            return []
            
    def parse_booking_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the booking response."""
        try:
            if response_data.get("success"):
                return {
                    "success": True,
                    "booking_id": response_data.get("bookingId"),
                    "message": response_data.get("message", "Booking successful")
                }
            else:
                return {
                    "success": False,
                    "message": response_data.get("message", "Booking failed")
                }
                
        except Exception as e:
            logger.error("Failed to parse booking response", error=str(e))
            return {
                "success": False,
                "message": f"Failed to parse booking response: {str(e)}"
            }
            
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the API configuration."""
        try:
            # Validate the new configuration
            if not self._validate_config(new_config):
                raise ConfigurationError("Invalid configuration format")
                
            # Create WebsiteConfig instance
            config = WebsiteConfig(**new_config)
            
            # Update database
            await db.website_config.replace_one(
                {},  # Empty filter to replace the single document
                new_config,
                upsert=True
            )
            
            # Update local config
            self.config = config
            logger.info("Updated API configuration")
            
        except Exception as e:
            logger.error("Failed to update API configuration", error=str(e))
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")
            
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate API configuration format."""
        try:
            required_fields = [
                "service_id",
                "location_id",
                "base_url",
                "check_availability_endpoint",
                "book_appointment_endpoint",
                "headers",
                "request_timeout",
                "rate_limit",
                "rate_limit_period",
                "retry_count",
                "retry_delay"
            ]
            
            return all(field in config for field in required_fields)
            
        except Exception:
            return False
            
    async def get_available_days(
        self, 
        service_id: str, 
        office_id: str, 
        start_date: str, 
        end_date: str, 
        service_count: int = 1
    ) -> Dict[str, Any]:
        """Get available days for a specific service and office."""
        from src.utils.retry import async_retry, RetryConfig
        from src.utils.logger import log_api_request, log_api_response, log_error, get_correlation_id
        
        if not self._session:
            await self.initialize()
            
        endpoint = "/buergeransicht/api/backend/available-days"
        method = "GET"
        
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "officeId": office_id,
            "serviceId": service_id,
            "serviceCount": service_count
        }
        
        # Create retry configuration
        retry_config = RetryConfig(
            max_retries=MAX_RETRIES,
            base_delay=RETRY_DELAY,
            max_delay=RETRY_DELAY * 10,
            backoff_factor=2.0,
            jitter=True,
            jitter_factor=0.1,
            retry_on_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, APIRequestError),
            retry_on_status_codes=(429, 500, 502, 503, 504)
        )
        
        # Generate correlation ID for request tracking
        correlation_id = get_correlation_id()
        
        @async_retry(retry_config=retry_config)
        async def _make_request():
            # Check rate limit
            if not rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
                
            # Get captcha token if needed
            captcha_token = await self._get_captcha_token()
            if captcha_token:
                params["captchaToken"] = captcha_token
                
            # Construct URL with query parameters
            url = f"{BASE_URL}{endpoint}"
            
            # Log API request
            request_id = log_api_request(
                logger,
                method=method,
                url=url,
                headers=self._get_base_headers(),
                body=params,
                request_id=correlation_id
            )
            
            start_time = time.time()
            
            try:
                async with self._session.get(
                    url, 
                    params=params, 
                    headers=self._get_base_headers()
                ) as response:
                    response_time = time.time() - start_time
                    status_code = response.status
                    
                    # Track API request
                    await self._track_api_request(
                        endpoint=endpoint,
                        method=method,
                        parameters=params,
                        status_code=status_code,
                        success=status_code == 200,
                        response_time=response_time
                    )
                    
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    # Log API response
                    log_api_response(
                        logger,
                        status_code=status_code,
                        response_body=response_data,
                        elapsed=response_time,
                        request_id=request_id
                    )
                    
                    if response.status == 200:
                        if isinstance(response_data, dict):
                            # Handle specific error cases
                            if "errorCode" in response_data and response_data["errorCode"] == "noAppointmentForThisScope":
                                logger.info(f"No appointments available for service {service_id} at office {office_id}")
                                return {"available": False, "message": response_data.get("errorMessage", "No appointments available")}
                                
                            return {"available": True, "days": response_data.get("days", [])}
                        else:
                            return {"available": False, "message": "Invalid JSON response"}
                    else:
                        error_text = response_data if isinstance(response_data, str) else json.dumps(response_data)
                        error_msg = f"Error getting available days: {response.status} - {error_text}"
                        logger.error(error_msg, request_id=request_id)
                        
                        # Non-retryable status codes should raise an exception
                        if response.status not in retry_config.retry_on_status_codes:
                            raise APIRequestError(error_msg)
                        
                        # For retryable status codes, return a response that will trigger a retry
                        return response
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                error_msg = f"Error getting available days: {str(e)}"
                logger.error(error_msg, request_id=request_id)
                raise APIRequestError(error_msg)
        
        try:
            return await _make_request()
        except Exception as e:
            log_error(
                logger,
                error=e,
                context={
                    "service_id": service_id,
                    "office_id": office_id,
                    "start_date": start_date,
                    "end_date": end_date
                },
                request_id=correlation_id
            )
            raise APIRequestError(f"Failed to get available days: {str(e)}")
            
    async def book_appointment(
        self,
        service_id: str,
        office_id: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """Book an appointment."""
        from src.utils.retry import async_retry, RetryConfig
        from src.utils.logger import log_api_request, log_api_response, log_error, get_correlation_id
        
        if not self._session:
            await self.initialize()
            
        endpoint = "/buergeransicht/api/backend/book-appointment"
        method = "POST"
        
        # Prepare request body
        body = {
            "serviceId": service_id,
            "officeId": office_id,
            "date": date,
            "time": time,
            "user": {
                "name": USER_CREDENTIALS["name"],
                "email": USER_CREDENTIALS["email"],
                "personCount": USER_CREDENTIALS["person_count"]
            }
        }
        
        # Create retry configuration - use fewer retries for booking to avoid duplicate bookings
        retry_config = RetryConfig(
            max_retries=2,  # Fewer retries for booking operations
            base_delay=RETRY_DELAY,
            max_delay=RETRY_DELAY * 5,
            backoff_factor=2.0,
            jitter=True,
            jitter_factor=0.1,
            retry_on_exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
            retry_on_status_codes=(429, 500, 502, 503, 504)
        )
        
        # Generate correlation ID for request tracking
        correlation_id = get_correlation_id()
        
        @async_retry(retry_config=retry_config)
        async def _make_request():
            # Check rate limit
            if not rate_limiter.allow_request(endpoint):
                raise RateLimitExceeded(f"Rate limit exceeded for endpoint: {endpoint}")
                
            # Get captcha token if needed
            captcha_token = await self._get_captcha_token()
            if captcha_token:
                body["captchaToken"] = captcha_token
                
            # Construct URL
            url = f"{BASE_URL}{endpoint}"
            
            # Log API request
            request_id = log_api_request(
                logger,
                method=method,
                url=url,
                headers=self._get_base_headers(),
                body=body,
                request_id=correlation_id
            )
            
            start_time = time.time()
            
            try:
                async with self._session.post(
                    url, 
                    json=body, 
                    headers=self._get_base_headers()
                ) as response:
                    response_time = time.time() - start_time
                    status_code = response.status
                    
                    # Track API request
                    await self._track_api_request(
                        endpoint=endpoint,
                        method=method,
                        parameters=body,
                        status_code=status_code,
                        success=status_code == 200,
                        response_time=response_time
                    )
                    
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    # Log API response
                    log_api_response(
                        logger,
                        status_code=status_code,
                        response_body=response_data,
                        elapsed=response_time,
                        request_id=request_id
                    )
                    
                    if response.status == 200:
                        if isinstance(response_data, dict):
                            if response_data.get("success"):
                                return {
                                    "success": True,
                                    "booking_id": response_data.get("bookingId"),
                                    "message": response_data.get("message", "Booking successful")
                                }
                            else:
                                # Business logic failure (not a technical error)
                                return {
                                    "success": False,
                                    "message": response_data.get("message", "Booking failed")
                                }
                        else:
                            return {
                                "success": False,
                                "message": "Invalid JSON response"
                            }
                    else:
                        error_text = response_data if isinstance(response_data, str) else json.dumps(response_data)
                        error_msg = f"Error booking appointment: {response.status} - {error_text}"
                        logger.error(error_msg, request_id=request_id)
                        
                        # Non-retryable status codes should raise an exception
                        if response.status not in retry_config.retry_on_status_codes:
                            raise APIRequestError(error_msg)
                        
                        # For retryable status codes, return a response that will trigger a retry
                        return response
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                error_msg = f"Error booking appointment: {str(e)}"
                logger.error(error_msg, request_id=request_id)
                raise APIRequestError(error_msg)
        
        try:
            return await _make_request()
        except Exception as e:
            log_error(
                logger,
                error=e,
                context={
                    "service_id": service_id,
                    "office_id": office_id,
                    "date": date,
                    "time": time
                },
                request_id=correlation_id
            )
            raise APIRequestError(f"Failed to book appointment: {str(e)}")

# Create a global API configuration instance
api_config = APIConfig()
