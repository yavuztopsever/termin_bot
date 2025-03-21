"""Integration tests for the notification service."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from telegram import Bot, Update, Message, Chat, User as TelegramUser

from src.models import User, Notification
from src.services.notification import NotificationService
from src.services.user import UserService

@pytest.mark.asyncio
async def test_send_notification(
    mongodb,
    redis_client,
    clean_db
):
    """Test sending a notification to a user."""
    # Create test user
    user_service = UserService()
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Initialize notification service
    notification_service = NotificationService()
    
    # Send test notification
    notification_data = {
        "user_id": user.id,
        "type": "test",
        "content": "Test notification",
        "priority": "normal"
    }
    
    notification = await notification_service.send_notification(notification_data)
    
    # Verify notification was created
    assert notification is not None
    assert notification.user_id == user.id
    assert notification.type == "test"
    assert notification.content == "Test notification"
    assert notification.status == "sent"
    
    # Verify notification in database
    db_notification = await mongodb.notifications.find_one({
        "user_id": user.id,
        "type": "test"
    })
    assert db_notification is not None

@pytest.mark.asyncio
async def test_notification_delivery_status(
    mongodb,
    redis_client,
    clean_db
):
    """Test notification delivery status tracking."""
    user_service = UserService()
    notification_service = NotificationService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Send notification
    notification = await notification_service.send_notification({
        "user_id": user.id,
        "type": "test",
        "content": "Test notification",
        "priority": "high"
    })
    
    # Update delivery status
    await notification_service.update_notification_status(
        notification.id,
        "delivered"
    )
    
    # Verify status update
    updated_notification = await mongodb.notifications.find_one({
        "_id": notification.id
    })
    assert updated_notification["status"] == "delivered"
    
    # Verify delivery timestamp
    assert "delivered_at" in updated_notification
    assert (
        datetime.now() - datetime.fromisoformat(updated_notification["delivered_at"])
    ).total_seconds() < 5

@pytest.mark.asyncio
async def test_notification_priority_handling(
    mongodb,
    redis_client,
    clean_db
):
    """Test handling of notifications with different priorities."""
    user_service = UserService()
    notification_service = NotificationService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Send notifications with different priorities
    notifications = []
    for priority in ["low", "normal", "high", "urgent"]:
        notification = await notification_service.send_notification({
            "user_id": user.id,
            "type": "test",
            "content": f"Test {priority} priority notification",
            "priority": priority
        })
        notifications.append(notification)
    
    # Verify notifications were created with correct priorities
    for notification in notifications:
        db_notification = await mongodb.notifications.find_one({
            "_id": notification.id
        })
        assert db_notification["priority"] == notification.priority
    
    # Verify urgent notifications are processed first
    processing_order = await notification_service.get_pending_notifications()
    priorities = [n.priority for n in processing_order]
    
    # Higher priority notifications should come first
    assert priorities.index("urgent") < priorities.index("normal")
    assert priorities.index("high") < priorities.index("low")

@pytest.mark.asyncio
async def test_notification_rate_limiting(
    mongodb,
    redis_client,
    clean_db
):
    """Test notification rate limiting."""
    user_service = UserService()
    notification_service = NotificationService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Send multiple notifications rapidly
    notifications = []
    for i in range(20):  # Exceeds rate limit
        try:
            notification = await notification_service.send_notification({
                "user_id": user.id,
                "type": "test",
                "content": f"Test notification {i}",
                "priority": "normal"
            })
            notifications.append(notification)
        except Exception as e:
            assert "rate limit" in str(e).lower()
            break
    
    # Verify rate limiting was applied
    assert len(notifications) < 20
    
    # Wait for rate limit to reset
    await asyncio.sleep(60)
    
    # Should be able to send notifications again
    notification = await notification_service.send_notification({
        "user_id": user.id,
        "type": "test",
        "content": "Test notification after rate limit",
        "priority": "normal"
    })
    assert notification is not None

@pytest.mark.asyncio
async def test_notification_templates(
    mongodb,
    redis_client,
    clean_db
):
    """Test notification template rendering."""
    user_service = UserService()
    notification_service = NotificationService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Test template with variables
    template_data = {
        "user_name": user.first_name,
        "appointment_time": "14:00",
        "appointment_date": "2024-03-21",
        "location": "Test Location"
    }
    
    notification = await notification_service.send_notification({
        "user_id": user.id,
        "type": "appointment_confirmation",
        "template": "appointment_confirmation",
        "template_data": template_data,
        "priority": "high"
    })
    
    # Verify template was rendered correctly
    assert notification.content is not None
    assert user.first_name in notification.content
    assert "14:00" in notification.content
    assert "2024-03-21" in notification.content
    assert "Test Location" in notification.content

@pytest.mark.asyncio
async def test_notification_history(
    mongodb,
    redis_client,
    clean_db
):
    """Test notification history retrieval."""
    user_service = UserService()
    notification_service = NotificationService()
    
    # Create test user
    user = await user_service.create_user({
        "telegram_id": "123456789",
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en"
    })
    
    # Create test notifications
    test_notifications = []
    for i in range(10):
        notification = await notification_service.send_notification({
            "user_id": user.id,
            "type": "test",
            "content": f"Test notification {i}",
            "priority": "normal"
        })
        test_notifications.append(notification)
        
        # Simulate different statuses
        if i % 3 == 0:
            await notification_service.update_notification_status(
                notification.id,
                "delivered"
            )
        elif i % 3 == 1:
            await notification_service.update_notification_status(
                notification.id,
                "read"
            )
    
    # Test history retrieval
    history = await notification_service.get_user_notification_history(user.id)
    assert len(history) == 10
    
    # Test filtering by status
    delivered = await notification_service.get_user_notification_history(
        user.id,
        status="delivered"
    )
    assert len(delivered) == 4  # 10 // 3 + 1
    
    read = await notification_service.get_user_notification_history(
        user.id,
        status="read"
    )
    assert len(read) == 3  # 10 // 3
    
    # Test pagination
    page1 = await notification_service.get_user_notification_history(
        user.id,
        limit=5,
        skip=0
    )
    assert len(page1) == 5
    
    page2 = await notification_service.get_user_notification_history(
        user.id,
        limit=5,
        skip=5
    )
    assert len(page2) == 5
    
    # Verify no duplicate notifications between pages
    page1_ids = {n.id for n in page1}
    page2_ids = {n.id for n in page2}
    assert not page1_ids.intersection(page2_ids) 