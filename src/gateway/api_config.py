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
    CaptchaError,
    ValidationError,
    ResourceValidationError
)
from src.utils.rate_limiter import rate_limiter
from src.services.captcha_service import captcha_service

logger = setup_logger(__name__)

class APIConfig:
    """Configuration and mapping for Munich Termin API."""
    
    def __init__(self):
        """Initialize the API configuration."""
        self._initialized = False
        self.ua = UserAgent()
        self.config = None
        self._refresh_task = None
        self._session: Optional[ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize the configuration."""
        try:
            # Create aiohttp session
            timeout = ClientTimeout(total=API_TIMEOUT)
            self._session = ClientSession(timeout=timeout)
            
            # Load initial configuration
            await self._load_config()
            
            # Start config refresh task
            self._refresh_task = asyncio.create_task(self._refresh_config_periodically())
            
            self._initialized = True
        except Exception as e:
            logger.error("Failed to initialize APIConfig", error=str(e))
            raise APIRequestError(f"Failed to initialize config: {str(e)}")
            
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
            
        self._initialized = False
            
    async def _load_config(self, retries: int = MAX_RETRIES) -> None:
        """Load API configuration from database with retries."""
        from src.database.repositories import website_config_repository
        
        attempt = 0
        while attempt < retries:
            try:
                config_data = await website_config_repository.get_latest_config()
                if config_data:
                    self.config = config_data
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
            # Create API request object
            api_request = ApiRequest(
                endpoint=endpoint,
                method=method,
                parameters=parameters,
                status_code=status_code,
                success=success,
                error_message=error_message,
                response_time=response_time,
                created_at=datetime.utcnow()
            )
            
            # Log the request
            logger.info(
                "API request",
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                success=success,
                response_time=response_time
            )
            
            # We could store this in the database, but for now we'll just log it
            # In a future update, we could add an ApiRequestRepository
            
        except Exception as e:
            logger.error(f"Failed to track API request: {e}")
        
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        resource_type: str
    ) -> None:
        """Validate required fields are present."""
        required_fields = self.validation_rules[resource_type]["required_fields"]
        missing_fields = [
            field for field in required_fields
            if field not in data
        ]
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields for {resource_type}: {', '.join(missing_fields)}"
            )
            
    def _validate_field_types(
        self,
        data: Dict[str, Any],
        resource_type: str
    ) -> None:
        """Validate field types."""
        field_types = self.validation_rules[resource_type]["field_types"]
        
        for field, value in data.items():
            if field in field_types:
                expected_type = field_types[field]
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Invalid type for {field} in {resource_type}: "
                        f"expected {expected_type.__name__}, got {type(value).__name__}"
                    )
                    
    def _map_fields(
        self,
        data: Dict[str, Any],
        resource_type: str,
        reverse: bool = False
    ) -> Dict[str, Any]:
        """Map fields between API and internal format."""
        mapping = self.mappings[resource_type]
        result = {}
        
        for internal_field, api_field in mapping.items():
            if reverse:
                if internal_field in data:
                    result[api_field] = data[internal_field]
            else:
                if api_field in data:
                    result[internal_field] = data[api_field]
                    
        return result
        
    def _validate_date_format(self, date_str: str) -> None:
        """Validate date format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}")
            
    def _validate_time_format(self, time_str: str) -> None:
        """Validate time format."""
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValidationError(f"Invalid time format: {time_str}")
            
    async def get_check_availability_request(
        self,
        service_id: str,
        location_id: Optional[str] = None,
        date_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get request configuration for checking availability."""
        if not self._initialized:
            raise APIRequestError("APIConfig not initialized")
            
        endpoint = self.endpoints["availability"]["check"]
        data = {
            "serviceID": service_id,
            "datePreferences": date_preferences or {}
        }
        
        if location_id:
            data["locationID"] = location_id
            
        return {
            "url": endpoint,
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": data
        }
        
    async def get_available_days_request(
        self,
        service_id: str,
        office_id: str,
        start_date: str,
        end_date: str,
        service_count: int = 1
    ) -> Dict[str, Any]:
        """Get request configuration for getting available days."""
        if not self._initialized:
            raise APIRequestError("APIConfig not initialized")
            
        self._validate_date_format(start_date)
        self._validate_date_format(end_date)
        
        endpoint = self.endpoints["availability"]["days"]
        data = {
            "serviceID": service_id,
            "officeID": office_id,
            "startDate": start_date,
            "endDate": end_date,
            "serviceCount": service_count
        }
        
        return {
            "url": endpoint,
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": data
        }
        
    async def get_book_appointment_request(
        self,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get request configuration for booking an appointment."""
        if not self._initialized:
            raise APIRequestError("APIConfig not initialized")
            
        self._validate_required_fields(appointment_data, "appointment")
        self._validate_field_types(appointment_data, "appointment")
        self._validate_date_format(appointment_data["date"])
        self._validate_time_format(appointment_data["time"])
        
        endpoint = self.endpoints["appointments"]["book"]
        data = self._map_fields(appointment_data, "appointment", reverse=True)
        
        return {
            "url": endpoint,
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": data
        }
        
    def parse_availability_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse availability response data."""
        try:
            available_slots = response_data.get("availableSlots", [])
            parsed_slots = []
            
            for slot in available_slots:
                parsed_slot = {
                    "date": slot.get("date"),
                    "time": slot.get("time"),
                    "location_id": slot.get("locationID"),
                    "service_id": slot.get("serviceID"),
                    "capacity": slot.get("capacity")
                }
                parsed_slots.append(parsed_slot)
                
            return parsed_slots
            
        except Exception as e:
            logger.error("Failed to parse availability response", error=str(e))
            raise ResourceValidationError(f"Failed to parse availability response: {str(e)}")
            
    def parse_booking_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse booking response data."""
        try:
            return self._map_fields(response_data, "appointment")
        except Exception as e:
            logger.error("Failed to parse booking response", error=str(e))
            raise ResourceValidationError(f"Failed to parse booking response: {str(e)}")
            
    def parse_service_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse service response data."""
        try:
            return self._map_fields(response_data, "service")
        except Exception as e:
            logger.error("Failed to parse service response", error=str(e))
            raise ResourceValidationError(f"Failed to parse service response: {str(e)}")
            
    def parse_location_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse location response data."""
        try:
            return self._map_fields(response_data, "location")
        except Exception as e:
            logger.error("Failed to parse location response", error=str(e))
            raise ResourceValidationError(f"Failed to parse location response: {str(e)}")
            
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the API configuration."""
        from src.database.repositories import website_config_repository
        
        try:
            # Validate the new configuration
            if not self._validate_config(new_config):
                raise ConfigurationError("Invalid configuration format")
                
            # Update database using repository
            config = await website_config_repository.update_config(new_config)
            
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
