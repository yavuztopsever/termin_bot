"""Unit tests for the database module."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.db import (
    AsyncDatabase,
    User,
    Subscription,
    Appointment,
    Notification,
    WebsiteConfig
)

@pytest.fixture
async def mock_db():
    """Fixture to create a mock database."""
    db = AsyncMock(spec=AsyncDatabase)
    db.add_user = AsyncMock()
    db.get_user = AsyncMock()
    db.add_subscription = AsyncMock()
    db.get_active_subscriptions = AsyncMock()
    db.add_appointment = AsyncMock()
    db.add_notification = AsyncMock()
    db.get_website_config = AsyncMock()
    db.add_website_config = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_add_user(mock_db):
    """Test adding a new user."""
    db = await mock_db
    user_data = {
        'telegram_id': '123456789',
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'language_code': 'en'
    }
    
    mock_user = User(
        telegram_id='123456789',
        username='testuser',
        first_name='Test',
        last_name='User',
        language_code='en'
    )
    db.add_user.return_value = mock_user
    
    user = await db.add_user(user_data)
    assert user.telegram_id == '123456789'
    assert user.username == 'testuser'
    assert user.first_name == 'Test'
    assert user.last_name == 'User'
    assert user.language_code == 'en'
    db.add_user.assert_called_once_with(user_data)

@pytest.mark.asyncio
async def test_get_user(mock_db):
    """Test getting a user by telegram ID."""
    db = await mock_db
    mock_user = User(
        telegram_id='123456789',
        username='testuser',
        first_name='Test',
        last_name='User',
        language_code='en'
    )
    db.get_user.return_value = mock_user
    
    user = await db.get_user('123456789')
    assert user is not None
    assert user.telegram_id == '123456789'
    assert user.username == 'testuser'
    db.get_user.assert_called_once_with('123456789')

@pytest.mark.asyncio
async def test_add_subscription(mock_db):
    """Test adding a new subscription."""
    db = await mock_db
    mock_user = User(
        id=1,
        telegram_id='123456789',
        username='testuser',
        first_name='Test',
        last_name='User',
        language_code='en'
    )
    db.add_user.return_value = mock_user
    
    subscription_data = {
        'user_id': mock_user.id,
        'service_id': 'test_service',
        'location_id': 'test_location',
        'preferences': {'notify_on_available': True},
        'status': 'active'
    }
    
    mock_subscription = Subscription(**subscription_data)
    db.add_subscription.return_value = mock_subscription
    
    subscription = await db.add_subscription(subscription_data)
    assert subscription.user_id == mock_user.id
    assert subscription.service_id == 'test_service'
    assert subscription.location_id == 'test_location'
    assert subscription.preferences == {'notify_on_available': True}
    assert subscription.status == 'active'
    db.add_subscription.assert_called_once_with(subscription_data)

@pytest.mark.asyncio
async def test_get_active_subscriptions(mock_db):
    """Test getting all active subscriptions."""
    db = await mock_db
    mock_subscription = Subscription(
        user_id=1,
        service_id='test_service',
        location_id='test_location',
        preferences={'notify_on_available': True},
        status='active'
    )
    db.get_active_subscriptions.return_value = [mock_subscription]
    
    active_subscriptions = await db.get_active_subscriptions()
    assert len(active_subscriptions) == 1
    assert active_subscriptions[0].status == 'active'
    db.get_active_subscriptions.assert_called_once()

@pytest.mark.asyncio
async def test_add_appointment(mock_db):
    """Test adding a new appointment."""
    db = await mock_db
    mock_user = User(
        id=1,
        telegram_id='123456789',
        username='testuser',
        first_name='Test',
        last_name='User',
        language_code='en'
    )
    db.add_user.return_value = mock_user
    
    appointment_data = {
        'service_id': 'test_service',
        'location_id': 'test_location',
        'date': datetime.now(),
        'time': '10:00',
        'status': 'available',
        'user_id': mock_user.id
    }
    
    mock_appointment = Appointment(**appointment_data)
    db.add_appointment.return_value = mock_appointment
    
    appointment = await db.add_appointment(appointment_data)
    assert appointment.service_id == 'test_service'
    assert appointment.location_id == 'test_location'
    assert appointment.time == '10:00'
    assert appointment.status == 'available'
    assert appointment.user_id == mock_user.id
    db.add_appointment.assert_called_once_with(appointment_data)

@pytest.mark.asyncio
async def test_add_notification(mock_db):
    """Test adding a new notification."""
    db = await mock_db
    mock_user = User(
        id=1,
        telegram_id='123456789',
        username='testuser',
        first_name='Test',
        last_name='User',
        language_code='en'
    )
    db.add_user.return_value = mock_user
    
    notification_data = {
        'user_id': mock_user.id,
        'type': 'appointment_available',
        'message': 'An appointment is available!',
        'status': 'pending'
    }
    
    mock_notification = Notification(**notification_data)
    db.add_notification.return_value = mock_notification
    
    notification = await db.add_notification(notification_data)
    assert notification.user_id == mock_user.id
    assert notification.type == 'appointment_available'
    assert notification.message == 'An appointment is available!'
    assert notification.status == 'pending'
    db.add_notification.assert_called_once_with(notification_data)

@pytest.mark.asyncio
async def test_get_website_config(mock_db):
    """Test getting website configuration."""
    db = await mock_db
    config_data = {
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
    db.get_website_config.return_value = config_data
    
    config = await db.get_website_config()
    assert config is not None
    assert config['service_id'] == 'test_service'
    assert config['location_id'] == 'test_location'
    assert config['url'] == 'http://test.example.com'
    assert 'api_endpoints' in config
    assert 'check_availability' in config['api_endpoints']
    assert 'book_appointment' in config['api_endpoints']
    db.get_website_config.assert_called_once()

@pytest.mark.asyncio
async def test_add_website_config(mock_db):
    """Test adding website configuration."""
    db = await mock_db
    config_data = {
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
    
    mock_config = WebsiteConfig(**config_data)
    db.add_website_config.return_value = mock_config
    
    config = await db.add_website_config(config_data)
    assert config.service_id == 'test_service'
    assert config.location_id == 'test_location'
    assert config.url == 'http://test.example.com'
    assert config.api_endpoints == config_data['api_endpoints']
    db.add_website_config.assert_called_once_with(config_data) 