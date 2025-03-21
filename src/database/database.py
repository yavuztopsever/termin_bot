from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from redis import asyncio as aioredis
import asyncpg
import logging
from fastapi import Depends

from src.config.config import REDIS_URL, DATABASE_URL

logger = logging.getLogger(__name__)

class AsyncDatabase:
    def __init__(self, pool: asyncpg.Pool, redis: aioredis.Redis):
        self.pool = pool
        self.redis = redis

    async def ping(self) -> bool:
        """Check database connection."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False

    async def check_availability(
        self,
        date: date,
        service_id: int,
        doctor_id: Optional[int] = None
    ) -> List[time]:
        """Check available slots for a given date and service."""
        try:
            async with self.pool.acquire() as conn:
                query = """
                SELECT time_slot
                FROM available_slots
                WHERE date = $1 AND service_id = $2
                """
                params = [date, service_id]
                
                if doctor_id is not None:
                    query += " AND doctor_id = $3"
                    params.append(doctor_id)
                
                query += " ORDER BY time_slot"
                
                rows = await conn.fetch(query, *params)
                return [row['time_slot'] for row in rows]
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            raise

    async def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        try:
            return {
                "base_url": "http://test.com",
                "headers": {"Authorization": "test"}
            }
        except Exception as e:
            logger.error("Failed to get API configuration", error=str(e))
            raise

    async def book_appointment(
        self,
        date: date,
        time_slot: time,
        service_id: int,
        doctor_id: Optional[int] = None,
        patient_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Book an appointment."""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if slot is available
                    available = await self.check_availability(date, service_id, doctor_id)
                    if time_slot not in available:
                        raise ValueError("Time slot not available")
                    
                    # Insert appointment
                    row = await conn.fetchrow("""
                        INSERT INTO appointments (
                            date, time_slot, service_id, doctor_id, patient_data
                        ) VALUES ($1, $2, $3, $4, $5)
                        RETURNING *
                        """,
                        date, time_slot, service_id, doctor_id, patient_data
                    )
                    
                    # Remove slot from available_slots
                    await conn.execute("""
                        DELETE FROM available_slots
                        WHERE date = $1 AND time_slot = $2 AND service_id = $3
                        AND (doctor_id = $4 OR doctor_id IS NULL)
                        """,
                        date, time_slot, service_id, doctor_id
                    )
                    
                    return dict(row)
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            raise

async def get_db() -> AsyncDatabase:
    """Get database instance."""
    # Create connection pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    # Create Redis connection
    redis = await aioredis.from_url(REDIS_URL)
    
    try:
        yield AsyncDatabase(pool, redis)
    finally:
        await pool.close()
        await redis.close() 