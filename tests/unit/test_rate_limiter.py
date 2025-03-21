"""Unit tests for rate limiter."""

import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import asyncio

from src.utils.rate_limiter import (
    RateLimiter,
    rate_limited,
    RateLimitExceeded
)
from src.config.config import API_RATE_LIMITS
from src.monitoring.metrics import metrics_manager

class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        with patch('src.utils.rate_limiter.API_RATE_LIMITS', {
            '/api/v1/check': {'rate': 5, 'burst': 10},
            '/api/v1/book': {'rate': 2, 'burst': 5}
        }):
            return RateLimiter()
    
    def test_allow_request(self, rate_limiter):
        """Test request allowance."""
        # First request should be allowed
        assert rate_limiter.allow_request('/api/v1/check')
        
        # Should be able to make multiple requests up to burst limit
        for _ in range(9):  # 10 total (1 initial + 9 more)
            assert rate_limiter.allow_request('/api/v1/check')
        
        # Next request should be rate limited
        assert not rate_limiter.allow_request('/api/v1/check')
    
    def test_rate_limit_enforcement(self, rate_limiter):
        """Test rate limit enforcement."""
        # Make many requests quickly
        for _ in range(10):  # Use burst limit
            rate_limiter.allow_request('/api/v1/check')
        
        # Should be rate limited
        assert not rate_limiter.allow_request('/api/v1/check')
    
    def test_multiple_endpoints(self, rate_limiter):
        """Test rate limiting for multiple endpoints."""
        # Make requests to different endpoints
        assert rate_limiter.allow_request('/api/v1/check')
        assert rate_limiter.allow_request('/api/v1/book')
        
        # Rate limits should be enforced independently
        for _ in range(9):  # 10 total for check endpoint
            rate_limiter.allow_request('/api/v1/check')
        
        assert not rate_limiter.allow_request('/api/v1/check')
        assert rate_limiter.allow_request('/api/v1/book')
    
    def test_token_refill(self, rate_limiter):
        """Test token refill over time."""
        # Consume all tokens
        for _ in range(10):  # Use burst limit
            rate_limiter.allow_request('/api/v1/check')
        
        # Wait for refill
        time.sleep(0.2)  # Should refill 1 token (5 tokens/sec * 0.2 sec)
        
        # Should have 1 token available
        assert rate_limiter.allow_request('/api/v1/check')
        assert not rate_limiter.allow_request('/api/v1/check')
    
    def test_burst_limit(self, rate_limiter):
        """Test burst limit."""
        # Consume all tokens
        for _ in range(10):  # Use burst limit
            rate_limiter.allow_request('/api/v1/check')
        
        # Wait for a long time
        time.sleep(1.0)
        
        # Should still be limited by burst size
        assert rate_limiter.allow_request('/api/v1/check')
        assert rate_limiter.allow_request('/api/v1/check')
        assert not rate_limiter.allow_request('/api/v1/check')

class TestRateLimitedDecorator:
    """Test cases for rate_limited decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test rate limited asynchronous function."""
        endpoint = "test_endpoint"
        
        @rate_limited(endpoint)
        async def test_func():
            return "success"
        
        # First call should succeed
        assert await test_func() == "success"
        
        # Make many calls quickly
        for _ in range(10):  # Use burst limit
            await test_func()
        
        # Should be rate limited
        with pytest.raises(RateLimitExceeded):
            await test_func()
    
    def test_sync_function(self):
        """Test rate limited synchronous function."""
        endpoint = "test_endpoint"
        
        @rate_limited(endpoint)
        def test_func():
            return "success"
        
        # First call should succeed
        assert test_func() == "success"
        
        # Make many calls quickly
        for _ in range(10):  # Use burst limit
            test_func()
        
        # Should be rate limited
        with pytest.raises(RateLimitExceeded):
            test_func()

    @patch('src.monitoring.metrics.metrics_manager')
    def test_metrics_recording(self, mock_metrics):
        """Test that metrics are properly recorded."""
        endpoint = "test_endpoint"
        
        @rate_limited(endpoint)
        def test_func():
            return "success"
        
        # Make a request
        test_func()
        
        # Verify metrics were updated
        mock_metrics.increment.assert_called_with("rate_limit_requests", tags={"endpoint": endpoint})
        mock_metrics.increment.assert_not_called_with("rate_limit_exceeded", tags={"endpoint": endpoint})
        
        # Make many requests to trigger rate limit
        for _ in range(10):
            test_func()
        
        # Verify rate limit hit was recorded
        mock_metrics.increment.assert_called_with("rate_limit_exceeded", tags={"endpoint": endpoint})

if __name__ == "__main__":
    unittest.main() 