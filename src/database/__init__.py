"""Database package initialization."""

from typing import Optional
import redis.asyncio as redis

from src.database.db import AsyncDatabase

# Global database instance
db: Optional[AsyncDatabase] = None

async def get_database() -> AsyncDatabase:
    """Get the database instance."""
    global db
    if db is None:
        db = AsyncDatabase()
        await db.connect()
    return db

async def get_redis(redis_uri: str) -> redis.Redis:
    """Get a Redis connection."""
    return redis.from_url(redis_uri, encoding="utf-8", decode_responses=True)
