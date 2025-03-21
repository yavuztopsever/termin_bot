# Munich Termin Automator - User Guide

## 1. Introduction

The Munich Termin Automator (MTA) is a Telegram bot that helps you automatically find and book appointments at Munich's public service offices (Bürgerservice). This guide will help you get started and make the most of the bot's features.

## 2. Getting Started

### 2.1 Prerequisites
- Telegram account
- Internet connection
- Valid email address
- Personal details for booking
- Browser with JavaScript enabled (for captcha verification)

### 2.2 Initial Setup
1. Open Telegram
2. Search for `@MunichTerminBot`
3. Start the bot by clicking "Start" or typing `/start`
4. Follow the initial setup instructions
5. Complete the captcha verification when prompted

## 3. Basic Commands

### 3.1 Essential Commands
```
/start      - Start the bot and show welcome message
/help       - Show available commands and help
/settings   - Configure your preferences
/subscribe  - Subscribe to appointment notifications
/check      - Check current appointment availability
/status     - Show your active subscriptions
/cancel     - Cancel current operation
/verify     - Verify captcha status
```

### 3.2 Advanced Commands
```
/locations  - List available service locations
/services   - List available services
/history    - View your appointment history
/notify     - Configure notification preferences
/feedback   - Send feedback about the bot
/rate       - View current rate limits
```

## 4. Subscribing to Appointments

### 4.1 Basic Subscription
1. Type `/subscribe`
2. Select the desired service
3. Choose preferred location(s)
4. Set date/time preferences
5. Complete captcha verification if prompted
6. Confirm subscription

Example interaction:
```
You: /subscribe
Bot: Please select a service:
[Residence Permit]
[Passport Application]
[ID Card]
[Vehicle Registration]

You: *select Residence Permit*
Bot: Please select location(s):
[KVR]
[Bürgerbüro Pasing]
...

Bot: Please complete the captcha verification:
[Verify Captcha]

You: *complete verification*
Bot: Subscription confirmed! You will receive notifications when appointments become available.
```

### 4.2 Advanced Subscription Options
- Multiple time slots
- Date range preferences
- Location priorities
- Notification preferences
- Rate limit monitoring

## 5. Managing Subscriptions

### 5.1 Viewing Subscriptions
```
/status
```
Shows:
- Active subscriptions
- Service details
- Location preferences
- Next check time
- Current rate limit status
- Captcha verification status

### 5.2 Modifying Subscriptions
1. Use `/status` to view subscriptions
2. Select subscription to modify
3. Choose modification option:
   - Change service
   - Update locations
   - Adjust time preferences
   - Update notifications
   - Refresh captcha verification

### 5.3 Canceling Subscriptions
1. Use `/status` to view subscriptions
2. Select subscription to cancel
3. Confirm cancellation

## 6. Notifications

### 6.1 Notification Types
- Appointment found
- Booking confirmation
- Booking reminder
- Service updates
- Error notifications
- Rate limit warnings
- Captcha verification reminders

### 6.2 Configuring Notifications
1. Use `/notify` command
2. Select notification preferences:
   - Instant notifications
   - Daily summaries
   - Silent mode
   - Custom quiet hours
   - Rate limit alerts
   - Captcha reminders

## 7. Booking Process

### 7.1 Automatic Booking
When an appointment is found:
1. Bot sends notification
2. Verifies captcha status
3. Checks rate limits
4. Automatically attempts booking
5. Sends confirmation if successful
6. Provides booking details

### 7.2 Manual Booking
1. Receive availability notification
2. Complete captcha verification if required
3. Click "Book Now" button
4. Confirm booking details
5. Receive booking confirmation

### 7.3 Booking Details
- Appointment date and time
- Location details
- Service information
- Confirmation number
- Required documents
- Rate limit status
- Captcha verification status

## 8. Preferences & Settings

