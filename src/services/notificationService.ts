import notifier from 'node-notifier';
import twilio from 'twilio';
import { config } from '../config';
import { logger } from './loggingService';
import { AppointmentStatus, StatusChangeEvent, statusService } from './statusService';

// Initialize Twilio client with lazy loading to handle authentication errors
let twilioClient: twilio.Twilio | null = null;

/**
 * Get or initialize the Twilio client
 */
function getTwilioClient(): twilio.Twilio {
  if (!twilioClient) {
    try {
      // Check if Twilio credentials are provided
      if (!config.TWILIO_API_KEY_SID || !config.TWILIO_API_KEY_SECRET || !config.TWILIO_ACCOUNT_SID) {
        logger.warn('Twilio credentials not provided. SMS notifications will be disabled.');
        return null as any;
      }
      
      // Initialize with API Key SID format
      twilioClient = new twilio.Twilio(
        config.TWILIO_API_KEY_SID,
        config.TWILIO_API_KEY_SECRET,
        { accountSid: config.TWILIO_ACCOUNT_SID }
      );
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
    
    // Check if phone number is provided
    if (!config.PHONE_NUMBER) {
      logger.warn('Phone number not provided. SMS notification skipped.');
      return false;
    }
    
    // Send the SMS using Messaging Service
    const messageResponse = await client.messages.create({
      body: message,
      messagingServiceSid: config.TWILIO_MESSAGING_SERVICE_SID,
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
 * Get notification message for status change
 */
function getStatusChangeMessage(event: StatusChangeEvent): string | null {
  const { newStatus, details } = event;

  switch (newStatus) {
    case AppointmentStatus.API_ERROR:
      return `System Error: ${details?.message || 'The appointment system is experiencing issues'}`;
    
    case AppointmentStatus.APPOINTMENT_FOUND:
      return `Found available appointment on ${details?.date} at ${details?.time}`;
    
    case AppointmentStatus.BOOKING_IN_PROGRESS:
      return `Attempting to book appointment for ${details?.date} at ${details?.time}`;
    
    case AppointmentStatus.BOOKING_SUCCESSFUL:
      return `Successfully booked appointment for ${details?.date} at ${details?.time}. Check your email for confirmation.`;
    
    case AppointmentStatus.BOOKING_FAILED:
      return `Failed to book appointment: ${details?.error || 'Unknown error'}`;
    
    default:
      return null;
  }
}

// Initialize status change listener
statusService.onStatusChange(async (event: StatusChangeEvent) => {
  const message = getStatusChangeMessage(event);
  if (message) {
    // Send desktop notification for all status changes
    try {
      notifier.notify({
        title: event.newStatus,
        message,
        sound: true,
        wait: true
      });
      logger.info(`Desktop notification sent: ${event.newStatus} - ${message}`);
    } catch (error) {
      logger.error(`Failed to send desktop notification: ${error instanceof Error ? error.message : String(error)}`);
    }

    // Send SMS only for important status changes
    const importantStatuses = [
      AppointmentStatus.APPOINTMENT_FOUND,
      AppointmentStatus.BOOKING_SUCCESSFUL,
      AppointmentStatus.BOOKING_FAILED,
      AppointmentStatus.API_ERROR
    ];

    if (importantStatuses.includes(event.newStatus)) {
      await sendSMS(message);
    }
  }
});
