import notifier from 'node-notifier';
import twilio from 'twilio';
import { config } from '../config';

// Initialize Twilio client
const twilioClient = twilio(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN);

/**
 * Sends an SMS notification
 * @param message Message to send
 * @returns Promise that resolves when the SMS is sent
 */
export async function sendSMS(message: string): Promise<void> {
  try {
    const messageResponse = await twilioClient.messages.create({
      body: message,
      from: config.TWILIO_PHONE_NUMBER,
      to: config.PHONE_NUMBER
    });
    console.log('SMS sent successfully:', messageResponse.sid);
  } catch (error) {
    console.error('Failed to send SMS:', error);
  }
}

/**
 * Sends both desktop and SMS notifications
 * @param title Title for desktop notification
 * @param message Message content
 */
export async function sendNotifications(title: string, message: string): Promise<void> {
  // Send desktop notification
  notifier.notify({
    title,
    message,
    sound: true,
    wait: true
  });

  // Send SMS notification
  await sendSMS(message);
} 