### 8.1 User Settings
```
/settings
```
Configure:
- Language preference
- Time zone
- Notification preferences
- Default location
- Auto-booking preferences
- Captcha verification preferences
- Rate limit monitoring

### 8.2 Time Preferences
- Preferred days
- Time slots
- Blackout dates
- Notice period
- Rate limit windows

## 9. Troubleshooting

### 9.1 Common Issues

#### Bot Not Responding
1. Check internet connection
2. Restart Telegram
3. Type `/start` again
4. Verify captcha status
5. Check rate limits
6. Contact support if issue persists

#### Booking Failures
Common reasons:
- Slot already taken
- Service temporarily unavailable
- Invalid information
- System maintenance
- Captcha verification failed
- Rate limit exceeded
- Bot detection triggered

### 9.2 Error Messages
Example error messages and solutions:
```
Error: "Service unavailable"
Solution: Try again in a few minutes

Error: "Invalid email format"
Solution: Check and update email in settings

Error: "Booking conflict"
Solution: Choose different time slot

Error: "Captcha verification required"
Solution: Complete the captcha verification

Error: "Rate limit exceeded"
Solution: Wait a few minutes before trying again

Error: "Bot-like behavior detected"
Solution: Reduce request frequency and try again
```

## 10. Best Practices

### 10.1 Optimal Usage
- Set realistic time preferences
- Keep contact information updated
- Respond promptly to notifications
- Check status regularly
- Monitor rate limits
- Keep captcha verification current
- Avoid rapid repeated requests

### 10.2 Recommendations
- Enable instant notifications
- Set wider time ranges
- Include multiple locations
- Keep documents ready
- Monitor rate limit status
- Complete captcha verification promptly
- Use natural request patterns

## 11. Privacy & Security

### 11.1 Data Usage
The bot collects:
- Telegram user ID
- Email address
- Booking preferences
- Appointment history
- Captcha verification status
- Rate limit data
- Request patterns

### 11.2 Data Protection
- Encrypted storage
- Secure transmission
- Regular data cleanup
- No sharing with third parties
- Secure captcha handling
- Rate limit data protection
- Pattern analysis privacy

## 12. Support

### 12.1 Getting Help
- Use `/help` command
- Check FAQ section
- Contact support
- Submit bug reports
- Report rate limit issues
- Report captcha problems

### 12.2 Feedback
- Use `/feedback` command
- Rate your experience
- Suggest improvements
- Report issues
- Share rate limit experiences
- Provide captcha feedback

## 13. FAQ

### 13.1 General Questions

Q: How often does the bot check for appointments?
A: Every 15 minutes by default, subject to rate limits.

Q: Can I book multiple appointments?
A: Yes, but only one per service type.

Q: What happens if I miss a notification?
A: The bot will retry based on your settings.

Q: Why do I need to verify captcha?
A: To ensure fair usage and prevent automated abuse.

Q: What are rate limits?
A: Limits on request frequency to ensure system stability.

### 13.2 Technical Questions

Q: Does the bot work 24/7?
A: Yes, except during maintenance.

Q: What happens if the booking fails?
A: The bot will notify you and try again.

Q: How does the bot detect automated behavior?
A: Through pattern analysis of request timing and frequency.

Q: What happens if I exceed rate limits?
A: You'll receive a notification and need to wait before trying again.

Q: How is my data protected during captcha verification?
A: All captcha data is encrypted and securely transmitted.

## 14. Updates & Changes

### 14.1 Version History
- v2.0: Current version
- v1.5: Added multi-location support
- v1.0: Initial release

### 14.2 Upcoming Features
- Additional languages
- More service types
- Enhanced booking options
- Mobile app integration

## 15. Terms of Use

### 15.1 Usage Guidelines
- Fair usage policy
- Rate limiting
- Service availability
- User responsibilities

### 15.2 Limitations
- Maximum active subscriptions
- Booking restrictions
- Time constraints
- Service limitations 