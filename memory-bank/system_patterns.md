# Munich Termin Automator (MTA) - System Patterns

## Status
- **Version**: 1.0.0
- **Status**: In Development
- **Last Updated**: Current
- **Next Review**: Daily

## 1. Design Patterns

### 1.1 Repository Pattern
```python
# data/storage/database.py
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from ..models.base import Base

T = TypeVar('T', bound=Base)

class Repository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get(self, id: int) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self) -> List[T]:
        return self.session.query(self.model).all()

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        return entity

    def update(self, entity: T) -> T:
        self.session.commit()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.commit()
```

### 1.2 Service Pattern
```python
# control/manager/appointment.py
from typing import List, Optional
from datetime import datetime
from ...data.models.appointment import Appointment
from ...data.storage.database import Repository

class AppointmentService:
    def __init__(self, repository: Repository[Appointment]):
        self.repository = repository

    def get_appointment(self, id: int) -> Optional[Appointment]:
        return self.repository.get(id)

    def get_appointments(self) -> List[Appointment]:
        return self.repository.get_all()

    def create_appointment(self, appointment: Appointment) -> Appointment:
        return self.repository.create(appointment)

    def update_appointment(self, appointment: Appointment) -> Appointment:
        return self.repository.update(appointment)

    def delete_appointment(self, appointment: Appointment) -> None:
        self.repository.delete(appointment)
```

### 1.3 Observer Pattern
```python
# control/manager/events.py
from typing import List, Callable
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    APPOINTMENT_AVAILABLE = "appointment_available"
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    ERROR = "error"

@dataclass
class Event:
    type: EventType
    data: dict

class EventManager:
    def __init__(self):
        self.observers: List[Callable[[Event], None]] = []

    def add_observer(self, observer: Callable[[Event], None]) -> None:
        self.observers.append(observer)

    def remove_observer(self, observer: Callable[[Event], None]) -> None:
        self.observers.remove(observer)

    def notify(self, event: Event) -> None:
        for observer in self.observers:
            observer(event)
```

### 1.4 Factory Pattern
```python
# control/manager/factory.py
from typing import Type
from ...data.models.base import Base
from ...data.storage.database import Repository
from .appointment import AppointmentService
from .user import UserService

class ServiceFactory:
    @staticmethod
    def create_service(model: Type[Base], repository: Repository) -> Any:
        if model.__name__ == "Appointment":
            return AppointmentService(repository)
        elif model.__name__ == "User":
            return UserService(repository)
        raise ValueError(f"Unknown model: {model.__name__}")
```

### 1.5 Strategy Pattern
```python
# control/analyzer/pattern.py
from abc import ABC, abstractmethod
from typing import List, Dict

class PatternAnalyzer(ABC):
    @abstractmethod
    def analyze(self, data: List[Dict]) -> Dict:
        pass

class TimePatternAnalyzer(PatternAnalyzer):
    def analyze(self, data: List[Dict]) -> Dict:
        # Implement time-based pattern analysis
        pass

class LocationPatternAnalyzer(PatternAnalyzer):
    def analyze(self, data: List[Dict]) -> Dict:
        # Implement location-based pattern analysis
        pass
```

### 1.6 Command Pattern
```python
# control/manager/commands.py
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    @abstractmethod
    def execute(self) -> Any:
        pass

class CheckAppointmentCommand(Command):
    def __init__(self, service: AppointmentService, appointment_id: int):
        self.service = service
        self.appointment_id = appointment_id

    def execute(self) -> Any:
        return self.service.get_appointment(self.appointment_id)

class BookAppointmentCommand(Command):
    def __init__(self, service: AppointmentService, appointment: Appointment):
        self.service = service
        self.appointment = appointment

    def execute(self) -> Any:
        return self.service.create_appointment(self.appointment)
```

## 2. Architectural Patterns

### 2.1 Layered Architecture
```
src/
├── data/           # Data Layer
│   ├── storage/    # Data Access
│   ├── models/     # Data Models
│   └── database/   # Database
├── control/        # Control Layer
│   ├── manager/    # Business Logic
│   ├── analyzer/   # Analysis
│   └── services/   # Services
├── gateway/        # Gateway Layer
│   ├── api/        # API Gateway
│   └── bot/        # Bot Gateway
└── utils/          # Utility Layer
    ├── config/     # Configuration
    └── helpers/    # Helpers
```

