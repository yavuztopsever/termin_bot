# München Termin Bot

An automated appointment booking bot for München city services using Puppeteer and Twilio for notifications.

## Features

- Automated appointment checking between 6 AM and 8 AM
- 8-second interval checks during the time window
- Desktop and SMS notifications via Twilio
- Automatic booking when slots become available
- Error handling and status notifications
- Time window restrictions to comply with system usage policies

## Prerequisites

- Node.js (v14 or higher)
- npm (Node Package Manager)
- A Twilio account for SMS notifications

## Installation

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
   - Update the following variables in `src/index.ts`:
     ```typescript
     const TWILIO_ACCOUNT_SID = 'your_account_sid';
     const TWILIO_AUTH_TOKEN = 'your_auth_token';
     const TWILIO_PHONE_NUMBER = 'your_twilio_phone_number';
     ```

4. Configure personal information:
   - Update the following variables in `src/index.ts`:
     ```typescript
     const FULL_NAME = 'Your Name';
     const EMAIL = 'your.email@example.com';
     const PARTY_SIZE = '1';
     const PHONE_NUMBER = 'your_phone_number';
     ```

## Usage

1. Start the bot:
```bash
npm start
```

2. The bot will:
   - Run between 6 AM and 8 AM
   - Check for appointments every 8 seconds
   - Send notifications when appointments are found
   - Automatically attempt to book available slots
   - Send SMS updates about booking status

3. To stop the bot:
   - Press Ctrl+C in the terminal
   - The bot will send a final SMS notification before shutting down

## API Endpoints Used

- Available Days: `https://www48.muenchen.de/buergeransicht/api/backend/available-days`
- Available Appointments: `https://www48.muenchen.de/buergeransicht/api/backend/available-appointments`
- Book Appointment: `https://www48.muenchen.de/buergeransicht/api/backend/book-appointment`

## Configuration

You can modify the following settings in `src/index.ts`:

- `CHECK_INTERVAL`: Time between checks (default: 8 seconds)
- `START_HOUR`: Start time for checks (default: 6)
- `END_HOUR`: End time for checks (default: 8)
- `OFFICE_ID`: Target office ID
- `SERVICE_ID`: Target service ID

## Error Handling

The bot includes comprehensive error handling:
- SMS notifications for all errors
- Automatic retries on failure
- Detailed console logging
- Graceful shutdown with notifications

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