# Munich Termin Automator (MTA) - API Edition

A Telegram bot that automatically monitors, finds, and books appointments at Munich's public service offices through API requests. The bot uses SQLite with SQLAlchemy for data persistence, Redis for task queuing and rate limiting, and Celery for background task processing.

## Features

- 🔍 Monitors appointment availability through API requests
- 📅 Books appointments automatically when found
- 🤖 Telegram bot interface for easy interaction
- 🔔 Real-time notifications for appointment availability and booking
- 🛡️ Rate limiting and anti-bot detection measures
- 📊 Structured logging and monitoring capabilities
- 🐳 Docker support for easy deployment
- 📈 Health monitoring and metrics collection
- 🔄 Asynchronous task processing with Celery

## Prerequisites

- Python 3.9+
- Redis
- SQLite
- Docker and Docker Compose (for containerized deployment)

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yavuztopsever/termin_bot.git
   cd termin_bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python scripts/init_db.py
   ```

6. Start Redis:
   ```bash
   docker-compose up -d redis
   ```

7. Start Celery worker:
   ```bash
   celery -A src.tasks.celery worker --loglevel=info
   ```

8. Run the bot:
   ```bash
   python src/main.py
   ```

### Docker Deployment

1. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

2. Monitor the logs:
   ```bash
   docker-compose logs -f
   ```

3. Stop the containers:
   ```bash
   docker-compose down
   ```

## Usage

1. Start a chat with the bot on Telegram
2. Use the following commands:
   - `/start` - Initialize the bot and get help
   - `/subscribe` - Subscribe to appointment notifications
   - `/list` - List your active subscriptions
   - `/check` - Check appointments now
   - `/appointments` - View your appointments
   - `/settings` - Change your preferences
   - `/help` - Show help message
   - `/abort` - Cancel current operation

## Project Structure

```
termin_bot/
├── src/
│   ├── api/              # API interaction
│   ├── bot/             # Telegram bot
│   ├── config/          # Configuration
│   ├── database/        # SQLite database operations
│   ├── tasks/           # Celery tasks
│   ├── utils/           # Utilities
│   └── main.py          # Application entry point
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── scripts/             # Utility scripts
├── docs/               # Documentation
├── logs/               # Log files
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
├── docker-compose.yml # Container orchestration
└── README.md          # This file
```

## Architecture

### Database
- SQLite database using SQLAlchemy ORM
- Asynchronous database operations with aiosqlite
- Models for Users, Subscriptions, Appointments, and Notifications

### Task Queue
- Celery for background task processing
- Redis as message broker and result backend
- Key tasks for appointment checking and booking

### Rate Limiting
- Redis-based rate limiting for external API calls
- Configurable limits per operation type
- Default limits:
  - Check availability: 10 requests per minute
  - Book appointment: 5 requests per minute

### Monitoring
- Structured logging with structlog
- Error tracking with Sentry
- Performance metrics collection
- Health check endpoints:
  - `/monitoring/health`
  - `/monitoring/metrics`
  - `/monitoring/metrics/history`
  - `/monitoring/status/detailed`

## Configuration

The application can be configured using environment variables or a `.env` file:

### Database Configuration
- `DATABASE_URL`: SQLite database URL
- `REDIS_URI`: Redis connection URI

### API Configuration
- `API_BASE_URL`: Base URL for API requests
- `API_KEY`: API key for authentication
- `API_TIMEOUT`: Request timeout in seconds

### Rate Limiting Configuration
- `RATE_LIMIT_CONFIG`: Rate limiting settings
  - `tokens_per_second`: Rate of token generation
  - `bucket_capacity`: Maximum token capacity
  - `pattern_window_size`: Window size for pattern detection
  - `min_interval_variance`: Minimum interval variance
  - `min_requests_for_check`: Minimum requests for pattern check
  - `rate_limit_threshold`: Rate limit threshold

### Health Check Configuration
- `HEALTH_CHECK_CONFIG`: Health monitoring settings
  - `interval`: Check interval in seconds
  - `history_size`: Metrics history size
  - `thresholds`: Warning and critical thresholds

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test types
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

### Code Style and Quality

The project follows strict code quality standards:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking
- isort for import sorting

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the code style guide
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Redis](https://redis.io/)
- [Celery](https://docs.celeryproject.org/)
- [structlog](https://www.structlog.org/) 