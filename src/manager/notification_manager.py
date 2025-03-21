"""Notification manager for handling user notifications."""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

from src.config.config import TELEGRAM_TOKEN, NOTIFICATION_CONFIG
from src.utils.logger import setup_logger
from src.database.repositories import (
    notification_repository,
    user_repository
)
from src.monitoring.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

class NotificationManager:
    """Manages user notifications with rich formatting and preferences."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.application = None
        self._lock = asyncio.Lock()
        self.cooldown_users: Dict[int, datetime] = {}
        
    async def initialize(self) -> None:
        """Initialize the notification manager."""
        logger.info("Initializing notification manager")
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
    async def close(self) -> None:
        """Close the notification manager."""
        logger.info("Closing notification manager")
        if self.application:
            await self.application.shutdown()
            
    async def notify_user(
        self,
        user_id: int,
        notification_type: str,
        content: Dict[str, Any],
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Send a notification to a user.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            content: Notification content
            buttons: Optional buttons for inline keyboard
            priority: Notification priority (high, normal, low)
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Check if user has notifications enabled
            user = await user_repository.find_by_id(user_id)
            if not user or not user.settings.get("notifications_enabled", True):
                logger.info(
                    "Notifications disabled for user",
                    user_id=user_id,
                    notification_type=notification_type
                )
                return False
                
            # Check notification preferences
            if not self._check_notification_preferences(user, notification_type, priority):
                logger.info(
                    "Notification filtered by user preferences",
                    user_id=user_id,
                    notification_type=notification_type,
                    priority=priority
                )
                return False
                
            # Check cooldown
            if not self._check_cooldown(user_id, notification_type, priority):
                logger.info(
                    "Notification on cooldown",
                    user_id=user_id,
                    notification_type=notification_type
                )
                return False
                
            # Format message
            message = self._format_message(notification_type, content)
            
            # Create inline keyboard if buttons provided
            reply_markup = None
            if buttons:
                keyboard = []
                for button_row in buttons:
                    row = []
                    for button in button_row:
                        if "url" in button:
                            row.append(InlineKeyboardButton(
                                button["text"],
                                url=button["url"]
                            ))
                        else:
                            row.append(InlineKeyboardButton(
                                button["text"],
                                callback_data=button["callback_data"]
                            ))
                    keyboard.append(row)
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            # Send message to user
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            
            # Store notification in database
            await notification_repository.create({
                "user_id": user_id,
                "type": notification_type,
                "message": message,
                "status": "sent",
                "sent_at": datetime.utcnow(),
                "content": content,
                "priority": priority
            })
            
            # Update cooldown
            self._update_cooldown(user_id, notification_type)
            
            # Update metrics
            metrics.increment("notifications_sent")
            metrics.increment(f"notification_type_{notification_type}")
            
            logger.info(
                "Notification sent",
                user_id=user_id,
                notification_type=notification_type,
                priority=priority
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send notification",
                error=str(e),
                user_id=user_id,
                notification_type=notification_type
            )
            
            # Store failed notification in database
            try:
                await notification_repository.create({
                    "user_id": user_id,
                    "type": notification_type,
                    "message": "Error creating message",
                    "status": "failed",
                    "error_message": str(e),
                    "content": content,
                    "priority": priority
                })
            except Exception as db_error:
                logger.error(
                    "Failed to store notification in database",
                    error=str(db_error),
                    user_id=user_id
                )
                
            # Update metrics
            metrics.increment("notification_errors")
            
            return False
            
    def _format_message(self, notification_type: str, content: Dict[str, Any]) -> str:
        """
        Format notification message based on type.
        
        Args:
            notification_type: Type of notification
            content: Notification content
            
        Returns:
            Formatted message
        """
        if notification_type == "appointment_found":
            return self._format_appointment_found(content)
        elif notification_type == "appointment_booked":
            return self._format_appointment_booked(content)
        elif notification_type == "booking_failed":
            return self._format_booking_failed(content)
        elif notification_type == "booking_reminder":
            return self._format_booking_reminder(content)
        else:
            # Generic message format
            return f"<b>{content.get('title', 'Notification')}</b>\n\n{content.get('message', '')}"
            
    def _format_appointment_found(self, content: Dict[str, Any]) -> str:
        """Format appointment found notification."""
        parallel_attempts = content.get("parallel_attempts", 1)
        parallel_text = f" (Attempting to book {parallel_attempts} slots in parallel)" if parallel_attempts > 1 else ""
        
        message = (
            f"🎉 <b>Found an available appointment!</b>{parallel_text}\n\n"
            f"<b>Service:</b> {content.get('service_name', content.get('service_id', 'Unknown'))}\n"
            f"<b>Location:</b> {content.get('location_name', content.get('location_id', 'Unknown'))}\n"
            f"<b>Date:</b> {content.get('date', 'Unknown')}\n"
            f"<b>Time:</b> {content.get('time', 'Unknown')}\n\n"
        )
        
        if parallel_attempts > 1:
            message += "I'm trying to book multiple slots to increase your chances. Please wait..."
        else:
            message += "I'll try to book it for you..."
            
        return message
        
    def _format_appointment_booked(self, content: Dict[str, Any]) -> str:
        """Format appointment booked notification."""
        message = (
            "✅ <b>Successfully booked an appointment!</b>\n\n"
            f"<b>Service:</b> {content.get('service_name', content.get('service_id', 'Unknown'))}\n"
            f"<b>Location:</b> {content.get('location_name', content.get('location_id', 'Unknown'))}\n"
            f"<b>Date:</b> {content.get('date', 'Unknown')}\n"
            f"<b>Time:</b> {content.get('time', 'Unknown')}\n"
            f"<b>Booking ID:</b> {content.get('booking_id', 'N/A')}\n\n"
        )
        
        # Add any special instructions
        if content.get("instructions"):
            message += f"<b>Instructions:</b>\n{content.get('instructions')}\n\n"
            
        message += "Please make sure to arrive on time!"
        
        return message
        
    def _format_booking_failed(self, content: Dict[str, Any]) -> str:
        """Format booking failed notification."""
        message = (
            "❌ <b>Booking attempt failed</b>\n\n"
            f"<b>Service:</b> {content.get('service_name', content.get('service_id', 'Unknown'))}\n"
            f"<b>Location:</b> {content.get('location_name', content.get('location_id', 'Unknown'))}\n"
            f"<b>Date:</b> {content.get('date', 'Unknown')}\n"
            f"<b>Time:</b> {content.get('time', 'Unknown')}\n\n"
        )
        
        if content.get("reason"):
            message += f"<b>Reason:</b> {content.get('reason')}\n\n"
            
        message += "I'll continue looking for other appointments."
        
        return message
        
    def _format_booking_reminder(self, content: Dict[str, Any]) -> str:
        """Format booking reminder notification."""
        days_left = content.get("days_left", 0)
        
        message = (
            "🔔 <b>Appointment Reminder</b>\n\n"
            f"<b>Service:</b> {content.get('service_name', content.get('service_id', 'Unknown'))}\n"
            f"<b>Location:</b> {content.get('location_name', content.get('location_id', 'Unknown'))}\n"
            f"<b>Date:</b> {content.get('date', 'Unknown')}\n"
            f"<b>Time:</b> {content.get('time', 'Unknown')}\n"
            f"<b>Booking ID:</b> {content.get('booking_id', 'N/A')}\n\n"
        )
        
        if days_left > 1:
            message += f"Your appointment is in {days_left} days."
        elif days_left == 1:
            message += "Your appointment is tomorrow."
        else:
            message += "Your appointment is today!"
            
        if content.get("instructions"):
            message += f"\n\n<b>Instructions:</b>\n{content.get('instructions')}"
            
        return message
        
    def _check_notification_preferences(
        self,
        user: Dict[str, Any],
        notification_type: str,
        priority: str
    ) -> bool:
        """
        Check if notification should be sent based on user preferences.
        
        Args:
            user: User data
            notification_type: Type of notification
            priority: Notification priority
            
        Returns:
            True if notification should be sent
        """
        settings = user.get("settings", {})
        
        # High priority notifications are always sent
        if priority == "high":
            return True
            
        # Check notification frequency
        frequency = settings.get("notification_frequency", "immediate")
        
        if frequency == "disable":
            return False
            
        if frequency == "daily" and notification_type not in ["appointment_booked", "booking_reminder"]:
            # For daily frequency, only send appointment_booked and booking_reminder immediately
            # Other notifications will be batched and sent in a daily digest
            return False
            
        if frequency == "booked_only" and notification_type not in ["appointment_booked", "booking_reminder"]:
            return False
            
        # Check notification types
        enabled_types = settings.get("notification_types", ["all"])
        
        if "all" in enabled_types:
            return True
            
        return notification_type in enabled_types
        
    def _check_cooldown(self, user_id: int, notification_type: str, priority: str) -> bool:
        """
        Check if user is on cooldown for this notification type.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            priority: Notification priority
            
        Returns:
            True if notification can be sent
        """
        # High priority notifications bypass cooldown
        if priority == "high":
            return True
            
        # Check if user is on cooldown
        cooldown_key = f"{user_id}:{notification_type}"
        
        if cooldown_key in self.cooldown_users:
            cooldown_until = self.cooldown_users[cooldown_key]
            if datetime.utcnow() < cooldown_until:
                return False
                
        return True
        
    def _update_cooldown(self, user_id: int, notification_type: str) -> None:
        """
        Update cooldown for user and notification type.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        """
        cooldown_key = f"{user_id}:{notification_type}"
        cooldown_seconds = NOTIFICATION_CONFIG.get("cooldown", 300)  # Default 5 minutes
        
        self.cooldown_users[cooldown_key] = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
        
    async def send_appointment_found_notification(
        self,
        user_id: int,
        appointment_details: Dict[str, Any]
    ) -> bool:
        """
        Send appointment found notification.
        
        Args:
            user_id: User ID
            appointment_details: Appointment details
            
        Returns:
            True if notification was sent successfully
        """
        # Create buttons
        buttons = [
            [
                {
                    "text": "Book Now",
                    "callback_data": f"book_{appointment_details['service_id']}_{appointment_details['location_id']}_{appointment_details['date']}_{appointment_details['time']}"
                },
                {
                    "text": "Ignore",
                    "callback_data": f"ignore_{appointment_details['service_id']}_{appointment_details['location_id']}_{appointment_details['date']}_{appointment_details['time']}"
                }
            ]
        ]
        
        # Add a second row of buttons if parallel booking is in progress
        if appointment_details.get("parallel_attempts", 1) > 1:
            buttons.append([
                {
                    "text": "View Status",
                    "callback_data": f"status_{appointment_details['service_id']}_{appointment_details['location_id']}"
                }
            ])
            
        return await self.notify_user(
            user_id=user_id,
            notification_type="appointment_found",
            content=appointment_details,
            buttons=buttons,
            priority="high" if appointment_details.get("priority") == "high" else "normal"
        )
        
    async def send_appointment_booked_notification(
        self,
        user_id: int,
        booking_details: Dict[str, Any]
    ) -> bool:
        """
        Send appointment booked notification.
        
        Args:
            user_id: User ID
            booking_details: Booking details
            
        Returns:
            True if notification was sent successfully
        """
        # Create buttons
        buttons = [
            [
                {
                    "text": "Add to Calendar",
                    "callback_data": f"calendar_{booking_details['service_id']}_{booking_details['date']}_{booking_details['time']}"
                },
                {
                    "text": "Cancel Booking",
                    "callback_data": f"cancel_{booking_details.get('booking_id', 'unknown')}"
                }
            ],
            [
                {
                    "text": "View Location",
                    "callback_data": f"location_{booking_details['location_id']}"
                },
                {
                    "text": "Set Reminder",
                    "callback_data": f"reminder_{booking_details.get('booking_id', 'unknown')}"
                }
            ]
        ]
        
        # Add Google Maps link if location coordinates are available
        if booking_details.get("location_coordinates"):
            lat, lng = booking_details["location_coordinates"]
            buttons.append([
                {
                    "text": "Open in Google Maps",
                    "url": f"https://www.google.com/maps?q={lat},{lng}"
                }
            ])
            
        return await self.notify_user(
            user_id=user_id,
            notification_type="appointment_booked",
            content=booking_details,
            buttons=buttons,
            priority="high"
        )
        
    async def send_booking_failed_notification(
        self,
        user_id: int,
        booking_details: Dict[str, Any]
    ) -> bool:
        """
        Send booking failed notification.
        
        Args:
            user_id: User ID
            booking_details: Booking details
            
        Returns:
            True if notification was sent successfully
        """
        # Create buttons
        buttons = [
            [
                {
                    "text": "Try Again",
                    "callback_data": f"retry_{booking_details['service_id']}_{booking_details['location_id']}"
                },
                {
                    "text": "Change Preferences",
                    "callback_data": "settings_preferences"
                }
            ]
        ]
        
        return await self.notify_user(
            user_id=user_id,
            notification_type="booking_failed",
            content=booking_details,
            buttons=buttons,
            priority="normal"
        )
        
    async def send_booking_reminder_notification(
        self,
        user_id: int,
        booking_details: Dict[str, Any]
    ) -> bool:
        """
        Send booking reminder notification.
        
        Args:
            user_id: User ID
            booking_details: Booking details
            
        Returns:
            True if notification was sent successfully
        """
        # Create buttons
        buttons = [
            [
                {
                    "text": "View Details",
                    "callback_data": f"view_{booking_details.get('booking_id', 'unknown')}"
                },
                {
                    "text": "Cancel Booking",
                    "callback_data": f"cancel_{booking_details.get('booking_id', 'unknown')}"
                }
            ]
        ]
        
        # Add Google Maps link if location coordinates are available
        if booking_details.get("location_coordinates"):
            lat, lng = booking_details["location_coordinates"]
            buttons.append([
                {
                    "text": "Open in Google Maps",
                    "url": f"https://www.google.com/maps?q={lat},{lng}"
                }
            ])
            
        return await self.notify_user(
            user_id=user_id,
            notification_type="booking_reminder",
            content=booking_details,
            buttons=buttons,
            priority="high"
        )
        
    async def send_daily_digest(self, user_id: int) -> bool:
        """
        Send daily digest of notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Get user's pending notifications
            notifications = await notification_repository.find_by_user_id(user_id)
            
            # Filter to pending notifications
            pending = [n for n in notifications if n.status == "pending"]
            
            if not pending:
                return False
                
            # Group by type
            by_type = {}
            for notification in pending:
                if notification.type not in by_type:
                    by_type[notification.type] = []
                by_type[notification.type].append(notification)
                
            # Create digest message
            message = "<b>📋 Daily Notification Digest</b>\n\n"
            
            # Add appointment found notifications
            if "appointment_found" in by_type:
                message += f"<b>🔍 Found {len(by_type['appointment_found'])} available appointments</b>\n"
                for i, notification in enumerate(by_type["appointment_found"][:3], 1):
                    content = notification.content
                    message += (
                        f"{i}. {content.get('service_name', content.get('service_id', 'Unknown'))} at "
                        f"{content.get('location_name', content.get('location_id', 'Unknown'))}: "
                        f"{content.get('date', 'Unknown')} {content.get('time', 'Unknown')}\n"
                    )
                if len(by_type["appointment_found"]) > 3:
                    message += f"...and {len(by_type['appointment_found']) - 3} more\n"
                message += "\n"
                
            # Add booking failed notifications
            if "booking_failed" in by_type:
                message += f"<b>❌ {len(by_type['booking_failed'])} booking attempts failed</b>\n\n"
                
            # Add booking reminder notifications
            if "booking_reminder" in by_type:
                message += "<b>🔔 Upcoming appointments</b>\n"
                for i, notification in enumerate(by_type["booking_reminder"], 1):
                    content = notification.content
                    message += (
                        f"{i}. {content.get('service_name', content.get('service_id', 'Unknown'))}: "
                        f"{content.get('date', 'Unknown')} {content.get('time', 'Unknown')}\n"
                    )
                message += "\n"
                
            # Create buttons
            buttons = [
                [
                    {
                        "text": "View All Appointments",
                        "callback_data": "view_all_appointments"
                    }
                ],
                [
                    {
                        "text": "Check Now",
                        "callback_data": "check_now"
                    },
                    {
                        "text": "Settings",
                        "callback_data": "settings_notifications"
                    }
                ]
            ]
            
            # Send digest
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(b["text"], callback_data=b["callback_data"])]
                    for row in buttons
                    for b in row
                ]),
                parse_mode="HTML"
            )
            
            # Mark notifications as sent
            for notification in pending:
                await notification_repository.update(
                    notification.id,
                    {"status": "sent", "sent_at": datetime.utcnow()}
                )
                
            # Update metrics
            metrics.increment("digest_sent")
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send daily digest",
                error=str(e),
                user_id=user_id
            )
            metrics.increment("digest_errors")
            return False

# Create a global notification manager instance
notification_manager = NotificationManager()
