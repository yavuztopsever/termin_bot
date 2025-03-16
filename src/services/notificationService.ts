import notifier from 'node-notifier';
import twilio from 'twilio';
import { config } from '../config';
import { logger } from './loggingService';

// Initialize Twilio client with lazy loading to handle authentication errors
let twilioClient: twilio.Twilio | null = null;

/**
 * Get or initialize the Twilio client
 */
function getTwilioClient(): twilio.Twilio {
  if (!twilioClient) {
    try {
      // Check if Twilio credentials are provided
      if (!config.TWILIO_ACCOUNT_SID || !config.TWILIO_AUTH_TOKEN) {
        logger.warn('Twilio credentials not provided. SMS notifications will be disabled.');
        return null as any;
      }
      
      twilioClient = twilio(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN);
    } catch (error) {
      logger.error(`Failed to initialize Twilio client: ${error instanceof Error ? error.message : String(error)}`);
      return null as any;
    }
  }
  
  return twilioClient;
}

/**
 * Sends an SMS notification
 * @param message Message to send
 * @returns Promise that resolves when the SMS is sent
 */
export async function sendSMS(message: string): Promise<boolean> {
  try {
    const client = getTwilioClient();
    
    // If client is null, log a message and return
    if (!client) {
      logger.warn(`SMS not sent (Twilio disabled): ${message}`);
      return false;
    }
    
    // Check if phone numbers are provided
    if (!config.TWILIO_PHONE_NUMBER || !config.PHONE_NUMBER) {
      logger.warn('Phone numbers not provided. SMS notification skipped.');
      return false;
    }
    
    // Send the SMS
    const messageResponse = await client.messages.create({
      body: message,
      from: config.TWILIO_PHONE_NUMBER,
      to: config.PHONE_NUMBER
    });
    
    logger.info(`SMS sent successfully (SID: ${messageResponse.sid}): ${message}`);
    return true;
  } catch (error) {
    // Log the error with detailed information
    if (error instanceof Error) {
      logger.error(`Failed to send SMS: ${error.message}`);
      if ('code' in error) {
        logger.error(`Twilio error code: ${(error as any).code}`);
      }
      if ('status' in error) {
        logger.error(`HTTP status: ${(error as any).status}`);
      }
      if (error.stack) {
        logger.error(`Stack trace: ${error.stack}`);
      }
    } else {
      logger.error(`Failed to send SMS: ${String(error)}`);
    }
    
    return false;
  }
}

/**
 * Sends both desktop and SMS notifications
 * @param title Title for desktop notification
 * @param message Message content
 */
export async function sendNotifications(title: string, message: string): Promise<void> {
  try {
    // Send desktop notification
    notifier.notify({
      title,
      message,
      sound: true,
      wait: true
    });
    
    logger.info(`Desktop notification sent: ${title} - ${message}`);
  } catch (error) {
    logger.error(`Failed to send desktop notification: ${error instanceof Error ? error.message : String(error)}`);
  }

  // Send SMS notification
  await sendSMS(message);
}
