"""Booking manager for parallel appointment booking."""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
import time
from datetime import datetime
import random

from src.api.api_config import api_config
from src.utils.logger import setup_logger
from src.utils.retry import RetryConfig, async_retry
from src.database.repositories import (
    appointment_repository,
    notification_repository,
    subscription_repository
)
from src.manager.notification_manager import notification_manager
from src.monitoring.metrics import MetricsCollector
from src.config.config import MAX_PARALLEL_BOOKINGS, BOOKING_TIMEOUT

logger = setup_logger(__name__)
metrics = MetricsCollector()

class BookingManager:
    """Manages parallel booking attempts for appointments."""
    
    def __init__(self):
        """Initialize booking manager."""
        self.max_parallel_attempts = MAX_PARALLEL_BOOKINGS
        self.booking_timeout = BOOKING_TIMEOUT
        self.semaphore = asyncio.Semaphore(MAX_PARALLEL_BOOKINGS)
        self.active_bookings: Set[str] = set()
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the booking manager."""
        logger.info("Initializing booking manager")
        
    async def close(self) -> None:
        """Close the booking manager."""
        logger.info("Closing booking manager")
        
    async def book_appointment_parallel(
        self,
        service_id: str,
        location_id: str,
        slots: List[Dict[str, Any]],
        user_id: int,
        subscription_id: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Attempt to book an appointment in parallel.
        
        Args:
            service_id: Service ID
            location_id: Location ID
            slots: List of available slots
            user_id: User ID
            subscription_id: Subscription ID
            
        Returns:
            Tuple of (success, booking_details)
        """
        if not slots:
            logger.warning(
                "No slots available for booking",
                service_id=service_id,
                location_id=location_id,
                user_id=user_id
            )
            return False, None
            
        # Shuffle slots to avoid multiple users targeting the same slot first
        random.shuffle(slots)
        
        # Limit number of slots to attempt booking
        max_attempts = min(len(slots), self.max_parallel_attempts)
        target_slots = slots[:max_attempts]
        
        logger.info(
            f"Attempting to book {len(target_slots)} slots in parallel",
            service_id=service_id,
            location_id=location_id,
            user_id=user_id,
            slots_count=len(target_slots)
        )
        
        # Notify user that we found available slots and are attempting to book
        first_slot = target_slots[0]
        await notification_manager.send_appointment_found_notification(
            user_id,
            {
                "service_id": service_id,
                "location_id": location_id,
                "date": first_slot["date"],
                "time": first_slot["time"],
                "parallel_attempts": len(target_slots)
            }
        )
        
        # Start parallel booking attempts
        booking_tasks = []
        for slot in target_slots:
            # Create unique booking ID for tracking
            booking_id = f"{service_id}:{location_id}:{slot['date']}:{slot['time']}:{user_id}"
            
            # Check if this booking is already being attempted
            async with self._lock:
                if booking_id in self.active_bookings:
                    logger.info(
                        "Booking already in progress, skipping",
                        booking_id=booking_id
                    )
                    continue
                    
                # Add to active bookings
                self.active_bookings.add(booking_id)
            
            # Create booking task
            task = asyncio.create_task(
                self._attempt_booking(
                    service_id,
                    location_id,
                    slot,
                    user_id,
                    subscription_id,
                    booking_id
                )
            )
            booking_tasks.append(task)
        
        # Wait for first successful booking or all failures
        try:
            # Use asyncio.wait with return_when=FIRST_COMPLETED to get the first successful booking
            done, pending = await asyncio.wait(
                booking_tasks,
                timeout=self.booking_timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel all pending tasks once we have a successful booking
            for task in pending:
                task.cancel()
                
            # Check results from completed tasks
            for task in done:
                try:
                    success, booking_details = await task
                    if success:
                        # Successfully booked an appointment
                        metrics.increment("successful_bookings")
                        
                        # Update subscription status
                        await subscription_repository.update(
                            subscription_id,
                            {"status": "completed"}
                        )
                        
                        return True, booking_details
                except Exception as e:
                    logger.error(
                        f"Error in booking task: {e}",
                        error=str(e)
                    )
            
            # If we get here, all booking attempts failed
            metrics.increment("failed_bookings")
            
            # Notify user that all booking attempts failed
            await notification_manager.send_booking_failed_notification(
                user_id,
                {
                    "service_id": service_id,
                    "location_id": location_id,
                    "date": first_slot["date"],
                    "time": first_slot["time"],
                    "reason": "All booking attempts failed"
                }
            )
            
            return False, None
            
        except asyncio.TimeoutError:
            # Booking attempts timed out
            logger.warning(
                "Booking attempts timed out",
                service_id=service_id,
                location_id=location_id,
                user_id=user_id,
                timeout=self.booking_timeout
            )
            
            # Cancel all tasks
            for task in booking_tasks:
                task.cancel()
                
            metrics.increment("timeout_bookings")
            
            # Notify user that booking attempts timed out
            await notification_manager.send_booking_failed_notification(
                user_id,
                {
                    "service_id": service_id,
                    "location_id": location_id,
                    "date": first_slot["date"],
                    "time": first_slot["time"],
                    "reason": f"Booking attempts timed out after {self.booking_timeout} seconds"
                }
            )
            
            return False, None
            
        finally:
            # Clean up active bookings
            async with self._lock:
                for slot in target_slots:
                    booking_id = f"{service_id}:{location_id}:{slot['date']}:{slot['time']}:{user_id}"
                    self.active_bookings.discard(booking_id)
    
    async def _attempt_booking(
        self,
        service_id: str,
        location_id: str,
        slot: Dict[str, Any],
        user_id: int,
        subscription_id: int,
        booking_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Attempt to book a single appointment slot.
        
        Args:
            service_id: Service ID
            location_id: Location ID
            slot: Appointment slot
            user_id: User ID
            subscription_id: Subscription ID
            booking_id: Unique booking ID for tracking
            
        Returns:
            Tuple of (success, booking_details)
        """
        # Use semaphore to limit concurrent API requests
        async with self.semaphore:
            try:
                logger.info(
                    f"Attempting to book appointment",
                    service_id=service_id,
                    location_id=location_id,
                    date=slot["date"],
                    time=slot["time"],
                    user_id=user_id,
                    booking_id=booking_id
                )
                
                # Attempt to book the appointment
                result = await api_config.book_appointment(
                    service_id=service_id,
                    office_id=location_id,
                    date=slot["date"],
                    time=slot["time"]
                )
                
                if result.get("success"):
                    # Successfully booked the appointment
                    logger.info(
                        "Successfully booked appointment",
                        service_id=service_id,
                        location_id=location_id,
                        date=slot["date"],
                        time=slot["time"],
                        user_id=user_id,
                        booking_id=booking_id,
                        result_booking_id=result.get("booking_id")
                    )
                    
                    # Create appointment record
                    appointment = await appointment_repository.create({
                        "service_id": service_id,
                        "location_id": location_id,
                        "date": slot["date"],
                        "time": slot["time"],
                        "status": "booked",
                        "user_id": user_id,
                        "booking_id": result.get("booking_id"),
                        "booked_at": datetime.utcnow()
                    })
                    
                    # Notify user
                    booking_details = {
                        "service_id": service_id,
                        "location_id": location_id,
                        "date": slot["date"],
                        "time": slot["time"],
                        "booking_id": result.get("booking_id"),
                        "appointment_id": appointment.id
                    }
                    
                    await notification_manager.send_appointment_booked_notification(user_id, booking_details)
                    
                    return True, booking_details
                else:
                    # Booking failed
                    logger.warning(
                        f"Failed to book appointment: {result.get('message')}",
                        service_id=service_id,
                        location_id=location_id,
                        date=slot["date"],
                        time=slot["time"],
                        user_id=user_id,
                        booking_id=booking_id,
                        message=result.get("message")
                    )
                    
                    return False, None
                    
            except Exception as e:
                logger.error(
                    f"Error booking appointment: {e}",
                    service_id=service_id,
                    location_id=location_id,
                    date=slot["date"],
                    time=slot["time"],
                    user_id=user_id,
                    booking_id=booking_id,
                    error=str(e)
                )
                
                return False, None

# Create a global booking manager instance
booking_manager = BookingManager()
