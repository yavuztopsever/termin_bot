# Munich Termin Automator - Developer Guide

## 1. Development Environment Setup

### 1.1 Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git
- IDE (recommended: VSCode with Python extension)
- Redis Desktop Manager (optional)
- FriendlyCaptcha account for development

### 1.2 Initial Setup
```bash
# Clone repository
git clone https://github.com/yourusername/termin_bot.git
cd termin_bot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Setup pre-commit hooks
pre-commit install

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configurations
```

## 2. Project Structure

```
termin_bot/
├── src/
│   ├── api/            # API interaction
│   ├── analyzer/       # Website analysis
│   ├── bot/            # Telegram bot
│   ├── captcha/        # Captcha service
│   ├── config/         # Configuration
│   ├── database/       # Database models
│   ├── manager/        # Appointment management
│   ├── monitoring/     # Monitoring system
│   ├── patterns/       # Pattern analysis
│   └── utils/          # Utilities
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── e2e/           # End-to-end tests
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── docker/            # Docker configurations
```

## 3. Development Workflow

### 3.1 Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push changes
git push origin feature/your-feature

# Create pull request
# Wait for review and merge
```

### 3.2 Code Style
- Follow PEP 8
- Use type hints
- Document functions and classes
- Keep functions focused and small
- Use meaningful variable names
- Implement proper error handling
- Add logging for critical operations

Example:
```python
from typing import List, Dict, Optional
from datetime import datetime
import logging
from src.captcha.captcha_service import CaptchaService
from src.patterns.pattern_analyzer import PatternAnalyzer

logger = logging.getLogger(__name__)

def check_availability(
    service_id: str,
    location_id: Optional[str] = None,
    date_range: Optional[Dict[str, datetime]] = None
) -> List[Dict[str, str]]:
    """
    Check appointment availability for a service.

    Args:
        service_id: Service identifier
        location_id: Optional location identifier
        date_range: Optional date range for filtering

    Returns:
        List of available appointment slots

    Raises:
        CaptchaError: If captcha verification fails
        RateLimitError: If rate limit is exceeded
        BotDetectionError: If bot-like behavior is detected
    """
    try:
        # Verify captcha
        captcha_service = CaptchaService()
        captcha_service.verify_token()
        
        # Check for bot-like patterns
        pattern_analyzer = PatternAnalyzer()
        pattern_analyzer.analyze_request()
        
        # Implementation
        logger.info(f"Checking availability for service: {service_id}")
        # ... rest of the implementation
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        raise
```

## 4. Testing

### 4.1 Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_api_config.py

# Run with coverage
pytest --cov=src tests/

# Generate coverage report
coverage html

# Run captcha tests
pytest tests/unit/test_captcha_service.py

# Run pattern analysis tests
pytest tests/unit/test_pattern_analyzer.py
```

### 4.2 Writing Tests

#### Unit Tests
```python
# tests/unit/test_captcha_service.py
from unittest.mock import Mock, patch
import pytest
from src.captcha.captcha_service import CaptchaService

def test_verify_token():
    service = CaptchaService()
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {"success": True}
        assert service.verify_token() is True

def test_verify_token_failure():
    service = CaptchaService()
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {"success": False}
        with pytest.raises(CaptchaError):
            service.verify_token()

# tests/unit/test_pattern_analyzer.py
from src.patterns.pattern_analyzer import PatternAnalyzer

def test_analyze_request():
    analyzer = PatternAnalyzer()
    with patch('redis.Redis') as mock_redis:
        mock_redis.return_value.get.return_value = 5
        assert analyzer.analyze_request() is True

def test_detect_bot_behavior():
    analyzer = PatternAnalyzer()
    with patch('redis.Redis') as mock_redis:
        mock_redis.return_value.get.return_value = 100
        with pytest.raises(BotDetectionError):
            analyzer.analyze_request()
```

#### Integration Tests
```python
# tests/integration/test_appointment_workflow.py
import pytest
from src.manager.appointment_manager import AppointmentManager
from src.database.db import db

@pytest.mark.integration
def test_appointment_check_and_book():
    manager = AppointmentManager()
    result = manager.check_and_book_appointment(
        service_id="test_service",
        user_id="test_user"
    )
    
    # Verify database state
    booking = db.get_appointment("test_user")
    assert booking is not None
    assert booking["status"] == "booked"
```

### 4.3 Mocking
```python
# tests/unit/test_bot.py
from unittest.mock import Mock, patch
from src.bot.telegram_bot import TelegramBot

@patch('src.bot.telegram_bot.bot.send_message')
def test_notify_user(mock_send):
    bot = TelegramBot()
    bot.notify_user(
        user_id="123",
        message="Test notification"
    )
    
    mock_send.assert_called_once_with(
        chat_id="123",
        text="Test notification"
    )
```

## 5. Debugging

### 5.1 Local Debugging
```python
import logging
import pdb

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def problematic_function():
    try:
        # Some code
        pdb.set_trace()  # Breakpoint
    except Exception as e:
        logger.exception("Error occurred")
```

### 5.2 Remote Debugging
```python
import debugpy

# Enable debugging
debugpy.listen(("0.0.0.0", 5678))
```

## 6. Performance Optimization

### 6.1 Profiling
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Function to profile
    result = your_function()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()
```

### 6.2 Memory Optimization
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Implementation
```

## 7. API Development

