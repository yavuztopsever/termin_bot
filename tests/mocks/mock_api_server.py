"""Mock API server for testing."""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import time
import random
from pydantic import BaseModel

app = FastAPI(title="Mock Munich API Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
appointments: Dict[str, Dict] = {}
bookings: Dict[str, Dict] = {}
rate_limits: Dict[str, List[float]] = {}

class AppointmentSlot(BaseModel):
    """Appointment slot model."""
    date: str
    time: str
    service_id: str
    location_id: str
    capacity: int = 1

class BookingRequest(BaseModel):
    """Booking request model."""
    slot_id: str
    service_id: str
    location_id: str
    user_details: Dict[str, str]

def check_rate_limit(client_ip: str, limit: int = 10, period: int = 60) -> bool:
    """Check if request is within rate limit."""
    now = time.time()
    if client_ip not in rate_limits:
        rate_limits[client_ip] = []
    
    # Remove old timestamps
    rate_limits[client_ip] = [ts for ts in rate_limits[client_ip] if now - ts < period]
    
    # Check limit
    if len(rate_limits[client_ip]) >= limit:
        return False
    
    # Add new timestamp
    rate_limits[client_ip].append(now)
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    response = await call_next(request)
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/buergerservice/terminvereinbarung/api/availability")
async def check_availability(
    service_id: str,
    location_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Check appointment availability."""
    try:
        # Simulate processing delay
        time.sleep(random.uniform(0.1, 0.5))
        
        # Generate mock slots
        slots = []
        start_date = datetime.strptime(date_from, "%Y-%m-%d") if date_from else datetime.now()
        end_date = datetime.strptime(date_to, "%Y-%m-%d") if date_to else start_date + timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            # Add random slots
            if random.random() < 0.3:  # 30% chance of available slot
                slot = AppointmentSlot(
                    date=current_date.strftime("%Y-%m-%d"),
                    time=f"{random.randint(9,16):02d}:00",
                    service_id=service_id,
                    location_id=location_id or "10187259",
                    capacity=random.randint(1, 3)
                )
                slots.append(slot.dict())
                
                # Store slot
                slot_id = f"{slot.date}_{slot.time}_{slot.service_id}_{slot.location_id}"
                appointments[slot_id] = slot.dict()
            
            current_date += timedelta(days=1)
        
        return {"slots": slots}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/buergerservice/terminvereinbarung/api/book")
async def book_appointment(booking: BookingRequest):
    """Book an appointment."""
    try:
        # Simulate processing delay
        time.sleep(random.uniform(0.2, 0.8))
        
        # Check if slot exists
        slot = appointments.get(booking.slot_id)
        if not slot:
            raise HTTPException(
                status_code=404,
                detail="Appointment slot not found"
            )
        
        # Check if slot is already booked
        if booking.slot_id in bookings:
            raise HTTPException(
                status_code=409,
                detail="Appointment slot already booked"
            )
        
        # Create booking
        booking_id = f"BOOKING_{int(time.time())}_{random.randint(1000, 9999)}"
        confirmation_code = f"CONF{random.randint(100000, 999999)}"
        
        booking_data = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "slot": slot,
            "user_details": booking.user_details,
            "created_at": datetime.now().isoformat()
        }
        
        bookings[booking.slot_id] = booking_data
        
        return {
            "success": True,
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "appointment_details": {
                "date": slot["date"],
                "time": slot["time"],
                "service": slot["service_id"],
                "location": slot["location_id"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/buergerservice/terminvereinbarung/api/booking/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details."""
    try:
        # Find booking by ID
        booking = next(
            (b for b in bookings.values() if b["booking_id"] == booking_id),
            None
        )
        
        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete("/buergerservice/terminvereinbarung/api/booking/{booking_id}")
async def cancel_booking(booking_id: str):
    """Cancel a booking."""
    try:
        # Find booking by ID
        slot_id = next(
            (sid for sid, b in bookings.items() if b["booking_id"] == booking_id),
            None
        )
        
        if not slot_id:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )
        
        # Remove booking
        del bookings[slot_id]
        
        return {"success": True, "message": "Booking cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the mock API server."""
    uvicorn.run(app, host=host, port=port)

class MockAPIServer:
    """Mock API server manager."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server_thread = None
        
    def start(self):
        """Start the mock API server."""
        if self.server_thread is None:
            self.server_thread = threading.Thread(
                target=run_server,
                args=(self.host, self.port),
                daemon=True
            )
            self.server_thread.start()
            
            # Wait for server to start
            time.sleep(1)
            
    def stop(self):
        """Stop the mock API server."""
        # Server will stop when the thread is terminated
        self.server_thread = None
        
    def clear_data(self):
        """Clear all stored data."""
        appointments.clear()
        bookings.clear()
        rate_limits.clear()

if __name__ == "__main__":
    # Run server directly if script is executed
    run_server() 