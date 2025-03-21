"""Integration tests for the user service."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from src.models import User, Subscription
from src.services.user import UserService
from src.services.subscription import SubscriptionService

@pytest.mark.asyncio
async def test_create_user(
    mongodb,
    redis_client,
    clean_db
):
    """Test user creation."""
    user_service = UserService()
    
    # Create test user
    user_data = {
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    }
    
    user = await user_service.create_user(user_data)
    
    # Verify user was created
    assert user is not None
    assert user.telegram_id == user_data["telegram_id"]
    assert user.username == user_data["username"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]
    assert user.language_code == user_data["language_code"]
    
    # Verify user in database
    db_user = await mongodb.users.find_one({"telegram_id": user_data["telegram_id"]})
    assert db_user is not None
    assert str(db_user["_id"]) == user.id

@pytest.mark.asyncio
async def test_get_user(
    mongodb,
    redis_client,
    clean_db
):
    """Test retrieving a user."""
    user_service = UserService()
    
    # Create test user
    user_data = {
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    }
    
    created_user = await user_service.create_user(user_data)
    
    # Get user by ID
    user = await user_service.get_user(created_user.id)
    assert user is not None
    assert user.id == created_user.id
    
    # Get user by Telegram ID
    user = await user_service.get_user_by_telegram_id(user_data["telegram_id"])
    assert user is not None
    assert user.telegram_id == user_data["telegram_id"]
    
    # Get non-existent user
    user = await user_service.get_user("non_existent_id")
    assert user is None

@pytest.mark.asyncio
async def test_update_user(
    mongodb,
    redis_client,
    clean_db
):
    """Test updating user information."""
    user_service = UserService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Update user data
    updated_data = {
        "username": "updated_user",
        "first_name": "Updated",
        "last_name": "Name",
        "language_code": "de"
    }
    
    updated_user = await user_service.update_user(user.id, updated_data)
    
    # Verify updates
    assert updated_user.username == updated_data["username"]
    assert updated_user.first_name == updated_data["first_name"]
    assert updated_user.last_name == updated_data["last_name"]
    assert updated_user.language_code == updated_data["language_code"]
    
    # Verify in database
    db_user = await mongodb.users.find_one({"_id": user.id})
    assert db_user["username"] == updated_data["username"]
    assert db_user["first_name"] == updated_data["first_name"]
    assert db_user["last_name"] == updated_data["last_name"]
    assert db_user["language_code"] == updated_data["language_code"]

@pytest.mark.asyncio
async def test_delete_user(
    mongodb,
    redis_client,
    clean_db
):
    """Test user deletion."""
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Create test subscription
    subscription = await subscription_service.create_subscription({
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    })
    
    # Delete user
    success = await user_service.delete_user(user.id)
    assert success is True
    
    # Verify user was deleted
    db_user = await mongodb.users.find_one({"_id": user.id})
    assert db_user is None
    
    # Verify associated subscriptions were deleted
    db_subscription = await mongodb.subscriptions.find_one({"user_id": user.id})
    assert db_subscription is None

@pytest.mark.asyncio
async def test_user_preferences(
    mongodb,
    redis_client,
    clean_db
):
    """Test user preferences management."""
    user_service = UserService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Set preferences
    preferences = {
        "notification_enabled": True,
        "notification_time": "09:00",
        "preferred_language": "en",
        "time_zone": "Europe/Berlin"
    }
    
    updated_user = await user_service.update_preferences(user.id, preferences)
    
    # Verify preferences were updated
    assert updated_user.preferences == preferences
    
    # Verify in database
    db_user = await mongodb.users.find_one({"_id": user.id})
    assert db_user["preferences"] == preferences
    
    # Update single preference
    updated_user = await user_service.update_preferences(
        user.id,
        {"notification_enabled": False}
    )
    
    # Verify single preference update
    assert updated_user.preferences["notification_enabled"] is False
    assert updated_user.preferences["notification_time"] == "09:00"
    
    # Get preferences
    user_preferences = await user_service.get_preferences(user.id)
    assert user_preferences == updated_user.preferences

@pytest.mark.asyncio
async def test_user_activity(
    mongodb,
    redis_client,
    clean_db
):
    """Test user activity tracking."""
    user_service = UserService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Record activities
    activities = [
        {"type": "login", "details": {"ip": "127.0.0.1"}},
        {"type": "subscription_created", "details": {"service_id": "test"}},
        {"type": "appointment_booked", "details": {"appointment_id": "test"}}
    ]
    
    for activity in activities:
        await user_service.record_activity(user.id, activity)
    
    # Get user activities
    user_activities = await user_service.get_user_activities(user.id)
    assert len(user_activities) == 3
    
    # Verify activity order (most recent first)
    assert user_activities[0]["type"] == "appointment_booked"
    assert user_activities[1]["type"] == "subscription_created"
    assert user_activities[2]["type"] == "login"
    
    # Test activity filtering
    login_activities = await user_service.get_user_activities(
        user.id,
        activity_type="login"
    )
    assert len(login_activities) == 1
    assert login_activities[0]["type"] == "login"
    
    # Test activity pagination
    page1 = await user_service.get_user_activities(user.id, limit=2, skip=0)
    assert len(page1) == 2
    
    page2 = await user_service.get_user_activities(user.id, limit=2, skip=2)
    assert len(page2) == 1 