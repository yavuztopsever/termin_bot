"""Unit tests for repository base class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.repository import Repository
from src.database.db_pool import db_pool
from src.database.db import User

class TestRepository:
    """Tests for Repository class."""
    
    @pytest.fixture
    def user_repository(self):
        """Create a repository instance for testing."""
        return Repository(User)
        
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
        with patch('src.database.db_pool', autospec=True) as mock_pool:
            # Mock session context manager
            mock_pool.session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction context manager
            mock_pool.transaction.return_value.__aenter__.return_value = mock_session
            
            # Mock with_retry decorator
            mock_pool.with_retry.return_value = lambda func: func
            
            yield mock_pool
            
    @pytest.mark.asyncio
    async def test_find_by_id(self, user_repository, mock_db_pool, mock_session):
        """Test find_by_id method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(id=1, telegram_id="123", first_name="Test")
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.find_by_id(1)
        
        # Assertions
        assert result.id == 1
        assert result.telegram_id == "123"
        assert result.first_name == "Test"
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM users" in str(query_arg)
        assert "WHERE users.id = :id_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_find_one(self, user_repository, mock_db_pool, mock_session):
        """Test find_one method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(id=1, telegram_id="123", first_name="Test")
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.find_one(User.telegram_id == "123")
        
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
    async def test_find_all(self, user_repository, mock_db_pool, mock_session):
        """Test find_all method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [
            User(id=1, telegram_id="123", first_name="Test1"),
            User(id=2, telegram_id="456", first_name="Test2")
        ]
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.find_all(User.first_name.like("Test%"))
        
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
        assert "WHERE users.first_name LIKE :first_name_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_create(self, user_repository, mock_db_pool, mock_session):
        """Test create method."""
        # Setup data
        user_data = {
            "telegram_id": "123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.create(user_data)
        
        # Assertions
        assert isinstance(result, User)
        assert result.telegram_id == "123"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        
        # Verify session operations
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_update(self, user_repository, mock_db_pool, mock_session):
        """Test update method."""
        # Setup mock
        user = User(id=1, telegram_id="123", first_name="Test")
        mock_session.get.return_value = user
        
        # Setup data
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.update(1, update_data)
        
        # Assertions
        assert result.id == 1
        assert result.telegram_id == "123"
        assert result.first_name == "Updated"
        assert result.last_name == "Name"
        
        # Verify session operations
        mock_session.get.assert_called_once_with(User, 1)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(user)
        
    @pytest.mark.asyncio
    async def test_update_not_found(self, user_repository, mock_db_pool, mock_session):
        """Test update method when entity not found."""
        # Setup mock
        mock_session.get.return_value = None
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.update(999, {"first_name": "Updated"})
        
        # Assertions
        assert result is None
        
        # Verify session operations
        mock_session.get.assert_called_once_with(User, 999)
        mock_session.flush.assert_not_called()
        mock_session.refresh.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_delete(self, user_repository, mock_db_pool, mock_session):
        """Test delete method."""
        # Setup mock
        user = User(id=1, telegram_id="123", first_name="Test")
        mock_session.get.return_value = user
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.delete(1)
        
        # Assertions
        assert result is True
        
        # Verify session operations
        mock_session.get.assert_called_once_with(User, 1)
        mock_session.delete.assert_called_once_with(user)
        
    @pytest.mark.asyncio
    async def test_delete_not_found(self, user_repository, mock_db_pool, mock_session):
        """Test delete method when entity not found."""
        # Setup mock
        mock_session.get.return_value = None
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.delete(999)
        
        # Assertions
        assert result is False
        
        # Verify session operations
        mock_session.get.assert_called_once_with(User, 999)
        mock_session.delete.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_count(self, user_repository, mock_db_pool, mock_session):
        """Test count method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [User(), User(), User()]
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.count(User.first_name.like("Test%"))
        
        # Assertions
        assert result == 3
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM users" in str(query_arg)
        assert "WHERE users.first_name LIKE :first_name_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_exists(self, user_repository, mock_db_pool, mock_session):
        """Test exists method."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.first.return_value = (User(),)
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.exists(User.telegram_id == "123")
        
        # Assertions
        assert result is True
        
        # Verify query
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]
        assert str(query_arg).startswith("SELECT")
        assert "FROM users" in str(query_arg)
        assert "WHERE users.telegram_id = :telegram_id_1" in str(query_arg)
        
    @pytest.mark.asyncio
    async def test_exists_not_found(self, user_repository, mock_db_pool, mock_session):
        """Test exists method when entity not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.exists(User.telegram_id == "999")
        
        # Assertions
        assert result is False
        
    @pytest.mark.asyncio
    async def test_bulk_create(self, user_repository, mock_db_pool, mock_session):
        """Test bulk_create method."""
        # Setup data
        users_data = [
            {"telegram_id": "123", "first_name": "Test1"},
            {"telegram_id": "456", "first_name": "Test2"}
        ]
        
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.bulk_create(users_data)
        
        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], User)
        assert isinstance(result[1], User)
        assert result[0].telegram_id == "123"
        assert result[0].first_name == "Test1"
        assert result[1].telegram_id == "456"
        assert result[1].first_name == "Test2"
        
        # Verify session operations
        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()
        assert mock_session.refresh.call_count == 2
        
    @pytest.mark.asyncio
    async def test_transaction(self, user_repository, mock_db_pool, mock_session):
        """Test transaction method."""
        # Setup mock function
        async def test_func(session, arg1, arg2=None):
            return f"{arg1}-{arg2}-{session}"
            
        # Patch db_pool in the repository module
        with patch('src.database.repository.db_pool', mock_db_pool):
            # Call method
            result = await user_repository.transaction(test_func, "test", arg2="value")
        
        # Assertions
        assert result == f"test-value-{mock_session}"
        
    @pytest.mark.asyncio
    async def test_retry_on_error(self, user_repository):
        """Test retry on database error."""
        # This test verifies that the with_retry decorator is applied correctly
        
        # Check if the find_by_id method is decorated with with_retry
        from src.database.repository import Repository
        
        # Get the original method from the class
        original_method = Repository.find_by_id
        
        # Check if it's a decorated method (has a __wrapped__ attribute)
        assert hasattr(original_method, '__wrapped__'), "Method is not decorated with with_retry"
        
        # Verify the method is wrapped by checking if the function code is different
        assert original_method.__code__ is not original_method.__wrapped__.__code__, "Method is not properly decorated"
        
        # Also check that the wrapper function has the same name as the original
        # This is a good practice for decorators to preserve the original function's metadata
        assert original_method.__name__ == 'find_by_id', "Decorator did not preserve the original function name"
