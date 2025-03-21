"""Unit tests for repository implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.db import User, Subscription, Appointment, Notification, WebsiteConfig
from src.database.repositories import (
    UserRepository,
    SubscriptionRepository,
    AppointmentRepository,
    NotificationRepository,
    WebsiteConfigRepository
)
from src.database.db_pool import db_pool

class TestUserRepository:
    """Tests for UserRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        return UserRepository()
        
    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.close = AsyncMock()
        return session
        
    @pytest.fixture
    def mock_db_pool(self, mock_session):
        """Mock the database pool."""
        with patch('src.database.db_pool.db_pool') as mock_pool:
            # Mock session context manager
            mock_pool.session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction context manager
            mock_pool.transaction.return_value.__aenter__.return_value = mock_session
            
            # Mock with_retry decorator
            mock_pool.with_retry.return_value = lambda func: func
            
            yield mock_pool
            
    @pytest.mark.asyncio
    async def test_find_by_telegram_id(self, repository, mock_db_pool, mock_session):
        """Test find_by_telegram_id method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(id=1, telegram_id="123", first_name="Test")
        mock_session.execute.return_value = mock_result
        
        # Call method
        result = await repository.find_by_telegram_id("123")
        
        # Assertions
        assert result.id == 1
        assert result.telegram_id == "123"
        assert result.first_name == "Test"
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM users" in str(query_arg)
        assert "WHERE users.telegram_id = :telegram_id_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_get_users_with_active_subscriptions(self, repository, mock_db_pool, mock_session):
        """Test get_users_with_active_subscriptions method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [
            User(id=1, telegram_id="123", first_name="Test1"),
            User(id=2, telegram_id="456", first_name="Test2")
        ]
        mock_session.execute.return_value = mock_result
        
        # Call method
        with patch('src.database.repositories.db_pool', mock_db_pool):
            result = await repository.get_users_with_active_subscriptions()
        
        # Assertions
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].telegram_id == "123"
        assert result[0].first_name == "Test1"
        assert result[1].id == 2
        assert result[1].telegram_id == "456"
        assert result[1].first_name == "Test2"
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM users" in str(query_arg)
        assert "JOIN subscriptions" in str(query_arg)
        assert "WHERE subscriptions.status = :status_1" in str(query_arg)
        assert "DISTINCT" in str(query_arg).upper()

class TestSubscriptionRepository:
    """Tests for SubscriptionRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        return SubscriptionRepository()
        
    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.close = AsyncMock()
        return session
        
    @pytest.fixture
    def mock_db_pool(self, mock_session):
        """Mock the database pool."""
        with patch('src.database.db_pool.db_pool') as mock_pool:
            # Mock session context manager
            mock_pool.session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction context manager
            mock_pool.transaction.return_value.__aenter__.return_value = mock_session
            
            # Mock with_retry decorator
            mock_pool.with_retry.return_value = lambda func: func
            
            yield mock_pool
            
    @pytest.mark.asyncio
    async def test_find_active_subscriptions(self, repository, mock_db_pool, mock_session):
        """Test find_active_subscriptions method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [
            Subscription(id=1, user_id=1, service_id="service1", status="active"),
            Subscription(id=2, user_id=2, service_id="service2", status="active")
        ]
        mock_session.execute.return_value = mock_result
        
        # Call method
        result = await repository.find_active_subscriptions()
        
        # Assertions
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].user_id == 1
        assert result[0].service_id == "service1"
        assert result[0].status == "active"
        assert result[1].id == 2
        assert result[1].user_id == 2
        assert result[1].service_id == "service2"
        assert result[1].status == "active"
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM subscriptions" in str(query_arg)
        assert "WHERE subscriptions.status = :status_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_deactivate_subscription(self, repository, mock_db_pool, mock_session):
        """Test deactivate_subscription method."""
        # Setup mock
        subscription = Subscription(id=1, user_id=1, service_id="service1", status="active")
        mock_session.get.return_value = subscription
        
        # Call method
        result = await repository.deactivate_subscription(1)
        
        # Assertions
        assert result.id == 1
        assert result.user_id == 1
        assert result.service_id == "service1"
        assert result.status == "inactive"  # Status should be updated
        
        # Verify session operations
        mock_session.get.assert_called_once_with(Subscription, 1)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(subscription)

