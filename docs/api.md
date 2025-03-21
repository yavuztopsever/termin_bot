# Munich Termin Automator API Documentation

## Overview

This document describes the internal API structure and endpoints used by the Munich Termin Automator (MTA) system.

## Base Configuration

- Base URL: `https://stadt.muenchen.de`
- API Version: Not versioned (uses direct endpoints)
- Authentication: None (public endpoints)
- Rate Limits: See configuration section
- Captcha: FriendlyCaptcha integration
- Pattern Analysis: Request pattern monitoring

## Endpoints

### 1. Check Availability

Checks for available appointment slots.

```http
POST /buergerservice/terminvereinbarung/api/availability
Content-Type: application/json
X-Captcha-Token: string
```

**Request Body:**
```json
{
    "service_id": "string",
    "location_id": "string",
    "date_range": {
        "start": "YYYY-MM-DD",
        "end": "YYYY-MM-DD"
    }
}
```

**Response:**
```json
{
    "available_slots": [
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "service_id": "string",
            "location_id": "string",
            "slot_id": "string"
        }
    ]
}
```

**Rate Limit:**
- 10 requests per 60 seconds

### 2. Book Appointment

Books a specific appointment slot.

```http
POST /buergerservice/terminvereinbarung/api/book
Content-Type: application/json
X-Captcha-Token: string
```

**Request Body:**
```json
{
    "slot_id": "string",
    "service_id": "string",
    "location_id": "string",
    "user_details": {
        "name": "string",
        "email": "string",
        "person_count": "integer"
    }
}
```

**Response:**
```json
{
    "booking_id": "string",
    "confirmation_code": "string",
    "appointment_details": {
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "service": "string",
        "location": "string"
    }
}
```

**Rate Limit:**
- 2 requests per 60 seconds

### 3. Get Available Slots

Retrieves all available slots for a service.

```http
GET /buergerservice/terminvereinbarung/api/slots
X-Captcha-Token: string
```

**Query Parameters:**
- `service_id` (required): Service identifier
- `location_id` (optional): Location identifier
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response:**
```json
{
    "slots": [
        {
            "slot_id": "string",
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "service_id": "string",
            "location_id": "string",
            "capacity": "integer"
        }
    ]
}
```

**Rate Limit:**
- 20 requests per 60 seconds

### 4. Captcha Verification

Verifies a FriendlyCaptcha token.

```http
POST /buergerservice/terminvereinbarung/api/verify-captcha
Content-Type: application/json
```

**Request Body:**
```json
{
    "token": "string",
    "site_key": "string"
}
```

**Response:**
```json
{
    "success": true,
    "expiry_time": "YYYY-MM-DDTHH:MM:SSZ"
}
```

**Rate Limit:**
- 3 requests per 60 seconds

### 5. Pattern Analysis

Analyzes request patterns for bot detection.

```http
GET /buergerservice/terminvereinbarung/api/patterns
```

**Query Parameters:**
- `window_size` (optional): Analysis window size in seconds
- `min_requests` (optional): Minimum number of requests to analyze

**Response:**
```json
{
    "patterns": {
        "request_rate": "float",
        "interval_mean": "float",
        "interval_stddev": "float",
        "variance": "float",
        "is_bot_like": "boolean"
    }
}
```

**Rate Limit:**
- 5 requests per 60 seconds

## Error Responses

All endpoints use standard HTTP status codes and return errors in the following format:

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    }
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized (Invalid Captcha)
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error
- `503`: Service Unavailable

## Rate Limiting

The system implements a token bucket algorithm for rate limiting:

```python
API_RATE_LIMITS = {
    "check_availability": {
        "limit": 10,  # requests
        "period": 60  # seconds
    },
    "book_appointment": {
        "limit": 2,   # requests
        "period": 60  # seconds
    },
    "get_slots": {
        "limit": 20,  # requests
        "period": 60  # seconds
    },
    "verify_captcha": {
        "limit": 3,   # requests
        "period": 60  # seconds
    },
    "pattern_analysis": {
        "limit": 5,   # requests
        "period": 60  # seconds
    }
}
```

When rate limits are exceeded, the API returns a 429 status code with a Retry-After header.

## Captcha Integration

The system uses FriendlyCaptcha for bot protection:

```python
CAPTCHA_CONFIG = {
    "site_key": "string",
    "secret_key": "string",
    "timeout": 30,        # seconds
    "token_lifetime": 300, # seconds
    "refresh_threshold": 60 # seconds
}
```

Token management:
- Tokens are cached with Redis
- Automatic token refresh before expiry
- Error handling for invalid tokens
- Rate limiting for verification requests

## Anti-Bot Detection

The system implements various measures to avoid bot detection:

- Random delays between requests
- Variable request patterns
- Request pattern analysis
- User-agent rotation
- IP rotation (if configured)
- Captcha verification
- Pattern-based bot detection

Configuration:
```python
ANTI_BOT_CONFIG = {
    "min_request_interval": 0.5,    # seconds
    "max_request_interval": 3.0,    # seconds
    "pattern_window_size": 60,      # seconds
    "variance_threshold": 0.1,      # minimum variance
    "max_requests_per_second": 2.0, # maximum request rate
    "min_requests_for_check": 5,    # minimum requests for pattern analysis
    "bot_detection_threshold": 0.8  # threshold for bot detection
}
```

## Health Monitoring

The system provides health metrics for monitoring:

- CPU usage
- Memory usage
- Request success rate
- Average response time
- Active tasks count
- Rate limit status
- Error count
- Captcha success rate
- Pattern analysis results
- Bot detection alerts

Metrics are collected every 60 seconds and stored for 24 hours.

## Best Practices

1. **Rate Limiting:**
   - Respect the rate limits
   - Implement exponential backoff for retries
   - Monitor rate limit status

2. **Error Handling:**
   - Always check response status codes
   - Implement proper error handling
   - Log errors with context

3. **Performance:**
   - Use connection pooling
   - Implement request caching
   - Monitor response times
   - Cache captcha tokens

4. **Security:**
   - Validate all input data
   - Sanitize output data
   - Use secure headers
   - Implement proper logging
   - Handle captcha tokens securely
   - Monitor request patterns

## Example Usage

```python
from src.api.api_config import APIConfig
from src.utils.rate_limiter import rate_limited
from src.captcha.captcha_service import CaptchaService

@rate_limited("check_availability")
def check_appointment_availability(service_id: str, location_id: str):
    api_config = APIConfig()
    captcha_service = CaptchaService()
    
    # Get valid captcha token
    token = captcha_service.get_valid_token()
    
    request_data = api_config.get_check_availability_request(
        service_id=service_id,
        location_id=location_id,
        captcha_token=token
    )
    
    response = requests.post(
        request_data["url"],
        headers=request_data["headers"],
        json=request_data["body"]
    )
    
    # Check for captcha errors
    if response.status_code == 401:
        captcha_service.invalidate_token(token)
        return check_appointment_availability(service_id, location_id)
    
    return api_config.parse_availability_response(response.json()) 