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
        
        # Connect to the database and create tables
        await db.connect()
        logger.info("Successfully connected to database and created tables")
        
        # Verify tables were created
        async with db.async_session() as session:
            # Try a simple query to verify tables exist
            try:
                from sqlalchemy import text
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = result.scalars().all()
                logger.info(f"Created tables: {', '.join(tables)}")
            except Exception as e:
                logger.error(f"Error verifying tables: {e}")
        
        # Close the connection
        await db.close()
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the initialization
    asyncio.run(init_db())
