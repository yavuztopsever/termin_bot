"""Task management for appointment booking system."""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import redis
from celery import Celery
import threading
import time

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
from src.monitoring.metrics import MetricsManager
from src.utils.logger import setup_logger
from src.bot.telegram_bot import notify_user_appointment_found, notify_user_appointment_booked
from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager

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
metrics = MetricsManager()

class TaskManager:
    """Manager for scheduling and executing appointment-related tasks."""
    
    def __init__(self):
        """Initialize task manager."""
        self._initialized = False
        self._running = False
        self._scheduler_thread = None
        self._stop_event = threading.Event()
        
    async def initialize(self):
        """Initialize task manager."""
        if self._initialized:
            return
            
        logger.info("Initializing task manager")
        self._initialized = True
        metrics.set_gauge("active_tasks", 0)
        
    async def close(self):
        """Close task manager and clean up resources."""
        if not self._initialized:
            return
            
        logger.info("Closing task manager")
        self.stop_scheduled_tasks()
        self._initialized = False
        
    def start_scheduled_tasks(self):
        """Start scheduled task execution in a background thread."""
        if self._running:
            return
            
        logger.info("Starting scheduled tasks")
        self._running = True
        self._stop_event.clear()
        
        self._scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            daemon=True
        )
        self._scheduler_thread.start()
        
    def stop_scheduled_tasks(self):
        """Stop scheduled task execution."""
        if not self._running:
            return
            
        logger.info("Stopping scheduled tasks")
        self._stop_event.set()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
            
        self._running = False
        
    def _run_scheduler(self):
        """Run scheduler loop in background thread."""
        logger.info("Scheduler thread started")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while not self._stop_event.is_set():
                # Run check_appointments task
                loop.run_until_complete(self.check_appointments())
                
                # Check if it's time for daily digest (around 8 AM)
                now = datetime.now()
                if now.hour == 8 and 0 <= now.minute < 15:
                    loop.run_until_complete(self.send_daily_digests())
                    
                # Sleep until next interval
                self._stop_event.wait(CHECK_INTERVAL.total_seconds())
                
        except Exception as e:
            logger.error(f"Error in scheduler thread: {str(e)}")
        finally:
            loop.close()
            logger.info("Scheduler thread stopped")
            
    async def check_appointments(self):
        """Check appointments for all active subscriptions."""
        if not self._initialized:
            logger.warning("Task manager not initialized")
            return
            
        try:
            metrics.increment("active_tasks")
            metrics.set_gauge("active_tasks", metrics.get_gauge("active_tasks") + 1)
            
            logger.info("Checking appointments for active subscriptions")
            
            # Get active subscriptions
            subscriptions = await db.get_active_subscriptions()
            
            for subscription in subscriptions:
                try:
                    # Check availability
                    available_slots = await self._check_availability(
                        service_id=subscription["service_id"],
                        location_id=subscription.get("location_id"),
                        date_preferences=subscription.get("date_preferences")
                    )
                    
                    if available_slots:
                        await self._handle_available_slots(subscription, available_slots)
                        
                except Exception as e:
                    logger.error(
                        "Error checking appointments for subscription",
                        error=str(e),
                        subscription=subscription
                    )
                    metrics.increment("task_errors")
                    
                    # Log error to database
                    await db.log_error({
                        "component": "task_manager",
                        "operation": "check_appointments",
                        "subscription_id": str(subscription.get("_id", "")),
                        "error": str(e),
                        "timestamp": datetime.utcnow()
                    })
                    
        except Exception as e:
            logger.error(f"Error in check_appointments task: {str(e)}")
            metrics.increment("task_errors")
            
            # Log error to database
            await db.log_error({
                "component": "task_manager",
                "operation": "check_appointments",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            
        finally:
            metrics.decrement("active_tasks")
            metrics.set_gauge("active_tasks", max(0, metrics.get_gauge("active_tasks") - 1))
            
    async def send_daily_digests(self):
        """Send daily digest notifications to users."""
        if not self._initialized:
            logger.warning("Task manager not initialized")
            return
            
        try:
            metrics.increment("active_tasks")
            metrics.set_gauge("active_tasks", metrics.get_gauge("active_tasks") + 1)
            
            logger.info("Sending daily digest notifications")
            
            # Get users with daily digest preference
            users = await db.get_users_by_notification_preference("daily")
            
            for user in users:
                try:
                    # Send daily digest
                    await notification_manager.send_daily_digest(user["telegram_id"])
                    
                except Exception as e:
                    logger.error(
                        "Error sending daily digest",
                        error=str(e),
                        user_id=user.get("_id", "")
                    )
                    metrics.increment("notification_errors")
                    
        except Exception as e:
            logger.error(f"Error in send_daily_digests task: {str(e)}")
            metrics.increment("task_errors")
            
        finally:
            metrics.decrement("active_tasks")
            metrics.set_gauge("active_tasks", max(0, metrics.get_gauge("active_tasks") - 1))

    async def _send_request(
    self,
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
    self,
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
            config = await db.get_api_config()
            request_data = config.get_check_availability_request(
                service_id=service_id,
                location_id=location_id,
                date_preferences=date_preferences
            )
            
            # Send request
            response = await self._send_request(
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
    self,
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
            config = await db.get_api_config()
            request_data = config.get_book_appointment_request({
                "service_id": subscription["service_id"],
                "location_id": subscription.get("location_id"),
                "date": slot["date"],
                "time": slot["time"]
            })
            
            # Send request
            response = await self._send_request(
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
                    await db.add_appointment({
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
    self,
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
    self,
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
                if self._matches_preferences(slot, subscription.get("date_preferences", {}))
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

# Create Celery task for check_appointments
@celery.task
def check_appointments() -> None:
    """Check appointments for all active subscriptions."""
    # Create an event loop for the task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async function in the event loop
        loop.run_until_complete(task_manager.check_appointments())
    except Exception as e:
        logger.error(f"Error in check_appointments task: {str(e)}", exc_info=True)
    finally:
        # Clean up the event loop
        loop.close()

# Create Celery task for send_daily_digests
@celery.task
def send_daily_digests() -> None:
    """Send daily digest notifications to users."""
    # Create an event loop for the task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async function in the event loop
        loop.run_until_complete(task_manager.send_daily_digests())
    except Exception as e:
        logger.error(f"Error in send_daily_digests task: {str(e)}", exc_info=True)
    finally:
        # Clean up the event loop
        loop.close()

# Schedule periodic tasks
celery.conf.beat_schedule = {
    "check-appointments": {
        "task": "src.manager.tasks.check_appointments",
        "schedule": CHECK_INTERVAL
    },
    "send-daily-digests": {
        "task": "src.manager.tasks.send_daily_digests",
        "schedule": timedelta(days=1)
    }
}

# Create the task manager instance
task_manager = TaskManager()

# Expose methods at module level for backward compatibility
async def _send_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    max_retries: int = MAX_RETRIES
) -> Optional[aiohttp.ClientResponse]:
    """Module-level wrapper for TaskManager._send_request for backward compatibility."""
    return await task_manager._send_request(url, method, headers, json, max_retries)

async def _check_availability(
    service_id: str,
    location_id: Optional[str] = None,
    date_preferences: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Module-level wrapper for TaskManager._check_availability for backward compatibility."""
    return await task_manager._check_availability(service_id, location_id, date_preferences)

async def _book_appointment(
    slot: Dict[str, Any],
    subscription: Dict[str, Any]
) -> bool:
    """Module-level wrapper for TaskManager._book_appointment for backward compatibility."""
    return await task_manager._book_appointment(slot, subscription)

def _matches_preferences(
    slot: Dict[str, Any],
    preferences: Dict[str, Any]
) -> bool:
    """Module-level wrapper for TaskManager._matches_preferences for backward compatibility."""
    return task_manager._matches_preferences(slot, preferences)

async def _handle_available_slots(
    subscription: Dict[str, Any],
    available_slots: List[Dict[str, Any]]
) -> None:
    """Module-level wrapper for TaskManager._handle_available_slots for backward compatibility."""
    await task_manager._handle_available_slots(subscription, available_slots)
