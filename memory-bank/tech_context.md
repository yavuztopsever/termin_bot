# Munich Termin Automator (MTA) - Technical Context

## Status
- **Version**: 1.0.0
- **Status**: In Development
- **Last Updated**: Current
- **Next Review**: Daily

## 1. Technology Stack

### 1.1 Core Technologies
- **Programming Language**: Python 3.9+
- **Database**: SQLite
- **Cache**: Redis
- **Task Queue**: Celery
- **Web Framework**: FastAPI
- **Containerization**: Docker
- **Monitoring**: Prometheus
- **Logging**: Structured logging
- **Health Checks**: Custom implementation
- **Rate Limiting**: Custom implementation

### 1.2 Development Tools
- **Version Control**: Git
- **Package Manager**: pip
- **Virtual Environment**: venv
- **Code Quality**: pylint, black
- **Testing**: pytest
- **Documentation**: Sphinx
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus
- **Health Checks**: Custom implementation
- **Logging**: Custom implementation

### 1.3 External Services
- **Telegram Bot API**
- **Target Website API**
- **Redis Server**
- **Prometheus Server**
- **Health Check Service**
- **Logging Service**
- **Rate Limiting Service**
- **Monitoring Service**

## 2. Development Setup

### 2.1 Local Development
1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Set up environment variables
5. Initialize database
6. Start Redis server
7. Start Celery workers
8. Start monitoring
9. Start health checks
10. Start logging

### 2.2 Docker Setup
1. Build images
2. Set up environment variables
3. Start containers
4. Initialize database
5. Start Redis server
6. Start Celery workers
7. Start monitoring
8. Start health checks
9. Start logging
10. Verify setup

### 2.3 Environment Variables
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_URL=your_webhook_url

# Database
DATABASE_URL=sqlite:///app.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True

# Target Website
TARGET_WEBSITE_URL=your_target_url
TARGET_WEBSITE_API_KEY=your_api_key
TARGET_WEBSITE_RATE_LIMIT=100

# Captcha
CAPTCHA_SERVICE_URL=your_captcha_service_url
CAPTCHA_SERVICE_API_KEY=your_captcha_service_key

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp
PROMETHEUS_PORT=9090
PROMETHEUS_PATH=/metrics

# Health Checks
HEALTH_CHECK_PORT=8080
HEALTH_CHECK_PATH=/health
HEALTH_CHECK_INTERVAL=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Notifications
NOTIFICATION_EMAIL=your_email
NOTIFICATION_SMS=your_phone
NOTIFICATION_TELEGRAM=your_chat_id

# Task Queue
TASK_QUEUE_NAME=app_tasks
TASK_QUEUE_PRIORITY=1
TASK_QUEUE_RETRY_COUNT=3
TASK_QUEUE_RETRY_DELAY=300

# Appointment Check
APPOINTMENT_CHECK_INTERVAL=300
APPOINTMENT_CHECK_TIMEOUT=30
APPOINTMENT_CHECK_RETRY_COUNT=3
APPOINTMENT_CHECK_RETRY_DELAY=60

# API Rate Limits
API_RATE_LIMIT=100
API_RATE_WINDOW=3600
API_RATE_BURST=10
API_RATE_DELAY=1

# User Credentials
USER_USERNAME=your_username
USER_PASSWORD=your_password
USER_EMAIL=your_email
USER_PHONE=your_phone
```

## 3. Project Structure

### 3.1 Source Code
```
src/
├── data/
│   ├── storage/
│   │   ├── database.py
│   │   └── redis.py
│   ├── models/
│   │   ├── user.py
│   │   ├── appointment.py
│   │   └── notification.py
│   └── database/
│       ├── base.py
│       └── session.py
├── utils/
│   ├── config.py
│   ├── rate_limiter.py
│   ├── json_encoder.py
│   ├── retry.py
│   ├── logger.py
│   ├── exceptions.py
│   └── performance.py
├── control/
│   ├── manager/
│   │   ├── appointment.py
│   │   └── user.py
│   ├── analyzer/
│   │   ├── pattern.py
│   │   └── availability.py
│   ├── health/
│   │   ├── monitor.py
│   │   └── checks.py
│   ├── services/
│   │   ├── telegram.py
│   │   └── captcha.py
│   ├── pattern_analyzer/
│   │   ├── analyzer.py
│   │   └── patterns.py
│   └── rate_limiter/
│       ├── limiter.py
│       └── rules.py
├── gateway/
│   ├── middleware.py
│   ├── router.py
│   ├── api_gateway.py
│   ├── api_config.py
│   ├── app.py
│   └── routes.py
├── mesh/
│   ├── load_balancer.py
│   ├── circuit_breaker.py
│   ├── discovery.py
│   └── service_mesh.py
└── main.py
```

### 3.2 Tests
```
tests/
├── unit/
│   ├── test_api.py
│   ├── test_database.py
│   └── test_services.py
├── integration/
│   ├── test_flows.py
│   └── test_endpoints.py
└── e2e/
    ├── test_registration.py
    └── test_booking.py
```

### 3.3 Documentation
```
docs/
├── api/
│   ├── endpoints.md
│   └── models.md
├── deployment/
│   ├── docker.md
│   └── kubernetes.md
└── development/
    ├── setup.md
    └── guidelines.md
