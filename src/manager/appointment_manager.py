from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import threading
from queue import Queue
import time
from contextlib import asynccontextmanager

from src.config.config import (
    CHECK_INTERVAL,
    RETRY_DELAY,
    MAX_RETRIES,
    NUM_WORKERS,
    API_RATE_LIMITS
)
from src.database.db import db
from src.utils.logger import setup_logger
from src.api.api_config import api_config
from src.bot.telegram_bot import (
    notify_user_appointment_found,
    notify_user_appointment_booked
)
from src.exceptions import (
    APIRequestError,
    RateLimitExceeded,
    BookingError,
    ConfigurationError
)

logger = setup_logger(__name__)

class AppointmentManager:
    """Manages appointment checking and booking operations."""
    
    def __init__(self):
        """Initialize appointment manager."""
        self.task_queue: Queue = Queue()
        self.workers: List[threading.Thread] = []
        self.scheduler: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self.db = db  # Store db reference
        self.is_running = False
        self.api_config = api_config
        
    async def initialize(self) -> None:
        """Initialize async components."""
        try:
            # Initialize API configuration
            await self.api_config.initialize()
            # Start the manager
            await self.start()
            logger.info("Initialized AppointmentManager")
        except Exception as e:
            logger.error("Failed to initialize AppointmentManager", error=str(e))
            raise ConfigurationError(f"Initialization failed: {str(e)}")
            
    async def close(self) -> None:
        """Clean up resources."""
        if self.is_running:
            await self.stop()
        await self.api_config.close()
        self.task_queue = Queue()  # Clear the queue
        self.workers = []  # Clear workers list
        self.scheduler = None
        logger.info("Closed AppointmentManager")
        
    async def start(self) -> None:
        """Start the appointment manager and its worker threads."""
        logger.info("Starting AppointmentManager")
        if not self.is_running:
            self._start_workers()
            self._start_scheduler()
            self.is_running = True
        
    async def stop(self) -> None:
        """Stop the appointment manager and its worker threads."""
        logger.info("Stopping AppointmentManager")
        if self.is_running:
            self._stop_event.set()
            for worker in self.workers:
                worker.join()
            if self.scheduler:
                self.scheduler.join()
            self.is_running = False
            
    def _start_workers(self) -> None:
        """Start worker threads for processing booking tasks."""
        for _ in range(NUM_WORKERS):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def _start_scheduler(self) -> None:
        """Start the scheduler thread."""
        if not self.scheduler:
            self.scheduler = threading.Thread(target=self._scheduler_loop)
            self.scheduler.daemon = True
            self.scheduler.start()
            
    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop for the current thread."""
        thread_id = threading.get_ident()
        if thread_id not in self._loops:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loops[thread_id] = loop
        return self._loops[thread_id]
        
    def _scheduler_loop(self) -> None:
        """Main scheduler loop for checking appointments."""
        loop = self._get_event_loop()
        while not self._stop_event.is_set():
            try:
                loop.run_until_complete(self.check_appointments())
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            time.sleep(CHECK_INTERVAL)
            
    def _worker_loop(self) -> None:
        """Main worker loop for processing booking tasks."""
        loop = self._get_event_loop()
        while not self._stop_event.is_set():
            try:
                # Use a shorter timeout to avoid blocking shutdown
                try:
                    task = self.task_queue.get(timeout=1)
                except TimeoutError:
                    # No task available, just continue the loop
                    continue
                
                try:
                    # Process the booking task
                    loop.run_until_complete(self._process_booking_task(task))
                    self.task_queue.task_done()
                except Exception as e:
                    logger.error(f"Error processing booking task: {str(e)}", 
                                 exc_info=True,
                                 task=task)
                    # Make sure to mark the task as done even if it fails
                    self.task_queue.task_done()
            except Exception as e:
                if not isinstance(e, TimeoutError):
                    logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
                # Add a small sleep to prevent CPU spinning on repeated errors
                time.sleep(0.1)
                    
    async def check_appointments(self) -> None:
        """Check for available appointments."""
        try:
            # Get active subscriptions
            subscriptions = await self.db.get_active_subscriptions()
            
            for subscription in subscriptions:
                try:
                    # Check availability for each subscription
                    available_slots = await self._check_availability(
                        service_id=subscription.service_id,
                        location_id=subscription.location_id,
                        date_preferences=subscription.preferences
                    )
                    
                    if available_slots:
                        await self._handle_available_slots(subscription, available_slots)
                        
                except RateLimitExceeded as e:
                    logger.warning(f"Rate limit exceeded for subscription {subscription.id}: {e}")
                    await asyncio.sleep(RETRY_DELAY)
                except Exception as e:
                    logger.error(
                        f"Error checking appointments for subscription {subscription.id}: {e}"
                    )
                    
        except Exception as e:
            logger.error(f"Error in check_appointments: {e}")
            
    @asynccontextmanager
    async def _make_request(self, url: str, headers: Dict[str, str], body: Dict[str, Any]):
        """Make an HTTP request with proper async context management."""
        async with self.api_config._session.post(url, headers=headers, json=body) as response:
            yield response
            
    async def _check_availability(
        self,
        service_id: str,
        location_id: str,
        date_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check appointment availability."""
        try:
            # Check rate limit
            if not await self.api_config._check_rate_limit('/api/v1/check'):
                logger.warning("Rate limit exceeded for check availability")
                return []
            
            # Get request details
            request_details = await self.api_config.get_check_availability_request(
                service_id=service_id,
                location_id=location_id,
                date_preferences=date_preferences
            )
            
            # Make API request
            response = await self.api_config._session.post(**request_details)
            
            if response.status == 200:
                data = await response.json()
                return data.get('slots', [])
            else:
                logger.error(f"Error checking availability: {response.status}")
                return []
                
        except Exception as e:
            logger.error(f"Error checking availability", extra={
                'service_id': service_id,
                'location_id': location_id,
                'error': str(e)
            })
            return []
            
    async def _handle_available_slots(
        self,
        subscription: Any,
        available_slots: List[Dict[str, Any]]
    ) -> None:
        """
        Handle available appointment slots.
        
        Args:
            subscription: Subscription details
            available_slots: List of available slots
        """
        for slot in available_slots:
            if await self._matches_preferences(slot, subscription.preferences):
                task = {
                    "user_id": subscription.user_id,
                    "service_id": subscription.service_id,
                    "location_id": subscription.location_id,
                    "slot": slot
                }
                self.task_queue.put(task)
                
                # Notify user about found appointment
                await notify_user_appointment_found(
                    user_id=subscription.user_id,
                    appointment_details={
                        "service_id": subscription.service_id,
                        "location_id": subscription.location_id,
                        "date": slot["date"],
                        "time": slot["time"]
                    }
                )
                
    async def _process_booking_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a booking task."""
        try:
            # Check rate limit
            if not await self.api_config._check_rate_limit('/api/v1/book'):
                logger.warning("Rate limit exceeded for booking")
                return {'success': False, 'error': 'Rate limit exceeded'}
            
            # Get request details
            request_details = await self.api_config.get_book_appointment_request(task)
            
            # Make API request
            response = await self.api_config._session.post(**request_details)
            
            if response.status == 200:
                data = await response.json()
                return {'success': True, 'booking_id': data.get('booking_id')}
            else:
                logger.error(f"Error processing booking task: {response.status}")
                return {'success': False, 'error': f'API error: {response.status}'}
                
        except Exception as e:
            logger.error(f"Error processing booking task", extra={
                'task': task,
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
            
    async def _matches_preferences(
        self,
        slot: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Check if a slot matches user preferences.
        
        Args:
            slot: Appointment slot details
            preferences: User preferences
            
        Returns:
            True if slot matches preferences, False otherwise
        """
        try:
            slot_date = datetime.strptime(slot["date"], "%Y-%m-%d").date()
            slot_time = datetime.strptime(slot["time"], "%H:%M").time()
            slot_datetime = datetime.combine(slot_date, slot_time)
            
            # Check date range
            if "date_range" in preferences:
                start_date = datetime.strptime(
                    preferences["date_range"]["start"],
                    "%Y-%m-%d"
                ).date()
                end_date = datetime.strptime(
                    preferences["date_range"]["end"],
                    "%Y-%m-%d"
                ).date()
                
                if not (start_date <= slot_date <= end_date):
                    return False
                    
            # Check time range
            if "time_range" in preferences:
                start_time = datetime.strptime(
                    preferences["time_range"]["start"],
                    "%H:%M"
                ).time()
                end_time = datetime.strptime(
                    preferences["time_range"]["end"],
                    "%H:%M"
                ).time()
                
                if not (start_time <= slot_time <= end_time):
                    return False
                    
            # Check weekdays
            if "weekdays" in preferences:
                if slot_date.weekday() not in preferences["weekdays"]:
                    return False
                    
            return True
            
        except (ValueError, KeyError) as e:
            logger.error(
                "Error matching preferences",
                error=str(e),
                slot=slot,
                preferences=preferences
            )
            return False

    async def _check_appointments(self) -> None:
        """Check appointments for all active subscriptions."""
        try:
            subscriptions = await self.db.get_active_subscriptions()
            for subscription in subscriptions:
                await self._check_availability(subscription)
        except Exception as e:
            self.logger.error(f"Error checking appointments: {e}")

# Create a global appointment manager instance
appointment_manager = AppointmentManager()
