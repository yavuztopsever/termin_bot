from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from pathlib import Path
import re

from src.config.config import (
    BASE_URL,
    CAPTCHA_CONFIG
)
from src.database.db import db
from src.utils.logger import setup_logger
from src.api.api_config import api_config
from src.models import WebsiteConfig

logger = setup_logger(__name__)

class APIAnalyzer:
    """Analyzes the target website's API structure."""
    
    def __init__(self, debug_dir: str = "debug"):
        """Initialize API analyzer."""
        self.debug_dir = debug_dir
        self.network_logs: List[Dict[str, Any]] = []
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        
    async def analyze(self) -> Dict[str, Any]:
        """Analyze the API structure and return configuration."""
        logger.info("Starting API analysis")
        
        try:
            # Load network logs from debug directory
            await self._load_network_logs()
            
            # Analyze network logs to identify endpoints
            await self._analyze_network_logs()
            
            # Create API configuration
            config = await self._create_api_config()
            
            # Update API configuration in database
            await self._update_api_config(config)
            
            logger.info("API analysis completed successfully")
            return config
            
        except Exception as e:
            logger.error("API analysis failed", error=str(e))
            raise
            
    async def _load_network_logs(self) -> None:
        """Load network logs from debug directory."""
        try:
            network_dir = Path(self.debug_dir) / "network"
            
            if not network_dir.exists():
                logger.warning(f"Network debug directory not found: {network_dir}")
                return
                
            # Get all JSON files in the network directory
            json_files = list(network_dir.glob("*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        self.network_logs.append({
                            "file": file_path.name,
                            "data": data
                        })
                except Exception as e:
                    logger.warning(f"Failed to load network log file {file_path}: {e}")
                    continue
                    
            logger.info(f"Loaded {len(self.network_logs)} network log files")
            
        except Exception as e:
            logger.error(f"Failed to load network logs: {e}")
            raise
            
    async def _analyze_network_logs(self) -> None:
        """Analyze network logs to identify API endpoints."""
        try:
            # Identify unique endpoints
            for log in self.network_logs:
                try:
                    file_name = log["file"]
                    data = log["data"]
                    
                    # Extract endpoint from file name
                    match = re.search(r'GET__(.+?)\.json', file_name)
                    if match:
                        endpoint = "/" + match.group(1)
                        
                        # Store endpoint information
                        if endpoint not in self.endpoints:
                            self.endpoints[endpoint] = {
                                "url": f"{BASE_URL}/{endpoint}",
                                "method": "GET",
                                "parameters": self._extract_parameters(file_name),
                                "response_structure": self._analyze_response_structure(data)
                            }
                            
                except Exception as e:
                    logger.warning(f"Failed to analyze network log: {e}")
                    continue
                    
            logger.info(f"Identified {len(self.endpoints)} unique API endpoints")
            
        except Exception as e:
            logger.error(f"Failed to analyze network logs: {e}")
            raise
            
    def _extract_parameters(self, file_name: str) -> Dict[str, str]:
        """Extract query parameters from file name."""
        try:
            # Example: 2025-03-20T20-52-02.393Z_GET__buergeransicht_api_backend_available-days.json
            # Extract parameters from query string if present
            match = re.search(r'GET__(.+?)\.json', file_name)
            if not match:
                return {}
                
            endpoint = match.group(1)
            
            # Check if endpoint contains query parameters
            if "?" in endpoint:
                endpoint, query = endpoint.split("?", 1)
                params = {}
                
                for param in query.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        params[key] = value
                        
                return params
                
            return {}
            
        except Exception as e:
            logger.warning(f"Failed to extract parameters: {e}")
            return {}
            
    def _analyze_response_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of an API response."""
        try:
            # Create a template of the response structure
            template = {}
            
            for key, value in data.items():
                if isinstance(value, (int, float, bool)):
                    template[key] = type(value).__name__
                elif isinstance(value, str):
                    template[key] = "string"
                elif isinstance(value, list):
                    if value:
                        # Analyze the first item in the list
                        if isinstance(value[0], dict):
                            template[key] = [self._analyze_response_structure(value[0])]
                        else:
                            template[key] = [type(value[0]).__name__]
                    else:
                        template[key] = []
                elif isinstance(value, dict):
                    template[key] = self._analyze_response_structure(value)
                else:
                    template[key] = None
                    
            return template
            
        except Exception as e:
            logger.warning(f"Failed to analyze response structure: {e}")
            return {}
            
    async def _create_api_config(self) -> Dict[str, Any]:
        """Create API configuration from analyzed endpoints."""
        try:
            # Find key endpoints
            available_days_endpoint = None
            book_appointment_endpoint = None
            captcha_details_endpoint = None
            offices_services_endpoint = None
            
            for endpoint, info in self.endpoints.items():
                if "available-days" in endpoint:
                    available_days_endpoint = endpoint
                elif "book-appointment" in endpoint:
                    book_appointment_endpoint = endpoint
                elif "captcha-details" in endpoint:
                    captcha_details_endpoint = endpoint
                elif "offices-and-services" in endpoint:
                    offices_services_endpoint = endpoint
                    
            # Create configuration
            config = {
                "service_id": "1",  # Default service ID
                "location_id": "1",  # Default location ID
                "base_url": BASE_URL,
                "check_availability_endpoint": available_days_endpoint or "/buergeransicht/api/backend/available-days",
                "book_appointment_endpoint": book_appointment_endpoint or "/buergeransicht/api/backend/book-appointment",
                "captcha_endpoint": CAPTCHA_CONFIG["endpoints"]["verify"],
                "captcha_puzzle_endpoint": CAPTCHA_CONFIG["endpoints"]["puzzle"],
                "captcha_site_key": "FRIENDLYCAPTCHA_SITEKEY",  # This would be extracted from the HTML
                "captcha_enabled": True,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{BASE_URL}/buergerservice/terminvereinbarung.html",
                    "Origin": BASE_URL
                },
                "request_timeout": 30,
                "rate_limit": 10,
                "rate_limit_period": 60,
                "retry_count": 3,
                "retry_delay": 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create API configuration: {e}")
            raise
            
    async def _update_api_config(self, config: Dict[str, Any]) -> None:
        """Update the API configuration in the database."""
        try:
            # Create WebsiteConfig instance
            website_config = WebsiteConfig(**config)
            
            # Update database
            await api_config.update_config(config)
            
            logger.info("Updated API configuration in database")
            
        except Exception as e:
            logger.error(f"Failed to update API configuration: {e}")
            raise
            
async def run_analysis() -> Dict[str, Any]:
    """Run the API analysis."""
    analyzer = APIAnalyzer()
    return await analyzer.analyze()