### 2.2 CQRS Pattern
```python
# control/manager/cqrs.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class AppointmentQuery:
    id: int

@dataclass
class AppointmentCommand:
    service_type: str
    appointment_date: datetime
    user_id: int

class AppointmentQueryHandler:
    def handle(self, query: AppointmentQuery) -> Optional[Appointment]:
        # Handle query
        pass

class AppointmentCommandHandler:
    def handle(self, command: AppointmentCommand) -> Appointment:
        # Handle command
        pass
```

### 2.3 Event Sourcing
```python
# control/manager/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class Event:
    id: int
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    version: int

class EventStore:
    def append(self, event: Event) -> None:
        # Store event
        pass

    def get_events(self, aggregate_id: str) -> List[Event]:
        # Get events for aggregate
        pass
```

## 3. Integration Patterns

### 3.1 API Gateway
```python
# gateway/api_gateway.py
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from ..control.manager.appointment import AppointmentService

app = FastAPI()

@app.get("/appointments/{id}")
async def get_appointment(id: int):
    try:
        return await appointment_service.get_appointment(id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/appointments")
async def create_appointment(appointment: Dict[str, Any]):
    try:
        return await appointment_service.create_appointment(appointment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 3.2 Service Mesh
```python
# mesh/service_mesh.py
from typing import Dict, Any
import aiohttp

class ServiceMesh:
    def __init__(self):
        self.services: Dict[str, str] = {}

    async def register_service(self, name: str, url: str) -> None:
        self.services[name] = url

    async def call_service(self, name: str, method: str, path: str, data: Dict[str, Any] = None) -> Any:
        if name not in self.services:
            raise ValueError(f"Service {name} not found")
        
        url = f"{self.services[name]}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data) as response:
                return await response.json()
```

### 3.3 Circuit Breaker
```python
# mesh/circuit_breaker.py
from enum import Enum
from typing import Callable, Any
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise e
```

### 3.4 Load Balancer
```python
# mesh/load_balancer.py
from typing import List, Dict, Any
import random

class LoadBalancer:
    def __init__(self):
        self.services: List[Dict[str, Any]] = []

    def add_service(self, service: Dict[str, Any]) -> None:
        self.services.append(service)

    def remove_service(self, service_id: str) -> None:
        self.services = [s for s in self.services if s["id"] != service_id]

    def get_service(self) -> Dict[str, Any]:
        if not self.services:
            raise Exception("No services available")
        return random.choice(self.services)
```

## 4. Testing Patterns

### 4.1 Unit Testing
```python
# tests/unit/test_appointment_service.py
import pytest
from unittest.mock import Mock
from src.control.manager.appointment import AppointmentService
from src.data.models.appointment import Appointment

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def appointment_service(mock_repository):
    return AppointmentService(mock_repository)

def test_get_appointment(appointment_service, mock_repository):
    # Arrange
    appointment = Appointment(id=1, service_type="test")
    mock_repository.get.return_value = appointment

    # Act
    result = appointment_service.get_appointment(1)

    # Assert
    assert result == appointment
    mock_repository.get.assert_called_once_with(1)
```

### 4.2 Integration Testing
```python
# tests/integration/test_appointment_flow.py
import pytest
from src.control.manager.appointment import AppointmentService
from src.data.storage.database import Repository
from src.data.models.appointment import Appointment

@pytest.mark.asyncio
async def test_appointment_flow():
    # Arrange
    repository = Repository(Appointment, session)
    service = AppointmentService(repository)
    appointment = Appointment(service_type="test")

    # Act
    created = await service.create_appointment(appointment)
    retrieved = await service.get_appointment(created.id)

    # Assert
    assert retrieved == created
    assert retrieved.service_type == "test"
