# München Termin Bot

An automated appointment booking bot for München city services using Puppeteer and Twilio for notifications.

## Features

- Dual approach: Browser-based and direct API requests for maximum efficiency
- Randomized check intervals (5-8 seconds) to avoid detection
- Adaptive timing with more aggressive checks during peak hours
- User agent rotation and browser fingerprinting protection
- Robust error handling with exponential backoff and retry logic
- Comprehensive logging and debugging capabilities
- Desktop and SMS notifications via Twilio
- Automatic booking when slots become available
- Parallel processing for multiple locations
- Debug mode with screenshots and network monitoring
- Docker support for easy deployment

## Prerequisites

- Node.js (v14 or higher) or Docker
- npm (Node Package Manager) if not using Docker
- A Twilio account for SMS notifications

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yavuztopsever/termin_bot.git
cd termin_bot
```

2. Install dependencies:
```bash
npm install
```

3. Configure Twilio credentials:
   - Sign up for a Twilio account at https://www.twilio.com/
   - Get your Account SID and Auth Token from the Twilio Console
   - Get a Twilio phone number
   - Update the following variables in `src/config.ts`:
     ```typescript
     TWILIO_ACCOUNT_SID: 'your_account_sid',
     TWILIO_AUTH_TOKEN: 'your_auth_token',
     TWILIO_PHONE_NUMBER: 'your_twilio_phone_number',
     ```

4. Configure personal information:
   - Update the following variables in `src/config.ts`:
     ```typescript
     FULL_NAME: 'Your Name',
     EMAIL: 'your.email@example.com',
     PARTY_SIZE: '1',
     PHONE_NUMBER: 'your_phone_number',
     ```

### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/yavuztopsever/termin_bot.git
cd termin_bot
```

2. Configure Twilio credentials and personal information in `src/config.ts` as described above.

3. Build and run the Docker container:
```bash
docker-compose up -d
```

## Usage

### Running Locally

1. Validate API endpoints (recommended before first run):
```bash
./validate-api.sh
```
This will:
   - Launch a browser in visible mode
   - Navigate to the appointment booking page
   - Test API endpoints and capture requests/responses
   - Save screenshots and network logs to the debug directory
   - Help verify that your configuration is correct

2. Start the bot:
```bash
npm start
```

3. The bot will:
   - Run dual approaches simultaneously (browser-based and direct API)
   - Use randomized check intervals to avoid detection
   - Check more aggressively during peak hours
   - Rotate user agents and browser fingerprints
   - Send notifications when appointments are found
   - Automatically attempt to book available slots
   - Send SMS updates about booking status

4. Debug mode:
   - Set `DEBUG_MODE = true` in src/index.ts to enable debug features
   - This will save screenshots, HTML, and network logs to the debug directory
   - The browser will run in visible mode for easier debugging

5. To stop the bot:
   - Press Ctrl+C in the terminal
   - The bot will send a final SMS notification before shutting down

### Running with Docker

1. Use the provided script to build and run the bot:
```bash
./run-docker.sh
```

This script will:
- Build the Docker image with all dependencies
- Start the container in detached mode
- Set up volume mounts for logs and debug information

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the bot:
```bash
docker-compose down
```

4. Health check:
The container includes a health check endpoint that Docker uses to monitor the application's status. You can manually check it with:
```bash
curl http://localhost:3000/health
```

## Troubleshooting

If you encounter browser connection issues:
- Make sure you have enough system resources (memory, CPU)
- Check that you don't have firewall or antivirus software blocking the connection
- Try increasing the MAX_BROWSER_RETRIES value in src/index.ts
- Use Docker to run the application, which provides a more consistent environment

## Project Structure

```
src/
├── config.ts                    # Configuration settings
├── index.ts                     # Main entry point
├── validateApi.ts               # API validation tool
├── services/
│   ├── appointmentService.ts    # Appointment checking and booking
│   ├── apiService.ts            # Browser-based API client
│   ├── coordinationService.ts   # Coordinates both approaches
│   ├── directApiService.ts      # Direct API client
│   ├── loggingService.ts        # Structured logging
│   └── notificationService.ts   # SMS and desktop notifications
├── utils/
│   ├── browserUtils.ts          # Browser fingerprinting protection
│   ├── debugUtils.ts            # Debugging and monitoring tools
│   ├── processUtils.ts          # Process handling utilities
│   ├── retryUtils.ts            # Retry logic with exponential backoff
│   └── timeUtils.ts             # Time formatting utilities
└── __tests__/
    └── booking.test.ts          # Tests for appointment booking
```

## API Endpoints Used

- Available Days: `https://www48.muenchen.de/buergeransicht/api/backend/available-days`
- Available Appointments: `https://www48.muenchen.de/buergeransicht/api/backend/available-appointments`
- Book Appointment: `https://www48.muenchen.de/buergeransicht/api/backend/book-appointment`

## Configuration

You can modify the following settings in `src/config.ts`:

### Basic Settings
- `URL`: The appointment booking page URL
- `FULL_NAME`: Your full name for the appointment
- `EMAIL`: Your email address
- `PARTY_SIZE`: Number of people for the appointment
- `PHONE_NUMBER`: Your phone number for SMS notifications

### Twilio Settings
- `TWILIO_ACCOUNT_SID`: Your Twilio account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

### API Settings
- `API_BASE_URL`: Base URL for the API endpoints
- `OFFICE_ID`: Target office ID
- `SERVICE_ID`: Target service ID
- `SERVICE_COUNT`: Number of services to book

### Timing Settings
- `CHECK_INTERVAL`: Default check interval (5 seconds)
- `BROWSER_CHECK_INTERVAL`: Browser-based approach check interval (8 seconds)
- `API_CHECK_INTERVAL`: Direct API approach check interval (5 seconds)
- `MIN_CHECK_INTERVAL`: Minimum interval during aggressive mode (3 seconds)
- `AGGRESSIVE_MODE_HOURS`: Hours when slots typically appear (more frequent checks)
- `JITTER_FACTOR`: Randomization factor to avoid detection (0.3 = ±30%)

### Retry Settings
- `MAX_RETRIES`: Maximum number of retries for failed requests
- `INITIAL_BACKOFF_MS`: Initial backoff delay for retries
- `MAX_BACKOFF_MS`: Maximum backoff delay for retries

### Location Settings
- `LOCATIONS`: Array of office locations to check in parallel

## Error Handling

The bot includes comprehensive error handling:
- SMS notifications for all errors
- Automatic retries on failure
- Detailed console logging
- Graceful shutdown with notifications

## Testing

Run the tests with:
```bash
npm test
```

The tests use Jest and mock the Puppeteer, Twilio, and notification services to verify the appointment booking functionality.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational purposes only. Please ensure you comply with the website's terms of service and usage policies when using this bot.
