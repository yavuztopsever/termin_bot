import { Page } from 'puppeteer';
import { config } from '../config';
import { sendSMS, sendNotifications } from './notificationService';
import { ApiClient, ApiError, ConnectionError, ValidationError, AvailableDaysResponse } from './apiService';
import { logger } from './loggingService';

/**
 * Checks for available appointments and attempts to book one if found
 * @param page Puppeteer page instance
 * @returns Promise that resolves to true if an appointment was booked, false otherwise
 */
export async function checkAppointments(page: Page): Promise<boolean> {
  const apiClient = new ApiClient(page);
  
  try {
    // First, check API health
    logger.info('Checking API health...');
    const isApiHealthy = await apiClient.checkApiHealth();
    if (!isApiHealthy) {
      logger.error('API health check failed. Skipping this check cycle.');
      await sendSMS('API health check failed. The appointment system may be down.');
      return false;
    }
    
    // Calculate date range (6 months from today)
    const startDate = new Date().toISOString().split('T')[0];
    const endDate = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    logger.info(`Checking for appointments at ${new Date().toLocaleTimeString()}...`);

    // Get available days
    const availableDaysResponse = await apiClient.getAvailableDays(startDate, endDate);
    
    // Convert to array of dates (empty if error response)
    const availableDays: string[] = Array.isArray(availableDaysResponse) 
      ? availableDaysResponse 
      : [];

    if (availableDays.length > 0) {
      // Get the first available date
      const firstAvailableDate = availableDays[0];
      logger.info(`Found available date: ${firstAvailableDate}`);

      // Get available appointments for that date
      const availableAppointments = await apiClient.getAvailableAppointments(firstAvailableDate);

      if (availableAppointments.length > 0) {
        // Get the first available appointment
        const firstAppointment = availableAppointments[0];
        logger.info(`Found available appointment at: ${firstAppointment.time}`);

        // Send SMS about available appointment
        await sendSMS(`Found available appointment on ${firstAvailableDate} at ${firstAppointment.time}`);

        // Try to book the appointment
        const bookingResponse = await apiClient.bookAppointment(firstAvailableDate, firstAppointment.time);

        if (bookingResponse.success) {
          // Send notifications about successful booking
          logger.info(`Successfully booked appointment for ${firstAvailableDate} at ${firstAppointment.time}`);
          await sendNotifications(
            'Appointment Booked!', 
            `Successfully booked appointment for ${firstAvailableDate} at ${firstAppointment.time}`
          );
          return true;
        } else {
          // Handle booking failure
          const errorMessage = bookingResponse.error || bookingResponse.message || 'Unknown booking error';
          logger.error(`Booking failed: ${errorMessage}`);
          await sendSMS(`Booking attempt failed: ${errorMessage}`);
        }
      }
    } else {
      // Handle case where no available days were found
      if (!Array.isArray(availableDaysResponse) && 'errorCode' in availableDaysResponse) {
        logger.info(`No appointments available: ${availableDaysResponse.errorMessage}`);
      } else {
        logger.info('No appointments available');
      }
    }

    return false;
  } catch (error) {
    // Enhanced error handling
    if (error instanceof ApiError) {
      logger.error(`API Error (${error.endpoint}): ${error.message}`, error);
      await sendSMS(`API Error: ${error.message}`);
    } else if (error instanceof ConnectionError) {
      logger.error(`Connection Error (${error.endpoint}): ${error.message}`, error);
      await sendSMS(`Connection Error: ${error.message}`);
    } else if (error instanceof ValidationError) {
      logger.error(`Validation Error (${error.endpoint}): ${error.message}`, error);
      await sendSMS(`Validation Error: The appointment system may have changed. Please check the application.`);
    } else if (error instanceof Error) {
      logger.error('Error checking appointments:', error);
      await sendSMS(`Error checking appointments: ${error.message}`);
    } else {
      logger.error('Unknown error checking appointments:', error as Error);
      await sendSMS(`Unknown error checking appointments`);
    }
    return false;
  }
}
