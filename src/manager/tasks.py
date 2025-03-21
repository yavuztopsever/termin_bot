"""Celery tasks for appointment management."""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import redis
from celery import Celery

from src.config.config import (
    REDIS_URL,
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CHECK_INTERVAL,
    MAX_RETRIES,
    RETRY_DELAY
)
from src.database.db import db
from src.monitoring.health_check import health_monitor
from src.monitoring.metrics import MetricsCollector
from src.utils.logger import setup_logger
from src.bot.telegram_bot import notify_user_appointment_found, notify_user_appointment_booked
from src.manager.booking_manager import booking_manager

logger = setup_logger(__name__)

# Initialize Redis
redis_client = redis.Redis.from_url(REDIS_URL)

# Initialize Celery
celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Initialize metrics collector
metrics = MetricsCollector()

async def _send_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    max_retries: int = MAX_RETRIES
) -> Optional[aiohttp.ClientResponse]:
    """
    Send HTTP request with retry logic.
    
    Args:
        url: Request URL
        method: HTTP method
        headers: Request headers
        json: Request body
        max_retries: Maximum retries
        
    Returns:
        Response object or None
    """
    headers = headers or {}
    
    for attempt in range(max_retries):
        try:
            start_time = datetime.utcnow()
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    timeout=30
                ) as response:
                    # Record metrics
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    success = 200 <= response.status < 300
                    
                    metrics.increment("requests_sent")
                    health_monitor.record_request(duration, success)
                    
                    if success:
                        return response
                    
                    metrics.increment("request_errors")
                    logger.error(
                        f"Request failed with status {response.status}",
                        url=url,
                        status=response.status
                    )
                    
        except Exception as e:
            metrics.increment("request_errors")
            if attempt == max_retries - 1:  # Last attempt
                logger.error(
                    "Request failed after retries",
                    error=str(e),
                    url=url,
                    attempt=attempt + 1
                )
                raise
                
            metrics.increment("request_retries")
            logger.warning(
                "Request failed, retrying",
                error=str(e),
                url=url,
                attempt=attempt + 1
            )
            await asyncio.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
            
    return None

