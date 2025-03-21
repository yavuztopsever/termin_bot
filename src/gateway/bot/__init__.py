"""Bot module for the application."""

from telegram.ext import Application
from src.config import Settings
from src.bot.telegram_bot import TelegramBot

async def create_bot(settings: Settings = None) -> Application:
    """Create and return a Telegram bot instance."""
    bot = TelegramBot()
    await bot.application.initialize()
    return bot.application