class TestWebsiteConfigRepository:
    """Tests for WebsiteConfigRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        return WebsiteConfigRepository()
        
    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.close = AsyncMock()
        return session
        
    @pytest.fixture
    def mock_db_pool(self, mock_session):
        """Mock the database pool."""
        with patch('src.database.db_pool.db_pool') as mock_pool:
            # Mock session context manager
            mock_pool.session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction context manager
            mock_pool.transaction.return_value.__aenter__.return_value = mock_session
            
            # Mock with_retry decorator
            mock_pool.with_retry.return_value = lambda func: func
            
            yield mock_pool
            
    @pytest.mark.asyncio
    async def test_get_latest_config(self, repository, mock_db_pool, mock_session):
        """Test get_latest_config method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = WebsiteConfig(
            id=1,
            service_id="service1",
            location_id="location1",
            url="https://example.com",
            api_endpoints={"check": "/api/check", "book": "/api/book"},
            updated_at=datetime.utcnow()
        )
        mock_session.execute.return_value = mock_result
        
        # Call method
        with patch('src.database.repositories.db_pool', mock_db_pool):
            result = await repository.get_latest_config()
        
        # Assertions
        assert result.id == 1
        assert result.service_id == "service1"
        assert result.location_id == "location1"
        assert result.url == "https://example.com"
        assert result.api_endpoints == {"check": "/api/check", "book": "/api/book"}
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM website_config" in str(query_arg)
        assert "ORDER BY website_config.updated_at DESC" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_update_config_existing(self, repository, mock_db_pool, mock_session):
        """Test update_config method with existing config."""
        # Setup mock for get_latest_config
        existing_config = WebsiteConfig(
            id=1,
            service_id="service1",
            location_id="location1",
            url="https://example.com",
            api_endpoints={"check": "/api/check", "book": "/api/book"},
            updated_at=datetime.utcnow()
        )
        
        # Setup mock for update
        mock_session.get.return_value = existing_config
        
        # Setup data
        config_data = {
            "service_id": "service2",
            "location_id": "location2",
            "url": "https://example2.com",
            "api_endpoints": {"check": "/api/v2/check", "book": "/api/v2/book"}
        }
        
        # Mock get_latest_config to return existing config
        with patch.object(repository, 'get_latest_config', return_value=existing_config):
            # Mock update to return updated config
            with patch.object(repository, 'update', return_value=WebsiteConfig(id=1, **config_data)):
                # Call method
                result = await repository.update_config(config_data)
        
        # Assertions
        assert result.id == 1
        assert result.service_id == "service2"
        assert result.location_id == "location2"
        assert result.url == "https://example2.com"
        assert result.api_endpoints == {"check": "/api/v2/check", "book": "/api/v2/book"}
        
    @pytest.mark.asyncio
    async def test_update_config_new(self, repository, mock_db_pool, mock_session):
        """Test update_config method with new config."""
        # Setup data
        config_data = {
            "service_id": "service1",
            "location_id": "location1",
            "url": "https://example.com",
            "api_endpoints": {"check": "/api/check", "book": "/api/book"}
        }
        
        # Mock get_latest_config to return None
        with patch.object(repository, 'get_latest_config', return_value=None):
            # Mock create to return new config
            with patch.object(repository, 'create', return_value=WebsiteConfig(id=1, **config_data)):
                # Call method
                result = await repository.update_config(config_data)
        
        # Assertions
        assert result.id == 1
        assert result.service_id == "service1"
        assert result.location_id == "location1"
        assert result.url == "https://example.com"
        assert result.api_endpoints == {"check": "/api/check", "book": "/api/book"}