```

## 4. Configuration

### 4.1 Application Config
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str = ""

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    # Target Website
    TARGET_WEBSITE_URL: str
    TARGET_WEBSITE_API_KEY: str
    TARGET_WEBSITE_RATE_LIMIT: int = 100

    # Captcha
    CAPTCHA_SERVICE_URL: str
    CAPTCHA_SERVICE_API_KEY: str

    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_PATH: str = "/metrics"

    # Health Checks
    HEALTH_CHECK_PORT: int = 8080
    HEALTH_CHECK_PATH: str = "/health"
    HEALTH_CHECK_INTERVAL: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "app.log"
    LOG_MAX_SIZE: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    # Notifications
    NOTIFICATION_EMAIL: str
    NOTIFICATION_SMS: str
    NOTIFICATION_TELEGRAM: str

    # Task Queue
    TASK_QUEUE_NAME: str = "app_tasks"
    TASK_QUEUE_PRIORITY: int = 1
    TASK_QUEUE_RETRY_COUNT: int = 3
    TASK_QUEUE_RETRY_DELAY: int = 300

    # Appointment Check
    APPOINTMENT_CHECK_INTERVAL: int = 300
    APPOINTMENT_CHECK_TIMEOUT: int = 30
    APPOINTMENT_CHECK_RETRY_COUNT: int = 3
    APPOINTMENT_CHECK_RETRY_DELAY: int = 60

    # API Rate Limits
    API_RATE_LIMIT: int = 100
    API_RATE_WINDOW: int = 3600
    API_RATE_BURST: int = 10
    API_RATE_DELAY: int = 1

    # User Credentials
    USER_USERNAME: str
    USER_PASSWORD: str
    USER_EMAIL: str
    USER_PHONE: str

    class Config:
        env_file = ".env"
```

### 4.2 Database Models
```python
# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    telegram_id = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# models/appointment.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from .base import Base
import enum

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_type = Column(String, nullable=False)
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# models/notification.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from .base import Base
import enum

class NotificationType(enum.Enum):
    APPOINTMENT_AVAILABLE = "appointment_available"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    SYSTEM_ERROR = "system_error"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## 5. Dependencies

### 5.1 Core Dependencies
```
python-telegram-bot==20.7
aiohttp==3.9.1
SQLAlchemy==2.0.23
alembic==1.12.1
redis==5.0.1
celery==5.3.4
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0
prometheus-client==0.19.0
structlog==23.2.0
```

### 5.2 Development Dependencies
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
pylint==3.0.2
mypy==1.7.1
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
```

### 5.3 Testing Dependencies
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-xdist==3.3.1
```

### 5.4 Monitoring Dependencies
```
prometheus-client==0.19.0
structlog==23.2.0
```

## 6. Development Guidelines

### 6.1 Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings
- Keep functions small
- Use meaningful names
- Add comments when needed
- Follow SOLID principles
- Write unit tests
- Use async/await properly
- Handle errors gracefully

### 6.2 Testing Guidelines
- Write unit tests for all functions
- Write integration tests for flows
- Write end-to-end tests for features
- Use fixtures for test data
- Mock external services
- Test error cases
- Test edge cases
- Test performance
- Test security
- Test monitoring

### 6.3 Documentation Guidelines
- Keep documentation up to date
- Write clear docstrings
- Document API endpoints
- Document database schema
- Document deployment process
- Document monitoring setup
- Document health checks
- Document logging setup
- Document error handling
- Document security measures

### 6.4 Git Guidelines
- Use feature branches
- Write clear commit messages
- Keep commits small
- Review code before merging
- Update documentation
- Run tests before committing
- Follow semantic versioning
- Tag releases
- Keep history clean
- Document breaking changes

## 7. Deployment

### 7.1 Docker Setup
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A src.tasks worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis

  bot:
    build: .
    command: python src/main.py
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=sqlite:///app.db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
      - celery

volumes:
  redis_data:
```

### 7.3 Environment Setup
```bash
# setup.sh
#!/bin/bash

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Initialize database
alembic upgrade head

# Start services
docker-compose up -d
```

## 8. Monitoring

### 8.1 Metrics
- API response time
- Error rate
- Booking success rate
- System uptime
- Resource usage
- Health status
- Log volume
- Monitoring data

### 8.2 Health Checks
- API health
- Database health
- Redis health
- Celery health
- Bot health
- Monitoring health
- Logging health
- Rate limiting health

### 8.3 Logging
- Application logs
- Error logs
- Access logs
- Performance logs
- Security logs
- Health check logs
- Monitoring logs
- Rate limiting logs

## 9. Security

### 9.1 Authentication
- JWT tokens
- API keys
- User credentials
- Session management
- Rate limiting
- IP blocking
- Request validation
- Response validation

### 9.2 Authorization
- Role-based access
- Permission checks
- Resource access
- API access
- Database access
- File access
- Service access
- Monitoring access

### 9.3 Data Protection
- Encryption at rest
- Encryption in transit
- Secure storage
- Secure transmission
- Data validation
- Input sanitization
- Output encoding
- Error handling

## 10. Performance

### 10.1 Optimization
- Database queries
- API responses
- Task processing
- Resource usage
- Memory usage
- CPU usage
- Network usage
- Disk usage

### 10.2 Caching
- Redis cache
- Response cache
- Query cache
- Session cache
- Rate limit cache
- Health check cache
- Monitoring cache
- Logging cache

### 10.3 Scaling
- Horizontal scaling
- Vertical scaling
- Load balancing
- Service discovery
- Circuit breaking
- Rate limiting
- Health checking
- Monitoring 