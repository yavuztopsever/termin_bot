from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date, time
from pydantic import BaseModel

from src.database.database import AsyncDatabase, get_db
from src.utils.rate_limiter import rate_limited
from src.monitoring.metrics import metrics_collector

router = APIRouter()

class AvailabilityRequest(BaseModel):
    date: date
    service_id: int
    doctor_id: Optional[int] = None

class AvailabilityResponse(BaseModel):
    available_slots: List[time]
    service_id: int
    doctor_id: Optional[int]
    date: date

@router.post("/check-availability", response_model=AvailabilityResponse)
@rate_limited("check_availability")
async def check_availability(
    request: AvailabilityRequest,
    db: AsyncDatabase = Depends(get_db)
) -> AvailabilityResponse:
    """Check availability for a specific date and service."""
    try:
        metrics_collector.increment("api_request", {"endpoint": "check_availability"})
        
        available_slots = await db.check_availability(
            date=request.date,
            service_id=request.service_id,
            doctor_id=request.doctor_id
        )
        
        return AvailabilityResponse(
            available_slots=available_slots,
            service_id=request.service_id,
            doctor_id=request.doctor_id,
            date=request.date
        )
    except Exception as e:
        metrics_collector.increment("api_error", {"endpoint": "check_availability"})
        raise HTTPException(status_code=500, detail=str(e))

# ... existing code ... 