async def _check_availability(
    service_id: str,
    location_id: Optional[str] = None,
    date_preferences: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Check appointment availability.
    
    Args:
        service_id: Service ID to check
        location_id: Optional location ID
        date_preferences: Optional date preferences
        
    Returns:
        List of available slots
    """
    try:
        # Get API configuration
        config = db.get_api_config()
        request_data = config.get_check_availability_request(
            service_id=service_id,
            location_id=location_id,
            date_preferences=date_preferences
        )
        
        # Send request
        response = await _send_request(
            url=request_data["url"],
            method=request_data["method"],
            headers=request_data["headers"],
            json=request_data.get("body")
        )
        
        if response:
            data = await response.json()
            return config.parse_availability_response(data)
            
    except Exception as e:
        logger.error(
            "Error checking availability",
            error=str(e),
            service_id=service_id,
            location_id=location_id
        )
        metrics.increment("availability_check_errors")
        
    return []

async def _book_appointment(
    slot: Dict[str, Any],
    subscription: Dict[str, Any]
) -> bool:
    """
    Book an appointment.
    
    Args:
        slot: Appointment slot
        subscription: Subscription details
        
    Returns:
        True if booking successful
    """
    try:
        # Get API configuration
        config = db.get_api_config()
        request_data = config.get_book_appointment_request({
            "service_id": subscription["service_id"],
            "location_id": subscription.get("location_id"),
            "date": slot["date"],
            "time": slot["time"]
        })
        
        # Send request
        response = await _send_request(
            url=request_data["url"],
            method=request_data["method"],
            headers=request_data["headers"],
            json=request_data.get("body")
        )
        
        if response:
            data = await response.json()
            result = config.parse_booking_response(data)
            
            if result.get("success"):
                # Store appointment
                db.add_appointment({
                    "service_id": subscription["service_id"],
                    "location_id": subscription.get("location_id"),
                    "date": slot["date"],
                    "time": slot["time"],
                    "status": "booked",
                    "user_id": subscription["user_id"],
                    "booking_id": result.get("booking_id")
                })
                
                # Update metrics
                metrics.increment("appointments_booked")
                return True
                
    except Exception as e:
        logger.error(
            "Error booking appointment",
            error=str(e),
            slot=slot,
            subscription=subscription
        )
        metrics.increment("booking_errors")
        
    return False

def _matches_preferences(
    slot: Dict[str, Any],
    preferences: Dict[str, Any]
) -> bool:
    """
    Check if slot matches preferences.
    
    Args:
        slot: Appointment slot
        preferences: User preferences
        
    Returns:
        True if slot matches preferences
    """
    try:
        # Check location
        if preferences.get("locations"):
            if slot["location"] not in preferences["locations"]:
                return False
                
        # Check time range
        if preferences.get("time_ranges"):
            slot_time = datetime.strptime(slot["time"], "%H:%M").time()
            in_range = False
            
            for time_range in preferences["time_ranges"]:
                start = datetime.strptime(time_range["start"], "%H:%M").time()
                end = datetime.strptime(time_range["end"], "%H:%M").time()
                
                if start <= slot_time <= end:
                    in_range = True
                    break
                    
            if not in_range:
                return False
                
        # Check days
        if preferences.get("days"):
            slot_date = datetime.strptime(slot["date"], "%Y-%m-%d")
            if slot_date.strftime("%A") not in preferences["days"]:
                return False
                
        # Check appointment type
        if preferences.get("appointment_types"):
            if slot.get("type") not in preferences["appointment_types"]:
                return False
                
        return True
        
    except Exception as e:
        logger.error(
            "Error matching preferences",
            error=str(e),
            slot=slot,
            preferences=preferences
        )
        return False

async def _handle_available_slots(
    subscription: Dict[str, Any],
    available_slots: List[Dict[str, Any]]
) -> None:
    """
    Handle available appointment slots.
    
    Args:
        subscription: Subscription details
        available_slots: List of available slots
    """
    try:
        # Filter slots by preferences
        matching_slots = [
            slot for slot in available_slots
            if _matches_preferences(slot, subscription.get("date_preferences", {}))
        ]
        
        if matching_slots:
            # Use BookingManager to attempt parallel booking
            logger.info(
                f"Attempting to book {len(matching_slots)} matching slots in parallel",
                subscription_id=subscription.get("_id"),
                user_id=subscription.get("user_id"),
                slots_count=len(matching_slots)
            )
            
            success, booking_details = await booking_manager.book_appointment_parallel(
                service_id=subscription["service_id"],
                location_id=subscription.get("location_id", ""),
                slots=matching_slots,
                user_id=subscription["user_id"],
                subscription_id=subscription["_id"]
            )
            
            if success:
                logger.info(
                    "Successfully booked appointment through parallel booking",
                    subscription_id=subscription.get("_id"),
                    user_id=subscription.get("user_id"),
                    booking_details=booking_details
                )
                metrics.increment("parallel_booking_success")
            else:
                logger.warning(
                    "Failed to book any appointment through parallel booking",
                    subscription_id=subscription.get("_id"),
                    user_id=subscription.get("user_id")
                )
                metrics.increment("parallel_booking_failure")
                
    except Exception as e:
        logger.error(
            "Error handling available slots",
            error=str(e),
            subscription=subscription
        )
        metrics.increment("slot_handling_errors")

@celery.task
async def check_appointments() -> None:
    """Check appointments for all active subscriptions."""
    try:
        # Get active subscriptions
        subscriptions = db.get_active_subscriptions()
        
        for subscription in subscriptions:
            try:
                # Check availability
                available_slots = await _check_availability(
                    service_id=subscription["service_id"],
                    location_id=subscription.get("location_id"),
                    date_preferences=subscription.get("date_preferences")
                )
                
                if available_slots:
                    await _handle_available_slots(subscription, available_slots)
                    
            except Exception as e:
                logger.error(
                    "Error checking appointments for subscription",
                    error=str(e),
                    subscription=subscription
                )
                metrics.increment("task_errors")
                
    except Exception as e:
        logger.error("Error in check_appointments task", error=str(e))
        metrics.increment("task_errors")

# Schedule periodic tasks
celery.conf.beat_schedule = {
    "check-appointments": {
        "task": "src.manager.tasks.check_appointments",
        "schedule": CHECK_INTERVAL
    }
}
