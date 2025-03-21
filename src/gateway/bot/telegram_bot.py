from typing import Dict, Any, Optional, Callable
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
import json
from datetime import datetime

from src.config.config import TELEGRAM_TOKEN
from src.utils.logger import setup_logger
from src.database.db import db
from src.analyzer.analyzer import run_analysis

logger = setup_logger(__name__)

# Conversation states
(
    SELECTING_SERVICE,
    SELECTING_LOCATION,
    SELECTING_DATE_PREFERENCE,
    CONFIRMING_SUBSCRIPTION
) = range(4)

class TelegramBot:
    """Handles Telegram bot operations and user interactions."""
    
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        self._setup_handlers()
        
    def _setup_handlers(self) -> None:
        """Set up command and conversation handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("check", self.check_command))
        self.application.add_handler(CommandHandler("appointments", self.appointments_command))
        self.application.add_handler(CommandHandler("list", self.list_command))
        
        # Subscription conversation handler
        subscription_conv = ConversationHandler(
            entry_points=[CommandHandler("subscribe", self.subscribe_command)],
            states={
                SELECTING_SERVICE: [
                    CallbackQueryHandler(self.select_service_callback, pattern=r"^service_")
                ],
                SELECTING_LOCATION: [
                    CallbackQueryHandler(self.select_location_callback, pattern=r"^location_")
                ],
                SELECTING_DATE_PREFERENCE: [
                    CallbackQueryHandler(self.select_date_preference_callback, pattern=r"^date_")
                ],
                CONFIRMING_SUBSCRIPTION: [
                    CallbackQueryHandler(self.confirm_subscription_callback, pattern=r"^confirm_")
                ]
            },
            fallbacks=[CommandHandler("abort", self.abort_command)]
        )
        self.application.add_handler(subscription_conv)
        
        # Appointment action handlers
        self.application.add_handler(CallbackQueryHandler(self.book_appointment_callback, pattern=r"^book_"))
        self.application.add_handler(CallbackQueryHandler(self.ignore_appointment_callback, pattern=r"^ignore_"))
        self.application.add_handler(CallbackQueryHandler(self.calendar_callback, pattern=r"^calendar_"))
        self.application.add_handler(CallbackQueryHandler(self.cancel_booking_callback, pattern=r"^cancel_"))
        
        # Settings handlers
        self.application.add_handler(CallbackQueryHandler(self.settings_language_callback, pattern=r"^settings_language"))
        self.application.add_handler(CallbackQueryHandler(self.settings_notifications_callback, pattern=r"^settings_notifications"))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        try:
            user = update.effective_user
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "settings": {
                    "language": "en",
                    "notification_frequency": 15
                }
            }
            
            # Add or update user in database
            db.add_user(user_data)
            
            await update.message.reply_text(
                f"Welcome {user.first_name}! 👋\n\n"
                "I can help you find and book appointments at Munich's public service offices. "
                "Here are the available commands:\n\n"
                "/subscribe - Subscribe to appointment notifications\n"
                "/list - List your active subscriptions\n"
                "/check - Check appointments now\n"
                "/appointments - View your appointments\n"
                "/settings - Change your preferences\n"
                "/help - Show this help message\n"
                "/abort - Cancel current operation"
            )
            
        except Exception as e:
            logger.error("Error in start command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        await self.start_command(update, context)
        
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /settings command."""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("Language 🌐", callback_data="settings_language"),
                    InlineKeyboardButton("Notifications 🔔", callback_data="settings_notifications")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to change?",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error("Error in settings command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /check command."""
        try:
            await update.message.reply_text(
                "Checking for appointments... I'll notify you if I find any available slots."
            )
            # The actual checking is done by the appointment manager
            
        except Exception as e:
            logger.error("Error in check command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def appointments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /appointments command."""
        try:
            user_id = update.effective_user.id
            # TODO: Implement appointment retrieval from database
            await update.message.reply_text(
                "You don't have any appointments yet."
            )
            
        except Exception as e:
            logger.error("Error in appointments command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /list command."""
        try:
            user = db.get_user(update.effective_user.id)
            if not user or not user.get("subscriptions"):
                await update.message.reply_text(
                    "You don't have any active subscriptions."
                )
                return
                
            subscriptions = user["subscriptions"]
            message = "Your active subscriptions:\n\n"
            for i, sub in enumerate(subscriptions, 1):
                if sub.get("active"):
                    message += f"{i}. Service: {sub['service_id']}\n"
                    message += f"   Location: {sub['location_id']}\n"
                    message += "   ----\n"
                    
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error("Error in list command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the /subscribe command."""
        try:
            # Get available services from database
            services = [
                {"id": "10339027", "name": "Residence Registration"}
            ]  # Placeholder
            
            keyboard = [
                [InlineKeyboardButton(
                    service["name"],
                    callback_data=f"service_{service['id']}"
                )]
                for service in services
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Please select a service:",
                reply_markup=reply_markup
            )
            
            return SELECTING_SERVICE
            
        except Exception as e:
            logger.error("Error in subscribe command", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            return ConversationHandler.END
            
    async def abort_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the /abort command."""
        await update.message.reply_text(
            "Operation cancelled."
        )
        return ConversationHandler.END
        
    async def select_service_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle service selection."""
        try:
            query = update.callback_query
            await query.answer()
            
            service_id = query.data.split("_")[1]
            context.user_data["service_id"] = service_id
            
            # Get locations for the selected service
            locations = [
                {"id": "10187259", "name": "KVR"}
            ]  # Placeholder
            
            keyboard = [
                [InlineKeyboardButton(
                    location["name"],
                    callback_data=f"location_{location['id']}"
                )]
                for location in locations
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please select a location:",
                reply_markup=reply_markup
            )
            
            return SELECTING_LOCATION
            
        except Exception as e:
            logger.error("Error in service selection", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            return ConversationHandler.END
            
    async def select_location_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle location selection."""
        try:
            query = update.callback_query
            await query.answer()
            
            location_id = query.data.split("_")[1]
            context.user_data["location_id"] = location_id
            
            # Create date preference options
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Next available",
                        callback_data="date_next"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Within 1 week",
                        callback_data="date_week"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Within 1 month",
                        callback_data="date_month"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "When would you like to get an appointment?",
                reply_markup=reply_markup
            )
            
            return SELECTING_DATE_PREFERENCE
            
        except Exception as e:
            logger.error("Error in location selection", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            return ConversationHandler.END
            
    async def select_date_preference_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle date preference selection."""
        try:
            query = update.callback_query
            await query.answer()
            
            date_preference = query.data.split("_")[1]
            context.user_data["date_preference"] = date_preference
            
            await query.edit_message_text(
                f"You selected {date_preference} as your date preference."
            )
            
            return CONFIRMING_SUBSCRIPTION
            
        except Exception as e:
            logger.error("Error in date preference selection", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            return ConversationHandler.END
            
    async def confirm_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle subscription confirmation."""
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "Subscription confirmed! You'll receive notifications about available appointments."
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error("Error in subscription confirmation", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            return ConversationHandler.END
            
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors."""
        logger.error("Bot error", error=context.error, update=update)
        if isinstance(update, Update):
            await self._handle_error(update, str(context.error))
            
    async def book_appointment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle book appointment callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data
            parts = query.data.split("_")
            if len(parts) < 5:
                logger.error("Invalid book callback data", data=query.data)
                await query.edit_message_text("Invalid booking data. Please try again.")
                return
                
            service_id = parts[1]
            location_id = parts[2]
            date = parts[3]
            time = parts[4]
            
            # Update message to show booking in progress
            await query.edit_message_text(
                "Booking appointment...\n\n"
                f"Service: {service_id}\n"
                f"Location: {location_id}\n"
                f"Date: {date}\n"
                f"Time: {time}"
            )
            
            # TODO: Implement actual booking logic
            # This would typically call the appointment manager to book the appointment
            
            # For now, just simulate a successful booking
            booking_details = {
                "service_id": service_id,
                "location_id": location_id,
                "date": date,
                "time": time,
                "booking_id": f"BOOK-{int(datetime.utcnow().timestamp())}"
            }
            
            # Notify user of successful booking
            await notify_user_appointment_booked(update.effective_user.id, booking_details)
            
        except Exception as e:
            logger.error("Error in book appointment callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def ignore_appointment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle ignore appointment callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data
            parts = query.data.split("_")
            if len(parts) < 5:
                logger.error("Invalid ignore callback data", data=query.data)
                await query.edit_message_text("Invalid data. Please try again.")
                return
                
            service_id = parts[1]
            location_id = parts[2]
            date = parts[3]
            time = parts[4]
            
            # Update message to show appointment ignored
            await query.edit_message_text(
                "Appointment ignored.\n\n"
                f"Service: {service_id}\n"
                f"Location: {location_id}\n"
                f"Date: {date}\n"
                f"Time: {time}\n\n"
                "I'll continue looking for other appointments."
            )
            
            # TODO: Implement logic to mark this appointment as ignored in the database
            
        except Exception as e:
            logger.error("Error in ignore appointment callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle add to calendar callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data
            parts = query.data.split("_")
            if len(parts) < 4:
                logger.error("Invalid calendar callback data", data=query.data)
                await query.edit_message_text("Invalid data. Please try again.")
                return
                
            service_id = parts[1]
            date = parts[2]
            time = parts[3]
            
            # Generate calendar link (iCal format)
            calendar_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Appointment&dates={date}T{time.replace(':', '')}00/{date}T{time.replace(':', '')}30&details=Appointment%20at%20Munich%20Public%20Service%20Office&location=Munich"
            
            # Update message with calendar link
            keyboard = [
                [InlineKeyboardButton("Add to Google Calendar", url=calendar_link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Click the button below to add this appointment to your calendar:\n\n"
                f"Service: {service_id}\n"
                f"Date: {date}\n"
                f"Time: {time}",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error("Error in calendar callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def cancel_booking_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle cancel booking callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data
            booking_id = query.data.split("_")[1]
            
            # Update message to show cancellation in progress
            await query.edit_message_text(
                f"Cancelling booking {booking_id}..."
            )
            
            # TODO: Implement actual cancellation logic
            # This would typically call the appointment manager to cancel the booking
            
            # For now, just simulate a successful cancellation
            await query.edit_message_text(
                f"Booking {booking_id} has been cancelled."
            )
            
        except Exception as e:
            logger.error("Error in cancel booking callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def settings_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle language settings callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Create language options
            keyboard = [
                [
                    InlineKeyboardButton("English 🇬🇧", callback_data="language_en"),
                    InlineKeyboardButton("Deutsch 🇩🇪", callback_data="language_de")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select your preferred language:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error("Error in language settings callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def settings_notifications_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle notifications settings callback."""
        try:
            query = update.callback_query
            await query.answer()
            
            # Create notification frequency options
            keyboard = [
                [
                    InlineKeyboardButton("Immediate", callback_data="notify_immediate"),
                    InlineKeyboardButton("Daily", callback_data="notify_daily")
                ],
                [
                    InlineKeyboardButton("Only when booked", callback_data="notify_booked"),
                    InlineKeyboardButton("Disable", callback_data="notify_disable")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select your notification preference:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error("Error in notifications settings callback", error=str(e), update=update.to_dict())
            await self._handle_error(update, str(e))
            
    async def _handle_error(self, update: Update, error_message: str) -> None:
        """Send error message to user."""
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )
        
    def run(self) -> None:
        """Run the bot."""
        logger.info("Starting Telegram bot")
        self.application.run_polling()
        
# Notification functions
async def notify_user_appointment_found(user_id: int, appointment_details: Dict[str, Any]) -> None:
    """Notify user when an appointment is found."""
    try:
        message = (
            "🎉 Found an available appointment!\n\n"
            f"Service: {appointment_details['service_id']}\n"
            f"Location: {appointment_details['location_id']}\n"
            f"Date: {appointment_details['date']}\n"
            f"Time: {appointment_details['time']}\n\n"
            "I'll try to book it for you..."
        )
        
        # Create inline keyboard for user actions
        keyboard = [
            [
                InlineKeyboardButton("Book Now", callback_data=f"book_{appointment_details['service_id']}_{appointment_details['location_id']}_{appointment_details['date']}_{appointment_details['time']}"),
                InlineKeyboardButton("Ignore", callback_data=f"ignore_{appointment_details['service_id']}_{appointment_details['location_id']}_{appointment_details['date']}_{appointment_details['time']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message to user
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        await application.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup
        )
        
        # Store notification in database
        await db.add_notification({
            "user_id": user_id,
            "type": "appointment_found",
            "message": message,
            "status": "sent",
            "sent_at": datetime.utcnow(),
            "appointment_details": appointment_details
        })
        
        logger.info("Appointment found notification sent",
                   user_id=user_id,
                   appointment_details=appointment_details)
        
    except Exception as e:
        logger.error("Failed to send appointment found notification",
                    error=str(e),
                    user_id=user_id,
                    appointment_details=appointment_details)
        
        # Store failed notification in database
        try:
            await db.add_notification({
                "user_id": user_id,
                "type": "appointment_found",
                "message": message if 'message' in locals() else "Error creating message",
                "status": "failed",
                "error_message": str(e),
                "appointment_details": appointment_details
            })
        except Exception as db_error:
            logger.error("Failed to store notification in database",
                        error=str(db_error),
                        user_id=user_id)
        
async def notify_user_appointment_booked(user_id: int, booking_details: Dict[str, Any]) -> None:
    """Notify user when an appointment is booked."""
    try:
        message = (
            "✅ Successfully booked an appointment!\n\n"
            f"Service: {booking_details['service_id']}\n"
            f"Location: {booking_details['location_id']}\n"
            f"Date: {booking_details['date']}\n"
            f"Time: {booking_details['time']}\n"
            f"Booking ID: {booking_details.get('booking_id', 'N/A')}\n\n"
            "Please make sure to arrive on time!"
        )
        
        # Create inline keyboard for user actions
        keyboard = [
            [
                InlineKeyboardButton("Add to Calendar", callback_data=f"calendar_{booking_details['service_id']}_{booking_details['date']}_{booking_details['time']}"),
                InlineKeyboardButton("Cancel Booking", callback_data=f"cancel_{booking_details.get('booking_id', 'unknown')}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message to user
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        await application.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup
        )
        
        # Store notification in database
        await db.add_notification({
            "user_id": user_id,
            "type": "appointment_booked",
            "message": message,
            "status": "sent",
            "sent_at": datetime.utcnow(),
            "booking_details": booking_details
        })
        
        logger.info("Appointment booked notification sent",
                   user_id=user_id,
                   booking_details=booking_details)
        
    except Exception as e:
        logger.error("Failed to send appointment booked notification",
                    error=str(e),
                    user_id=user_id,
                    booking_details=booking_details)
        
        # Store failed notification in database
        try:
            await db.add_notification({
                "user_id": user_id,
                "type": "appointment_booked",
                "message": message if 'message' in locals() else "Error creating message",
                "status": "failed",
                "error_message": str(e),
                "booking_details": booking_details
            })
        except Exception as db_error:
            logger.error("Failed to store notification in database",
                        error=str(db_error),
                        user_id=user_id)
        
# Create a global bot instance
bot = TelegramBot()
