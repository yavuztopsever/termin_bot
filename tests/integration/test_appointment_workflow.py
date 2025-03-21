"""Integration tests for the appointment workflow."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from src.models import User, Subscription, Appointment
from src.services.appointment import AppointmentService
from src.services.subscription import SubscriptionService
from src.services.notification import NotificationService

@pytest.fixture
def clean_db():
    """Clean database before and after tests."""
    db.users.delete_many({})
    db.appointments.delete_many({})
    db.subscriptions.delete_many({})
    yield
    db.users.delete_many({})
    db.appointments.delete_many({})
    db.subscriptions.delete_many({})

@pytest.fixture
def mock_api():
    """Mock API responses."""
    with patch('src.api.api_config.APIConfig._send_request') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {
            "slots": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "service_id": "test_service",
                    "location_id": "test_location"
                }
            ]
        }
        yield mock

@pytest.fixture
def test_user():
    """Create test user."""
    user_data = {
        "user_id": "test_user",
        "settings": {
            "notifications": True,
            "auto_book": True
        }
    }
    db.users.insert_one(user_data)
    return user_data

@pytest.mark.asyncio
async def test_complete_appointment_workflow(
    mongodb,
    redis_client,
    mock_api,
    test_user: User,
    clean_db
):
    """Test the complete appointment workflow from checking slots to booking."""
    # Initialize services
    appointment_service = AppointmentService()
    subscription_service = SubscriptionService()
    notification_service = NotificationService()
    
    # Create subscription
    subscription_data = {
        "user_id": test_user.id,
        "service_id": "test_service",
        "location_id": "test_location",
        "date_from": datetime.now().date(),
        "date_to": (datetime.now() + timedelta(days=30)).date(),
        "time_from": "09:00",
        "time_to": "17:00",
        "status": "active"
    }
    subscription = await subscription_service.create_subscription(subscription_data)
    
    # Check available slots
    slots = await appointment_service.check_availability(
        service_id=subscription.service_id,
        location_id=subscription.location_id,
        date_from=subscription.date_from.isoformat(),
        date_to=subscription.date_to.isoformat()
    )
    
    assert len(slots) > 0, "No slots available"
    
    # Book first available slot
    slot = slots[0]
    booking = await appointment_service.book_appointment(
        slot_id=f"{slot['date']}_{slot['time']}_{slot['service_id']}_{slot['location_id']}",
        service_id=slot["service_id"],
        location_id=slot["location_id"],
        user_details={
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "email": "test@example.com"
        }
    )
    
    assert booking["success"] is True
    assert "booking_id" in booking
    assert "confirmation_code" in booking
    
    # Verify booking in database
    appointment = await mongodb.appointments.find_one({"booking_id": booking["booking_id"]})
    assert appointment is not None
    
    # Verify notification was sent
    notifications = await mongodb.notifications.find(
        {"user_id": test_user.id}
    ).to_list(length=None)
    
    assert len(notifications) > 0
    assert any(n["type"] == "booking_confirmation" for n in notifications)

@pytest.mark.asyncio
async def test_rate_limited_appointment_check(
    mongodb,
    redis_client,
    mock_api,
    test_user: User,
    clean_db
):
    """Test rate limiting during appointment checks."""
    appointment_service = AppointmentService()
    
    # Make multiple rapid requests
    for _ in range(15):  # Exceeds rate limit of 10 requests per minute
        try:
            await appointment_service.check_availability(
                service_id="test_service",
                location_id="test_location",
                date_from=datetime.now().date().isoformat(),
                date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
            )
        except Exception as e:
            assert "Rate limit exceeded" in str(e)
            break
    else:
        pytest.fail("Rate limit was not enforced")

@pytest.mark.asyncio
async def test_concurrent_booking_attempts(
    mongodb,
    redis_client,
    mock_api,
    test_user: User,
    clean_db
):
    """Test handling of concurrent booking attempts."""
    appointment_service = AppointmentService()
    
    # Get available slots
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) > 0, "No slots available"
    
    # Try to book the same slot multiple times
    slot = slots[0]
    slot_id = f"{slot['date']}_{slot['time']}_{slot['service_id']}_{slot['location_id']}"
    
    # First booking should succeed
    booking1 = await appointment_service.book_appointment(
        slot_id=slot_id,
        service_id=slot["service_id"],
        location_id=slot["location_id"],
        user_details={"first_name": "Test1", "last_name": "User1", "email": "test1@example.com"}
    )
    
    assert booking1["success"] is True
    
    # Second booking should fail
    with pytest.raises(Exception) as exc_info:
        await appointment_service.book_appointment(
            slot_id=slot_id,
            service_id=slot["service_id"],
            location_id=slot["location_id"],
            user_details={"first_name": "Test2", "last_name": "User2", "email": "test2@example.com"}
        )
    
    assert "already booked" in str(exc_info.value)

@pytest.mark.asyncio
async def test_error_handling_and_retry(
    mongodb,
    redis_client,
    mock_api,
    test_user: User,
    clean_db
):
    """Test error handling and retry mechanism."""
    appointment_service = AppointmentService()
    
    # Simulate API errors by stopping the mock server
    mock_api.stop()
    
    # Attempt to check availability (should fail)
    with pytest.raises(Exception) as exc_info:
        await appointment_service.check_availability(
            service_id="test_service",
            location_id="test_location",
            date_from=datetime.now().date().isoformat(),
            date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
        )
    
    assert "Connection" in str(exc_info.value)
    
    # Restart mock server
    mock_api.start()
    
    # Retry should succeed
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) > 0

@pytest.mark.asyncio
async def test_notification_delivery(
    mongodb,
    redis_client,
    mock_api,
    test_user: User,
    clean_db
):
    """Test notification delivery throughout the appointment process."""
    appointment_service = AppointmentService()
    notification_service = NotificationService()
    
    # Get available slots
    slots = await appointment_service.check_availability(
        service_id="test_service",
        location_id="test_location",
        date_from=datetime.now().date().isoformat(),
        date_to=(datetime.now() + timedelta(days=30)).date().isoformat()
    )
    
    assert len(slots) > 0, "No slots available"
    
    # Book appointment
    slot = slots[0]
    booking = await appointment_service.book_appointment(
        slot_id=f"{slot['date']}_{slot['time']}_{slot['service_id']}_{slot['location_id']}",
        service_id=slot["service_id"],
        location_id=slot["location_id"],
        user_details={
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "email": "test@example.com"
        }
    )
    
    # Verify notifications
    notifications = await mongodb.notifications.find(
        {"user_id": test_user.id}
    ).to_list(length=None)
    
    # Check different types of notifications
    notification_types = [n["type"] for n in notifications]
    assert "slot_found" in notification_types
    assert "booking_confirmation" in notification_types
    
    # Verify notification content
    confirmation = next(n for n in notifications if n["type"] == "booking_confirmation")
    assert booking["booking_id"] in confirmation["content"]
    assert booking["confirmation_code"] in confirmation["content"] 