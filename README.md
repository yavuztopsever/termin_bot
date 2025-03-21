# Munich Termin Automator (MTA) - API Edition

A Telegram bot that automatically monitors, finds, and books appointments at Munich's public service offices through API requests.

## Features

- 🔍 Monitors appointment availability through API requests
- 📅 Books appointments automatically when found
- 🤖 Telegram bot interface for easy interaction
- 🔔 Real-time notifications for appointment availability and booking
- 🛡️ Rate limiting and anti-bot detection measures
- 📊 Logging and monitoring capabilities
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.9+
- MongoDB
- Redis
- Chrome/Chromium (for website analysis)
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

4. Create a `.env` file with your configuration:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   MONGO_PASSWORD=your_mongodb_password
   LOG_LEVEL=INFO
   CHECK_INTERVAL=15
   NUM_WORKERS=3
   ```

5. Run the application:
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
│   ├── analyzer/         # Website analysis
│   ├── bot/             # Telegram bot
│   ├── config/          # Configuration
│   ├── database/        # Database operations
│   ├── manager/         # Appointment management
│   ├── utils/           # Utilities
│   └── main.py          # Application entry point
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── logs/                # Log files
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
├── docker-compose.yml  # Container orchestration
└── README.md           # This file
```

## Configuration

The application can be configured using environment variables or a `.env` file:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `MONGODB_URI`: MongoDB connection URI
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CHECK_INTERVAL`: Minutes between appointment checks
- `NUM_WORKERS`: Number of worker threads
- `RETRY_DELAY`: Seconds between retries
- `MAX_RETRIES`: Maximum number of retries
- `DOCKER_MODE`: Whether running in Docker (True/False)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run with coverage
pytest --cov=src tests/
```

### Code Style

The project follows PEP 8 style guide. Use `black` for formatting and `flake8` for linting:

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [MongoDB](https://www.mongodb.com/)
- [Redis](https://redis.io/)
- [Selenium](https://www.selenium.dev/) 