"""Main application entry point."""

import asyncio
import signal
import sys
from typing import Set, Optional
import uvicorn
from fastapi import FastAPI
import threading

from src.bot.telegram_bot import bot
from src.manager.tasks import celery
from src.monitoring.api import app as monitoring_app
from src.monitoring.health_check import start_health_monitoring, stop_health_monitoring
from src.utils.logger import setup_logger
from src.config.config import (
    MONITORING_HOST,
    MONITORING_PORT,
    METRICS_ENABLED,
    LOG_LEVEL,
    validate_config
)
from src.api.api_config import api_config
from src.services.captcha_service import captcha_service
from src.manager.booking_manager import booking_manager
from src.manager.notification_manager import notification_manager
from src.database.db_pool import db_pool
from src.database.repositories import (
    user_repository,
    subscription_repository,
    appointment_repository,
    notification_repository,
    website_config_repository
)

logger = setup_logger(__name__)

class MTAApplication:
    """Main application class."""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks: Set[asyncio.Task] = set()
        self.monitoring_thread: Optional[threading.Thread] = None
        
    async def start(self):
        """Start all application components."""
        try:
            # Validate configuration
            if not validate_config():
                logger.error("Invalid configuration, exiting")
                sys.exit(1)
                
            # Initialize database pool and ensure tables exist
            await db_pool.initialize()
            
            # Verify database tables exist
            from sqlalchemy import text
            async with db_pool.session() as session:
                try:
                    result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = result.scalars().all()
                    if not tables:
                        logger.warning("No tables found in database. Running database initialization...")
                        from scripts.init_db import init_db
                        await init_db()
                    else:
                        logger.info(f"Database tables verified: {', '.join(tables)}")
                except Exception as e:
                    logger.error(f"Error verifying database tables: {e}")
                    logger.warning("Running database initialization...")
                    from scripts.init_db import init_db
                    await init_db()
            
            logger.info("Initialized database pool")
            
            # Initialize API client
            await api_config.initialize()
            logger.info("Initialized API client")
            
            # Initialize captcha service
            await captcha_service.initialize()
            logger.info("Initialized captcha service")
            
            # Initialize booking manager
            await booking_manager.initialize()
            logger.info("Initialized booking manager")
            
            # Initialize notification manager
            await notification_manager.initialize()
            logger.info("Initialized notification manager")
            
            # Start health monitoring
            if METRICS_ENABLED:
                await start_health_monitoring()
                self.monitoring_thread = threading.Thread(
                    target=self._run_monitoring_server,
                    daemon=True
                )
                self.monitoring_thread.start()
                logger.info("Started monitoring server")
            
            # Start Telegram bot
            bot_task = asyncio.create_task(self._run_bot())
            self.tasks.add(bot_task)
            bot_task.add_done_callback(self.tasks.discard)
            logger.info("Started Telegram bot")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown all application components."""
        try:
            # Stop health monitoring
            if METRICS_ENABLED:
                await stop_health_monitoring()
                if self.monitoring_thread:
                    self.monitoring_thread.join(timeout=5)
                logger.info("Stopped monitoring server")
            
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
            
            # Wait for all tasks to complete
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Stop Telegram bot
            await bot.application.stop()
            logger.info("Stopped Telegram bot")
            
            # Close API client
            await api_config.close()
            logger.info("Closed API client")
            
            # Close captcha service
            await captcha_service.close()
            logger.info("Closed captcha service")
            
            # Close booking manager
            await booking_manager.close()
            logger.info("Closed booking manager")
            
            # Close notification manager
            await notification_manager.close()
            logger.info("Closed notification manager")
            
            # Close database pool
            await db_pool.close()
            logger.info("Closed database pool")
            
            # Set shutdown event
            self.shutdown_event.set()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise
            
    async def _run_bot(self):
        """Run the Telegram bot."""
        try:
            await bot.application.initialize()
            await bot.application.start()
            await bot.application.run_polling()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
            
    def _run_monitoring_server(self):
        """Run the monitoring server."""
        try:
            uvicorn.run(
                monitoring_app,
                host=MONITORING_HOST,
                port=MONITORING_PORT,
                log_level=LOG_LEVEL.lower()
            )
        except Exception as e:
            logger.error(f"Error running monitoring server: {e}")
            raise

def handle_shutdown(app: MTAApplication, sig=None):
    """Handle shutdown signals."""
    def _handler(signum, frame):
        logger.info(f"Received shutdown signal: {sig or signum}")
        asyncio.create_task(app.shutdown())
    return _handler

async def main():
    """Main application entry point."""
    app = MTAApplication()
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, handle_shutdown(app, sig))
    
    try:
        await app.start()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        sys.exit(1)
