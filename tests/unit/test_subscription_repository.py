"""Unit tests for the subscription repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.database.repositories import SubscriptionRepository
from src.database.db import Subscription, User

# Constants for subscription status
ACTIVE = "active"
INACTIVE = "inactive"
EXPIRED = "expired"
PENDING = "pending"

class TestSubscriptionRepository:
    """Test cases for the subscription repository."""

    @pytest.fixture
    def mock_db_pool(self):
        """Create a mock database pool."""
        with patch('src.database.repositories.db_pool') as mock:
            mock.session = AsyncMock()
            mock.transaction = AsyncMock()
            mock.with_retry = lambda: lambda x: x  # No-op decorator
            yield mock

    @pytest.fixture
    def repository(self, mock_db_pool):
        """Create a subscription repository."""
        return SubscriptionRepository()

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            telegram_id="123456789",
            username="test_user",
            first_name="Test",
            last_name="User",
            language_code="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            id=1
        )

    @pytest.fixture
    def sample_subscription(self):
        """Create a sample subscription for testing."""
        return Subscription(
            user_id=1,
            service_id="service_1",
            location_id="location_1",
            preferences={
                "date_from": datetime.utcnow().date(),
                "date_to": (datetime.utcnow() + timedelta(days=30)).date(),
                "time_from": "09:00",
                "time_to": "17:00"
            },
            status=ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            id=1
        )

    @pytest.mark.asyncio
    async def test_create_subscription(self, repository, mock_db_pool, sample_subscription):
        """Test creating a new subscription."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one.return_value = sample_subscription

        # Call method
        subscription_data = {
            "user_id": sample_subscription.user_id,
            "service_id": sample_subscription.service_id,
            "location_id": sample_subscription.location_id,
            "preferences": sample_subscription.preferences,
            "status": sample_subscription.status
        }
        result = await repository.create(subscription_data)

        # Assertions
        assert result == sample_subscription
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscription(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving a subscription by ID."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_subscription

        # Call method
        result = await repository.find_by_id(sample_subscription.id)

        # Assertions
        assert result == sample_subscription
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_user(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving subscriptions by user ID."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_by_user_id(sample_subscription.user_id)

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_subscriptions(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving active subscriptions."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_active_subscriptions()

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_subscription(self, repository, mock_db_pool, sample_subscription):
        """Test updating a subscription."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        updated_subscription = sample_subscription
        updated_subscription.status = INACTIVE
        mock_session.get.return_value = updated_subscription

        # Call method
        result = await repository.update(updated_subscription.id, {"status": INACTIVE})

        # Assertions
        assert result == updated_subscription
        assert result.status == INACTIVE
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_subscription(self, repository, mock_db_pool, sample_subscription):
        """Test deleting a subscription."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.get.return_value = sample_subscription

        # Call method
        result = await repository.delete(sample_subscription.id)

        # Assertions
        assert result is True
        mock_session.delete.assert_called_once_with(sample_subscription)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_service(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving subscriptions by service ID."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_all({"service_id": sample_subscription.service_id})

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_location(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving subscriptions by location ID."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_all({"location_id": sample_subscription.location_id})

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_date_range(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving subscriptions by date range."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_all({
            "preferences__date_from__gte": sample_subscription.preferences["date_from"],
            "preferences__date_to__lte": sample_subscription.preferences["date_to"]
        })

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_status(self, repository, mock_db_pool, sample_subscription):
        """Test retrieving subscriptions by status."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]

        # Call method
        result = await repository.find_all({"status": ACTIVE})

        # Assertions
        assert result == [sample_subscription]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_preferences(self, repository, mock_db_pool, sample_subscription):
        """Test getting subscriptions by preferences."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_pool.session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_subscription]
        
        # Call method
        preferences = {
            "time_ranges": [
                {"start": "09:00", "end": "17:00"}
            ],
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
        result = await repository.find_all({"preferences": preferences})
        
        # Assertions
        assert result == [sample_subscription]
        subscription_repository.db.session.scalars.assert_called_once() 