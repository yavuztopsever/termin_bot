"""Service for handling FriendlyCaptcha challenges."""

import time
import json
import asyncio
import base64
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import ClientSession, ClientTimeout
from twocaptcha import TwoCaptcha

from src.config.config import (
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    CAPTCHA_CONFIG
)
from src.utils.logger import setup_logger
from src.exceptions import (
    CaptchaError,
    APIRequestError
)
from src.utils.rate_limiter import rate_limiter

logger = setup_logger(__name__)

class CaptchaService:
    """Service for handling FriendlyCaptcha challenges."""
    
    def __init__(self, session: Optional[ClientSession] = None):
        """Initialize captcha service."""
        self.session = session
        self.token_cache = {}
        self._lock = asyncio.Lock()
        self.solver = None
        if CAPTCHA_CONFIG["solver"] == "2captcha" and CAPTCHA_CONFIG["2captcha_api_key"]:
            self.solver = TwoCaptcha(CAPTCHA_CONFIG["2captcha_api_key"])
        
    async def initialize(self) -> None:
        """Initialize the captcha service."""
        if not self.session:
            timeout = ClientTimeout(total=API_TIMEOUT)
            self.session = ClientSession(timeout=timeout)
            
    async def close(self) -> None:
        """Close resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def get_captcha_token(
        self, 
        site_key: str, 
        puzzle_endpoint: str, 
        captcha_endpoint: str
    ) -> Optional[str]:
        """Get a valid captcha token, either from cache or by solving a new puzzle."""
        async with self._lock:
            # Check cache first
            current_time = time.time()
            cache_key = f"{site_key}:{puzzle_endpoint}"
            
            if cache_key in self.token_cache:
                token, expiry = self.token_cache[cache_key]
                if expiry > current_time:
                    logger.info("Using cached captcha token")
                    return token
                else:
                    # Token expired, remove from cache
                    del self.token_cache[cache_key]
            
            # No valid token in cache, solve new puzzle
            try:
                token = await self._solve_captcha(site_key, puzzle_endpoint, captcha_endpoint)
                if token:
                    # Cache token with 5-minute expiry
                    self.token_cache[cache_key] = (token, current_time + 300)
                    return token
                    
                return None
                
            except Exception as e:
                logger.error(f"Error getting captcha token: {e}")
                return None
                
    async def _solve_captcha(
        self, 
        site_key: str, 
        puzzle_endpoint: str, 
        captcha_endpoint: str
    ) -> Optional[str]:
        """Solve a FriendlyCaptcha puzzle."""
        try:
            # Get puzzle
            puzzle_response = await self._send_request(
                puzzle_endpoint,
                {"sitekey": site_key}
            )
            
            puzzle = puzzle_response.get("puzzle")
            if not puzzle:
                logger.error("No puzzle found in response")
                return None
                
            # Solve puzzle using the configured solver
            solution = await self._solve_puzzle(puzzle, site_key)
            
            # Verify solution
            verify_response = await self._send_request(
                captcha_endpoint,
                {"solution": solution, "sitekey": site_key}
            )
            
            if verify_response.get("success"):
                logger.info("Captcha solved successfully")
                return verify_response.get("token")
                
            logger.warning("Captcha solution verification failed")
            return None
            
        except Exception as e:
            logger.error(f"Error solving captcha: {e}")
            raise CaptchaError(f"Failed to solve captcha: {str(e)}")
            
    async def _solve_puzzle(self, puzzle: str, site_key: str) -> str:
        """
        Solve a FriendlyCaptcha puzzle using the configured solver.
        
        Args:
            puzzle: The puzzle data from the FriendlyCaptcha API
            site_key: The site key for the captcha
            
        Returns:
            The solution string
        """
        # Check which solver to use
        if CAPTCHA_CONFIG["solver"] == "2captcha" and self.solver:
            try:
                logger.info("Solving captcha using 2captcha service")
                # Convert puzzle to base64 if needed
                if not puzzle.startswith("data:"):
                    puzzle_data = f"data:image/png;base64,{base64.b64encode(puzzle.encode()).decode()}"
                else:
                    puzzle_data = puzzle
                
                # Use 2captcha to solve the puzzle
                # Run in a separate thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.solver.friendlycaptcha.solve(
                        sitekey=site_key,
                        url=CAPTCHA_CONFIG["endpoints"]["puzzle"],
                        data=puzzle_data
                    )
                )
                
                logger.info("Captcha solved successfully with 2captcha")
                return result["code"]
            except Exception as e:
                logger.error(f"Error solving captcha with 2captcha: {e}")
                # Fall back to dummy solution if 2captcha fails
                logger.warning("Falling back to dummy solution")
                return "dummy_solution"
        else:
            # Use dummy solution as fallback
            logger.warning("Using dummy captcha solution - no solver configured")
            return "dummy_solution"
        
    async def _send_request(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the captcha API."""
        from src.utils.retry import async_retry, RetryConfig
        from src.utils.logger import log_api_request, log_api_response, log_error
        
        if not self.session:
            await self.initialize()
            
        # Check rate limit
        if not rate_limiter.allow_request("/captcha"):
            logger.warning("Rate limit exceeded for captcha API")
            raise APIRequestError("Rate limit exceeded for captcha API")
        
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
        
        # Generate request ID for correlation
        request_id = None
        
        @async_retry(retry_config=retry_config)
        async def _make_request():
            nonlocal request_id
            
            # Log API request
            request_id = log_api_request(
                logger,
                method="POST",
                url=url,
                headers={"Content-Type": "application/json"},
                body=data
            )
            
            start_time = time.time()
            
            try:
                async with self.session.post(url, json=data) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    # Log API response
                    log_api_response(
                        logger,
                        status_code=response.status,
                        response_body=response_data,
                        elapsed=response_time,
                        request_id=request_id
                    )
                    
                    if response.status == 200:
                        if isinstance(response_data, dict):
                            return response_data
                        else:
                            return {"success": False, "message": "Invalid JSON response"}
                    else:
                        error_text = response_data if isinstance(response_data, str) else json.dumps(response_data)
                        error_msg = f"Captcha API error: {response.status} - {error_text}"
                        logger.error(error_msg, request_id=request_id)
                        raise APIRequestError(error_msg)
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                error_msg = f"Captcha API request failed: {str(e)}"
                logger.error(error_msg, request_id=request_id)
                raise APIRequestError(error_msg)
        
        try:
            return await _make_request()
        except Exception as e:
            log_error(
                logger,
                error=e,
                context={"url": url, "data": data},
                request_id=request_id
            )
            raise APIRequestError(f"Failed to send captcha API request after retries: {str(e)}")

# Create a global captcha service instance
captcha_service = CaptchaService()
