"""Main application entry point."""

import asyncio
import signal
import sys
from typing import Set, Optional
import uvicorn
from fastapi import FastAPI
import threading

from src.control.health.health_monitor import HealthMonitor
from src.data.database.database import Database
from src.data.redis.redis_client import RedisClient
from src.data.metrics.metrics_client import MetricsClient
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger(__name__)

class Application:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.shutdown_event = asyncio.Event()
        self.tasks: Set[asyncio.Task] = set()
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Initialize components
        self.database = Database()
        self.redis = RedisClient()
        self.metrics = MetricsClient()
        self.health_monitor = HealthMonitor()
        
    async def start(self):
        """Start all application components."""
        try:
            # Start database
            await self.database.start()
            logger.info("Started database")
            
            # Start Redis
            await self.redis.start()
            logger.info("Started Redis client")
            
            # Start metrics
            await self.metrics.start()
            logger.info("Started metrics client")
            
            # Start health monitoring
            await self.health_monitor.start()
            logger.info("Started health monitor")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown all application components."""
        try:
            # Stop health monitoring
            await self.health_monitor.stop()
            logger.info("Stopped health monitor")
            
            # Stop metrics
            await self.metrics.stop()
            logger.info("Stopped metrics client")
            
            # Stop Redis
            await self.redis.stop()
            logger.info("Stopped Redis client")
            
            # Stop database
            await self.database.stop()
            logger.info("Stopped database")
            
            # Set shutdown event
            self.shutdown_event.set()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise

def handle_shutdown(app: Application, sig=None):
    """Handle shutdown signals."""
    def _handler(signum, frame):
        logger.info(f"Received shutdown signal: {sig or signum}")
        asyncio.create_task(app.shutdown())
    return _handler

async def main():
    """Main application entry point."""
    app = Application()
    
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
