import { Page } from 'puppeteer';
import { config } from '../config';
import { sendSMS } from './notificationService';
import { ApiClient, ApiError, ConnectionError, ValidationError, AvailableDaysResponse } from './apiService';
import { logger } from './loggingService';
import { statusService, AppointmentStatus } from './statusService';

/**
 * Checks for available appointments and attempts to book one if found
 * @param page Puppeteer page instance
 * @returns Promise that resolves to true if an appointment was booked, false otherwise
 */
export async function checkAppointments(page: Page): Promise<boolean> {
  const apiClient = new ApiClient(page);
  
  try {
    // Update status to checking
    statusService.updateStatus(AppointmentStatus.CHECKING);

    // First, check API health
    logger.info('Checking API health...');
    const isApiHealthy = await apiClient.checkApiHealth();
    if (!isApiHealthy) {
      logger.error('API health check failed. Skipping this check cycle.');
      statusService.updateStatus(AppointmentStatus.API_ERROR, {
        message: 'API health check failed. The appointment system may be down.'
      });
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

        // Update status to appointment found
        statusService.updateStatus(AppointmentStatus.APPOINTMENT_FOUND, {
          date: firstAvailableDate,
          time: firstAppointment.time
        });

        // Update status to booking in progress
        statusService.updateStatus(AppointmentStatus.BOOKING_IN_PROGRESS, {
          date: firstAvailableDate,
          time: firstAppointment.time
        });

        // Try to book the appointment
        const bookingResponse = await apiClient.bookAppointment(firstAvailableDate, firstAppointment.time);

        if (bookingResponse.success) {
          // Update status to booking successful
          statusService.updateStatus(AppointmentStatus.BOOKING_SUCCESSFUL, {
            date: firstAvailableDate,
            time: firstAppointment.time
          });
          return true;
        } else {
          // Handle booking failure
          const errorMessage = bookingResponse.error || bookingResponse.message || 'Unknown booking error';
          logger.error(`Booking failed: ${errorMessage}`);
          statusService.updateStatus(AppointmentStatus.BOOKING_FAILED, {
            date: firstAvailableDate,
            time: firstAppointment.time,
            error: errorMessage
          });
        }
      }
    } else {
      // Handle case where no available days were found
      if (!Array.isArray(availableDaysResponse) && 'errorCode' in availableDaysResponse) {
        logger.info(`No appointments available: ${availableDaysResponse.errorMessage}`);
      } else {
        logger.info('No appointments available');
      }
      statusService.updateStatus(AppointmentStatus.NO_APPOINTMENTS);
    }

    return false;
  } catch (error) {
    // Enhanced error handling
    let errorMessage: string;
    if (error instanceof ApiError) {
      errorMessage = `API Error (${error.endpoint}): ${error.message}`;
      logger.error(errorMessage, error);
    } else if (error instanceof ConnectionError) {
      errorMessage = `Connection Error (${error.endpoint}): ${error.message}`;
      logger.error(errorMessage, error);
    } else if (error instanceof ValidationError) {
      errorMessage = 'The appointment system may have changed. Please check the application.';
      logger.error(`Validation Error (${error.endpoint}): ${error.message}`, error);
    } else if (error instanceof Error) {
      errorMessage = error.message;
      logger.error('Error checking appointments:', error);
    } else {
      errorMessage = 'Unknown error occurred';
      logger.error('Unknown error checking appointments:', error as Error);
    }

    statusService.updateStatus(AppointmentStatus.API_ERROR, {
      message: errorMessage
    });
    return false;
  }
}