### 7.1 Adding New Endpoints
1. Update API configuration in `src/api/api_config.py`
2. Implement request/response handling
3. Add rate limiting
4. Add captcha verification
5. Add pattern analysis
6. Add tests
7. Update documentation

Example:
```python
# src/api/api_config.py
class APIConfig:
    def get_check_availability_request(
        self,
        service_id: str,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get request configuration for checking availability.
        
        Args:
            service_id: Service identifier
            location_id: Optional location identifier
            
        Returns:
            Request configuration dictionary
        """
        return {
            "method": "POST",
            "url": f"{self.base_url}/check_availability",
            "headers": {
                "Content-Type": "application/json",
                "X-Captcha-Token": self.captcha_service.get_valid_token()
            },
            "body": {
                "service_id": service_id,
                "location_id": location_id
            }
        }
```

### 7.2 Rate Limiting
```python
# src/api/rate_limiter.py
class RateLimiter:
    def __init__(self):
        self.redis = Redis()
        self.tokens_per_second = 10.0
        self.bucket_capacity = 100.0
        
    def check_rate_limit(self, key: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            key: Rate limit key (e.g., IP address)
            
        Returns:
            True if request is allowed, False otherwise
        """
        current = self.redis.get(f"rate_limit:{key}")
        if current is None:
            self.redis.setex(f"rate_limit:{key}", 60, 1)
            return True
            
        if float(current) >= self.bucket_capacity:
            return False
            
        self.redis.incr(f"rate_limit:{key}")
        return True
```

### 7.3 Captcha Integration
```python
# src/captcha/captcha_service.py
class CaptchaService:
    def __init__(self):
        self.site_key = os.getenv("CAPTCHA_SITE_KEY")
        self.secret_key = os.getenv("CAPTCHA_SECRET_KEY")
        self.timeout = int(os.getenv("CAPTCHA_TIMEOUT", 30))
        
    def verify_token(self, token: str) -> bool:
        """
        Verify captcha token.
        
        Args:
            token: Captcha token to verify
            
        Returns:
            True if token is valid, False otherwise
            
        Raises:
            CaptchaError: If verification fails
        """
        try:
            response = requests.post(
                "https://api.friendlycaptcha.com/api/v1/siteverify",
                json={
                    "solution": token,
                    "secret": self.secret_key
                },
                timeout=self.timeout
            )
            result = response.json()
            
            if not result.get("success"):
                raise CaptchaError("Invalid captcha token")
                
            return True
            
        except Exception as e:
            raise CaptchaError(f"Captcha verification failed: {str(e)}")
```

### 7.4 Pattern Analysis
```python
# src/patterns/pattern_analyzer.py
class PatternAnalyzer:
    def __init__(self):
        self.redis = Redis()
        self.window_size = int(os.getenv("ANTI_BOT_PATTERN_WINDOW_SIZE", 60))
        self.min_requests = int(os.getenv("ANTI_BOT_MIN_REQUESTS_FOR_CHECK", 5))
        self.threshold = float(os.getenv("ANTI_BOT_DETECTION_THRESHOLD", 0.8))
        
    def analyze_request(self, key: str) -> bool:
        """
        Analyze request patterns for bot detection.
        
        Args:
            key: Request identifier (e.g., IP address)
            
        Returns:
            True if request pattern is normal, False if bot-like
            
        Raises:
            BotDetectionError: If bot-like behavior is detected
        """
        try:
            # Get request count in window
            count = int(self.redis.get(f"pattern:{key}") or 0)
            
            # Check if enough requests for analysis
            if count < self.min_requests:
                self.redis.incr(f"pattern:{key}")
                self.redis.expire(f"pattern:{key}", self.window_size)
                return True
                
            # Analyze pattern
            if count > self.threshold * self.window_size:
                raise BotDetectionError("Bot-like behavior detected")
                
            return True
            
        except Exception as e:
            raise BotDetectionError(f"Pattern analysis failed: {str(e)}")
```

## 8. Monitoring and Logging

### 8.1 Metrics Collection
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram

# Define metrics
request_counter = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['endpoint', 'status']
)

request_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint']
)

captcha_counter = Counter(
    'captcha_verifications_total',
    'Total number of captcha verifications',
    ['status']
)

pattern_counter = Counter(
    'pattern_analysis_total',
    'Total number of pattern analyses',
    ['result']
)
```

### 8.2 Logging Configuration
```python
# src/config/logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'app.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## 9. Error Handling

### 9.1 Custom Exceptions
```python
class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds",
            status_code=429
        )
```

### 9.2 Error Recovery
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def retry_operation():
    # Implementation
```

## 10. Security Best Practices

### 10.1 Input Validation
```python
from pydantic import BaseModel, validator

class AppointmentRequest(BaseModel):
    service_id: str
    location_id: str
    date: datetime
    
    @validator("service_id")
    def validate_service_id(cls, v):
        if not v.isalnum():
            raise ValueError("Invalid service ID format")
        return v
```

### 10.2 Secure Configuration
```python
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str) -> str:
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()
```

## 11. Contributing Guidelines

### 11.1 Pull Request Process
1. Create feature branch
2. Write tests
3. Update documentation
4. Submit PR with description
5. Address review comments
6. Merge after approval

### 11.2 Code Review Checklist
- [ ] Tests included
- [ ] Documentation updated
- [ ] Type hints used
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Security considerations addressed
- [ ] Performance impact considered 