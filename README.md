# München Termin Bot

An automated appointment booking bot for München city services using Puppeteer and Twilio for notifications.

## Features

- Continuous appointment checking at regular intervals
- 15-second interval checks
- Desktop and SMS notifications via Twilio
- Automatic booking when slots become available
- Error handling and status notifications
- Runs in headless mode for better stability
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

1. Start the bot:
```bash
npm start
```

2. The bot will:
   - Run continuously in headless mode (no visible browser window)
   - Check for appointments every 15 seconds
   - Send notifications when appointments are found
   - Automatically attempt to book available slots
   - Send SMS updates about booking status

3. To stop the bot:
   - Press Ctrl+C in the terminal
   - The bot will send a final SMS notification before shutting down

### Running with Docker

1. Start the bot as a background service:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker logs -f termin-bot
```

3. Stop the bot:
```bash
docker-compose down
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
├── config.ts                  # Configuration settings
├── index.ts                   # Main entry point
├── services/
│   ├── appointmentService.ts  # Appointment checking and booking
│   └── notificationService.ts # SMS and desktop notifications
├── utils/
│   ├── processUtils.ts        # Process handling utilities
│   └── timeUtils.ts           # Time formatting utilities
└── __tests__/
    └── booking.test.ts        # Tests for appointment booking
```

## API Endpoints Used

- Available Days: `https://www48.muenchen.de/buergeransicht/api/backend/available-days`
- Available Appointments: `https://www48.muenchen.de/buergeransicht/api/backend/available-appointments`
- Book Appointment: `https://www48.muenchen.de/buergeransicht/api/backend/book-appointment`

## Configuration

You can modify the following settings in `src/config.ts`:

- `CHECK_INTERVAL`: Time between checks (default: 15 seconds)
- `OFFICE_ID`: Target office ID
- `SERVICE_ID`: Target service ID

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