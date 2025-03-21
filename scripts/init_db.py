#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.db import Base, AsyncDatabase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def init_db():
    """Initialize the database."""
    try:
        # Create a new database instance
        db = AsyncDatabase()
        
        # Connect to the database
        await db.connect()
        logger.info("Successfully connected to database")
        
        # Close the connection
        await db.close()
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the initialization
    asyncio.run(init_db()) 