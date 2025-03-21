"""Integration tests for the subscription service."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from src.models import User, Subscription
from src.services.user import UserService
from src.services.subscription import SubscriptionService

@pytest.mark.asyncio
async def test_create_subscription(
    mongodb,
    redis_client,
    clean_db
):
    """Test subscription creation."""
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
    
    # Create subscription
    subscription_data = {
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    }
    
    subscription = await subscription_service.create_subscription(subscription_data)
    
    # Verify subscription was created
    assert subscription is not None
    assert subscription.user_id == user.id
    assert subscription.service_id == subscription_data["service_id"]
    assert subscription.location_id == subscription_data["location_id"]
    assert subscription.status == "active"
    
    # Verify subscription in database
    db_subscription = await mongodb.subscriptions.find_one({
        "user_id": user.id,
        "service_id": subscription_data["service_id"]
    })
    assert db_subscription is not None

@pytest.mark.asyncio
async def test_get_subscription(
    mongodb,
    redis_client,
    clean_db
):
    """Test retrieving a subscription."""
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    # Create test user and subscription
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    subscription_data = {
        "user_id": user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    }
    
    created_subscription = await subscription_service.create_subscription(subscription_data)
    
    # Get subscription by ID
    subscription = await subscription_service.get_subscription(created_subscription.id)
    assert subscription is not None
    assert subscription.id == created_subscription.id
    
    # Get user's subscriptions
    user_subscriptions = await subscription_service.get_user_subscriptions(user.id)
    assert len(user_subscriptions) == 1
    assert user_subscriptions[0].id == created_subscription.id
    
    # Get non-existent subscription
    subscription = await subscription_service.get_subscription("non_existent_id")
    assert subscription is None

@pytest.mark.asyncio
async def test_update_subscription(
    mongodb,
    redis_client,
    clean_db
):
    """Test updating subscription information."""
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    # Create test user and subscription
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
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
    
    # Update subscription
    updated_data = {
        "date_to": (datetime.now() + timedelta(days=60)).date(),
        "time_from": "10:00",
        "time_to": "16:00",
        "status": "paused"
    }
    
    updated_subscription = await subscription_service.update_subscription(
        subscription.id,
        updated_data
    )
    
    # Verify updates
    assert updated_subscription.date_to == updated_data["date_to"]
    assert updated_subscription.time_from == updated_data["time_from"]
    assert updated_subscription.time_to == updated_data["time_to"]
    assert updated_subscription.status == updated_data["status"]
    
    # Verify in database
    db_subscription = await mongodb.subscriptions.find_one({"_id": subscription.id})
    assert db_subscription["status"] == updated_data["status"]
    assert db_subscription["time_from"] == updated_data["time_from"]
    assert db_subscription["time_to"] == updated_data["time_to"]

@pytest.mark.asyncio
async def test_delete_subscription(
    mongodb,
    redis_client,
    clean_db
):
    """Test subscription deletion."""
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    # Create test user and subscription
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
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
    
    # Delete subscription
    success = await subscription_service.delete_subscription(subscription.id)
    assert success is True
    
    # Verify subscription was deleted
    db_subscription = await mongodb.subscriptions.find_one({"_id": subscription.id})
    assert db_subscription is None

@pytest.mark.asyncio
async def test_subscription_status_management(
    mongodb,
    redis_client,
    clean_db
):
    """Test subscription status management."""
    user_service = UserService()
    subscription_service = SubscriptionService()
    
    # Create test user and subscription
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
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
    
    # Test status transitions
    status_transitions = [
        ("active", "paused"),
        ("paused", "resumed"),
        ("resumed", "completed"),
        ("completed", "archived")
    ]
    
    for current_status, new_status in status_transitions:
        updated_subscription = await subscription_service.update_subscription_status(
            subscription.id,
            new_status
        )
        assert updated_subscription.status == new_status
        
        # Verify in database
        db_subscription = await mongodb.subscriptions.find_one({"_id": subscription.id})
        assert db_subscription["status"] == new_status

@pytest.mark.asyncio
async def test_subscription_filtering(
    mongodb,
    redis_client,
    clean_db
):
    """Test subscription filtering and querying."""
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
    
    # Create multiple subscriptions
    subscriptions = []
    for i in range(5):
        subscription = await subscription_service.create_subscription({
            "user_id": user.id,
            "service_id": f"service_{i}",
            "location_id": f"location_{i % 2}",  # Two locations
            "date_from": datetime.now().date(),
            "date_to": (datetime.now() + timedelta(days=30)).date(),
            "time_from": "09:00",
            "time_to": "17:00",
            "status": "active" if i % 2 == 0 else "paused"
        })
        subscriptions.append(subscription)
    
    # Test filtering by location
    location_0_subs = await subscription_service.get_subscriptions_by_location("location_0")
    assert len(location_0_subs) == 3
    
    location_1_subs = await subscription_service.get_subscriptions_by_location("location_1")
    assert len(location_1_subs) == 2
    
    # Test filtering by status
    active_subs = await subscription_service.get_subscriptions_by_status("active")
    assert len(active_subs) == 3
    
    paused_subs = await subscription_service.get_subscriptions_by_status("paused")
    assert len(paused_subs) == 2
    
    # Test combined filtering
    active_location_0_subs = await subscription_service.get_subscriptions(
        location_id="location_0",
        status="active"
    )
    assert len(active_location_0_subs) == 2 