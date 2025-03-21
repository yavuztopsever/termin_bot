"""Unit tests for retry utilities."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.retry import RetryConfig, async_retry, retry_async_call
from src.utils.logger import get_correlation_id, set_correlation_id

class TestRetryConfig:
    """Tests for RetryConfig class."""
    
    def test_init(self):
        """Test initialization."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=30.0,
            backoff_factor=3.0,
            jitter=True,
            jitter_factor=0.2,
            retry_on_exceptions=(ValueError, TypeError),
            retry_on_status_codes=(500, 502)
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 3.0
        assert config.jitter is True
        assert config.jitter_factor == 0.2
        assert config.retry_on_exceptions == (ValueError, TypeError)
        assert config.retry_on_status_codes == (500, 502)
        
    def test_calculate_delay(self):
        """Test delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            jitter=False
        )
        
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0
        assert config.calculate_delay(4) == 10.0  # Max delay
        
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            jitter=True,
            jitter_factor=0.5
        )
        
        # With jitter, we can only test that the delay is within expected range
        delay = config.calculate_delay(1)  # Expected base: 2.0
        assert 1.0 <= delay <= 3.0  # 2.0 +/- 50%

class TestAsyncRetry:
    """Tests for async_retry decorator."""
    
    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = AsyncMock(return_value="success")
        
        @async_retry()
        async def test_func():
            return await mock_func()
            
        result = await test_func()
        
        assert result == "success"
        mock_func.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """Test retry on exception."""
        mock_func = AsyncMock(side_effect=[ValueError("Error"), "success"])
        
        @async_retry(retry_config=RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Small delay for tests
            retry_on_exceptions=(ValueError,)
        ))
        async def test_func():
            return await mock_func()
            
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
        
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test max retries exceeded."""
        mock_func = AsyncMock(side_effect=ValueError("Error"))
        
        @async_retry(retry_config=RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Small delay for tests
            retry_on_exceptions=(ValueError,)
        ))
        async def test_func():
            return await mock_func()
            
        with pytest.raises(ValueError, match="Error"):
            await test_func()
            
        assert mock_func.call_count == 4  # Initial + 3 retries
        
    @pytest.mark.asyncio
    async def test_retry_on_status_code(self):
        """Test retry on status code."""
        # Create a mock response object with a status attribute
        response1 = MagicMock()
        response1.status = 500
        
        response2 = MagicMock()
        response2.status = 200
        
        mock_func = AsyncMock(side_effect=[response1, response2])
        
        @async_retry(retry_config=RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Small delay for tests
            retry_on_status_codes=(500,)
        ))
        async def test_func():
            return await mock_func()
            
        result = await test_func()
        
        assert result == response2
        assert mock_func.call_count == 2
        
    @pytest.mark.asyncio
    async def test_correlation_id_preserved(self):
        """Test correlation ID is preserved across retries."""
        # Set a correlation ID
        test_correlation_id = "test-correlation-id"
        set_correlation_id(test_correlation_id)
        
        # Mock function that checks correlation ID
        async def check_correlation_id():
            assert get_correlation_id() == test_correlation_id
            raise ValueError("Force retry")
            
        mock_func = AsyncMock(side_effect=check_correlation_id)
        
        @async_retry(retry_config=RetryConfig(
            max_retries=2,
            base_delay=0.01,
            retry_on_exceptions=(ValueError,)
        ))
        async def test_func():
            return await mock_func()
            
        with pytest.raises(ValueError):
            await test_func()
            
        assert mock_func.call_count == 3  # Initial + 2 retries

class TestRetryAsyncCall:
    """Tests for retry_async_call function."""
    
    @pytest.mark.asyncio
    async def test_retry_async_call(self):
        """Test retry_async_call function."""
        mock_func = AsyncMock(side_effect=[ValueError("Error"), "success"])
        
        result = await retry_async_call(
            mock_func,
            retry_config=RetryConfig(
                max_retries=3,
                base_delay=0.01,
                retry_on_exceptions=(ValueError,)
            )
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
        
    @pytest.mark.asyncio
    async def test_retry_async_call_with_args(self):
        """Test retry_async_call function with arguments."""
        mock_func = AsyncMock(side_effect=[ValueError("Error"), "success"])
        
        result = await retry_async_call(
            mock_func,
            "arg1",
            "arg2",
            retry_config=RetryConfig(
                max_retries=3,
                base_delay=0.01,
                retry_on_exceptions=(ValueError,)
            ),
            kwarg1="value1"
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
        mock_func.assert_called_with("arg1", "arg2", kwarg1="value1")
