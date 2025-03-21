"""Unit tests for the configuration module."""

import os
import pytest
import importlib
from unittest.mock import patch, MagicMock
import asyncio
from src.config import config as config_module

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Fixture to set up test environment variables."""
    original_environ = dict(os.environ)
    mock_vars = {
        'API_BASE_URL': 'http://test.example.com',
        'API_KEY': 'test_api_key',
        'API_TIMEOUT': '60',
        'DEFAULT_RATE_LIMIT': '15.0',
        'DEFAULT_BURST_LIMIT': '30',
        'CHECK_RATE_LIMIT': '7.5',
        'CHECK_BURST_LIMIT': '15',
        'BOOK_RATE_LIMIT': '3.0',
        'BOOK_BURST_LIMIT': '6',
        'ANTI_BOT_ENABLED': 'true',
        'MAX_REQUESTS_PER_IP': '200',
        'WINDOW_SIZE': '7200',
        'BLOCK_DURATION': '172800',
        'IP_WHITELIST': '127.0.0.1,192.168.1.1',
        'IP_BLACKLIST': '10.0.0.1,10.0.0.2'
    }
    with patch.dict('os.environ', mock_vars, clear=True):
        # Reload the config module to apply new environment variables
        importlib.reload(config_module)
        yield

@pytest.fixture
def mock_db():
    """Fixture to mock the database."""
    mock_config = {
        'service_id': 'test_service',
        'location_id': 'test_location',
        'url': 'http://test.example.com',
        'api_endpoints': {
            'check_availability': {
                'url': '/api/check',
                'method': 'GET'
            },
            'book_appointment': {
                'url': '/api/book',
                'method': 'POST'
            }
        }
    }
    
    async def mock_get_website_config():
        return mock_config

    mock_db = MagicMock()
    mock_db.get_website_config = mock_get_website_config
    
    with patch('src.database.db.db.get_website_config', side_effect=mock_get_website_config):
        yield mock_db

def test_api_config_defaults():
    """Test default API configuration values."""
    with patch.dict('os.environ', {}, clear=True):
        importlib.reload(config_module)
        assert config_module.API_BASE_URL == 'http://localhost:8000'
        assert config_module.API_KEY == 'test_key'
        assert config_module.API_TIMEOUT == 30

def test_api_config_custom():
    """Test custom API configuration values."""
    assert config_module.API_BASE_URL == 'http://test.example.com'
    assert config_module.API_KEY == 'test_api_key'
    assert config_module.API_TIMEOUT == 60

def test_rate_limits_defaults():
    """Test default rate limit configuration."""
    with patch.dict('os.environ', {}, clear=True):
        importlib.reload(config_module)
        assert config_module.API_RATE_LIMITS['default']['rate'] == 10.0
        assert config_module.API_RATE_LIMITS['default']['burst'] == 20
        assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/check']['rate'] == 5.0
        assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/check']['burst'] == 10
        assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/book']['rate'] == 2.0
        assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/book']['burst'] == 5

def test_rate_limits_custom():
    """Test custom rate limit configuration."""
    assert config_module.API_RATE_LIMITS['default']['rate'] == 15.0
    assert config_module.API_RATE_LIMITS['default']['burst'] == 30
    assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/check']['rate'] == 7.5
    assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/check']['burst'] == 15
    assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/book']['rate'] == 3.0
    assert config_module.API_RATE_LIMITS['endpoints']['/api/v1/book']['burst'] == 6

def test_anti_bot_config_defaults():
    """Test default anti-bot configuration."""
    with patch.dict('os.environ', {}, clear=True):
        importlib.reload(config_module)
        assert config_module.ANTI_BOT_CONFIG['enabled'] is True
        assert config_module.ANTI_BOT_CONFIG['max_requests_per_ip'] == 100
        assert config_module.ANTI_BOT_CONFIG['window_size'] == 3600
        assert config_module.ANTI_BOT_CONFIG['block_duration'] == 86400
        assert config_module.ANTI_BOT_CONFIG['whitelist'] == ['']
        assert config_module.ANTI_BOT_CONFIG['blacklist'] == ['']

def test_anti_bot_config_custom():
    """Test custom anti-bot configuration."""
    assert config_module.ANTI_BOT_CONFIG['enabled'] is True
    assert config_module.ANTI_BOT_CONFIG['max_requests_per_ip'] == 200
    assert config_module.ANTI_BOT_CONFIG['window_size'] == 7200
    assert config_module.ANTI_BOT_CONFIG['block_duration'] == 172800
    assert config_module.ANTI_BOT_CONFIG['whitelist'] == ['127.0.0.1', '192.168.1.1']
    assert config_module.ANTI_BOT_CONFIG['blacklist'] == ['10.0.0.1', '10.0.0.2']

@pytest.mark.asyncio
async def test_load_website_config(mock_db):
    """Test loading website configuration."""
    result = await config_module.load_website_config()
    assert isinstance(result, dict)
    assert result['service_id'] == 'test_service'
    assert result['location_id'] == 'test_location'
    assert result['url'] == 'http://test.example.com'
    assert 'api_endpoints' in result
    assert 'check_availability' in result['api_endpoints']
    assert 'book_appointment' in result['api_endpoints'] 