```

### 4.3 End-to-End Testing
```python
# tests/e2e/test_booking_flow.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_booking_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to website
        await page.goto("http://localhost:8000")

        # Login
        await page.fill("#username", "test_user")
        await page.fill("#password", "test_pass")
        await page.click("#login")

        # Book appointment
        await page.click("#book_appointment")
        await page.fill("#service_type", "test")
        await page.fill("#date", "2024-01-01")
        await page.click("#submit")

        # Verify booking
        assert await page.text_content("#success_message") == "Appointment booked successfully"
```

## 5. Monitoring Patterns

### 5.1 Metrics Collection
```python
# control/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any

# Metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests')
response_time = Histogram('http_response_time_seconds', 'HTTP response time')
error_counter = Counter('http_errors_total', 'Total HTTP errors')
active_users = Gauge('active_users', 'Number of active users')

class MetricsCollector:
    def record_request(self, method: str, path: str) -> None:
        request_counter.labels(method=method, path=path).inc()

    def record_response_time(self, method: str, path: str, duration: float) -> None:
        response_time.labels(method=method, path=path).observe(duration)

    def record_error(self, method: str, path: str, error_type: str) -> None:
        error_counter.labels(method=method, path=path, error=error_type).inc()

    def update_active_users(self, count: int) -> None:
        active_users.set(count)
```

### 5.2 Health Checks
```python
# control/health/checks.py
from typing import Dict, Any
import aiohttp

class HealthChecker:
    def __init__(self):
        self.checks: Dict[str, Callable] = {}

    def add_check(self, name: str, check: Callable) -> None:
        self.checks[name] = check

    async def check_health(self) -> Dict[str, Any]:
        results = {}
        for name, check in self.checks.items():
            try:
                results[name] = await check()
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results

class DatabaseHealthCheck:
    async def check(self) -> Dict[str, Any]:
        # Implement database health check
        pass

class RedisHealthCheck:
    async def check(self) -> Dict[str, Any]:
        # Implement Redis health check
        pass
```

### 5.3 Logging
```python
# utils/logger.py
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class LogManager:
    def __init__(self):
        self.logger = structlog.get_logger()

    def info(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self.logger.info(message, **kwargs)

    def error(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self.logger.error(message, **kwargs)

    def debug(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self.logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs: Dict[str, Any]) -> None:
        self.logger.warning(message, **kwargs)
```

## 6. Security Patterns

### 6.1 Authentication
```python
# control/auth/authentication.py
from typing import Optional
import jwt
from datetime import datetime, timedelta

class JWTManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_token(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### 6.2 Authorization
```python
# control/auth/authorization.py
from enum import Enum
from typing import List, Optional

class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class AuthorizationManager:
    def __init__(self):
        self.role_permissions: Dict[Role, List[Permission]] = {
            Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
            Role.USER: [Permission.READ, Permission.WRITE],
            Role.GUEST: [Permission.READ]
        }

    def has_permission(self, role: Role, permission: Permission) -> bool:
        return permission in self.role_permissions.get(role, [])
```

### 6.3 Rate Limiting
```python
# control/rate_limiter/limiter.py
from typing import Dict, Any
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self.requests[client_id] = [t for t in self.requests[client_id] if t > minute_ago]

        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False

        self.requests[client_id].append(now)
        return True
```

## 7. Performance Patterns

### 7.1 Caching
```python
# utils/cache.py
from typing import Any, Optional
import redis
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return value if value else None

    async def set(self, key: str, value: Any, expire: int = 3600) -> None:
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
```

### 7.2 Connection Pooling
```python
# data/storage/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

class DatabaseManager:
    def __init__(self, url: str, pool_size: int = 5):
        self.engine = create_engine(url, pool_size=pool_size)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        session = self.Session()
        try:
            yield session
        finally:
            session.close()
```

### 7.3 Async Processing
```python
# control/tasks/processor.py
from typing import List, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncProcessor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch(self, items: List[Any], processor: Callable) -> List[Any]:
        loop = asyncio.get_event_loop()
        tasks = []
        for item in items:
            task = loop.run_in_executor(self.executor, processor, item)
            tasks.append(task)
        return await asyncio.gather(*tasks)
``` 