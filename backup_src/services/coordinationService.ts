import { Browser, Page } from 'puppeteer';
import { ApiClient } from './apiService';
import { DirectApiClient } from './directApiService';
import { checkAppointments } from './appointmentService';
import { logger } from './loggingService';
import { config } from '../config';
import { sendSMS } from './notificationService';
import { statusService, AppointmentStatus } from './statusService';
import { applyUserAgentProfile, getRandomUserAgentProfile } from '../utils/browserUtils';

// Track booking status across approaches
let bookingInProgress = false;
let bookingSuccessful = false;

/**
 * Starts the browser-based appointment checking approach
 */
export async function startBrowserApproach(browser: Browser, page: Page): Promise<void> {
  const apiClient = new ApiClient(page);
  let checkCount = 1;
  
  // Apply random user agent to avoid detection
  await applyUserAgentProfile(page);
  
  // Initial check
  try {
    logger.info('Running initial browser check...');
    if (await attemptBooking(async () => checkAppointments(page))) {
      return; // Booking successful
    }
  } catch (error) {
    logger.error('Error during initial browser check:', error instanceof Error ? error : new Error(String(error)));
  }
  
  // Set up periodic checks with adaptive timing
  const runBrowserCheck = async () => {
    if (bookingSuccessful) {
      logger.info('Booking successful, stopping browser checks');
      return;
    }
    
    try {
      logger.info(`Running browser check #${checkCount}...`);
      if (await attemptBooking(async () => checkAppointments(page))) {
        return; // Booking successful
      }
      
      checkCount++;
      
      // Schedule next check with adaptive timing
      const nextInterval = config.getRandomizedCheckInterval(config.BROWSER_CHECK_INTERVAL);
      logger.debug(`Next browser check in ${nextInterval / 1000}s`);
      setTimeout(runBrowserCheck, nextInterval);
    } catch (error) {
      logger.error(`Error during browser check #${checkCount}:`, error instanceof Error ? error : new Error(String(error)));
      
      // Continue checking despite errors
      const nextInterval = config.getRandomizedCheckInterval(config.BROWSER_CHECK_INTERVAL);
      setTimeout(runBrowserCheck, nextInterval);
    }
  };
  
  // Start periodic checks
  const initialInterval = config.getRandomizedCheckInterval(config.BROWSER_CHECK_INTERVAL);
  logger.info(`First browser check in ${initialInterval / 1000}s`);
  setTimeout(runBrowserCheck, initialInterval);
}

/**
 * Starts the direct API appointment checking approach
 */
export async function startDirectApiApproach(): Promise<void> {
  const directApiClient = new DirectApiClient();
  let checkCount = 1;
  
  // Initial health check
  try {
    logger.info('Checking direct API health...');
    const isHealthy = await directApiClient.checkApiHealth();
    if (!isHealthy) {
      logger.error('Direct API health check failed. Will retry later.');
      // Continue with periodic checks anyway
    }
  } catch (error) {
    logger.error('Error checking direct API health:', error instanceof Error ? error : new Error(String(error)));
  }
  
  // Function to check for appointments using direct API
  const checkDirectApi = async (): Promise<boolean> => {
    // Check all configured locations in parallel
    const locationResults = await Promise.all(
      config.LOCATIONS.map(async (location) => {
        try {
          // Calculate date range (6 months from today)
          const startDate = new Date().toISOString().split('T')[0];
          const endDate = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          
          // Get available days
          const availableDays = await directApiClient.getAvailableDays(startDate, endDate, location.id);
          
          if (availableDays.length > 0) {
            // Get the first available date
            const firstAvailableDate = availableDays[0];
            logger.info(`Found available date at ${location.name}: ${firstAvailableDate}`);
            
            // Get available appointments for that date
            const availableAppointments = await directApiClient.getAvailableAppointments(firstAvailableDate, location.id);
            
            if (availableAppointments.length > 0) {
              // Get the first available appointment
              const firstAppointment = availableAppointments[0];
              logger.info(`Found available appointment at ${location.name} on ${firstAvailableDate} at ${firstAppointment.time}`);
              
              // Update status to appointment found
              statusService.updateStatus(AppointmentStatus.APPOINTMENT_FOUND, {
                date: firstAvailableDate,
                time: firstAppointment.time,
                location: location.name
              });
              
              // Update status to booking in progress
              statusService.updateStatus(AppointmentStatus.BOOKING_IN_PROGRESS, {
                date: firstAvailableDate,
                time: firstAppointment.time,
                location: location.name
              });
              
              // Try to book the appointment
              const bookingResponse = await directApiClient.bookAppointment(firstAvailableDate, firstAppointment.time, location.id);
              
              if (bookingResponse.success) {
                // Update status to booking successful
                statusService.updateStatus(AppointmentStatus.BOOKING_SUCCESSFUL, {
                  date: firstAvailableDate,
                  time: firstAppointment.time,
                  location: location.name
                });
                return true;
              } else {
                // Handle booking failure
                const errorMessage = bookingResponse.error || bookingResponse.message || 'Unknown booking error';
                logger.error(`Booking failed at ${location.name}: ${errorMessage}`);
                statusService.updateStatus(AppointmentStatus.BOOKING_FAILED, {
                  date: firstAvailableDate,
                  time: firstAppointment.time,
                  location: location.name,
                  error: errorMessage
                });
              }
            }
          }
          
          return false;
        } catch (error) {
          logger.error(`Error checking location ${location.name}:`, error instanceof Error ? error : new Error(String(error)));
          statusService.updateStatus(AppointmentStatus.API_ERROR, {
            location: location.name,
            message: error instanceof Error ? error.message : String(error)
          });
          return false;
        }
      })
    );
    
    // Return true if any location was successful
    return locationResults.some(result => result);
  };
  
  // Set up periodic checks with adaptive timing
  const runDirectApiCheck = async () => {
    if (bookingSuccessful) {
      logger.info('Booking successful, stopping direct API checks');
      return;
    }
    
    try {
      logger.info(`Running direct API check #${checkCount}...`);
      if (await attemptBooking(checkDirectApi)) {
        return; // Booking successful
      }
      
      checkCount++;
      
      // Schedule next check with adaptive timing
      const nextInterval = config.getRandomizedCheckInterval(config.API_CHECK_INTERVAL);
      logger.debug(`Next direct API check in ${nextInterval / 1000}s`);
      setTimeout(runDirectApiCheck, nextInterval);
    } catch (error) {
      logger.error(`Error during direct API check #${checkCount}:`, error instanceof Error ? error : new Error(String(error)));
      
      // Continue checking despite errors
      const nextInterval = config.getRandomizedCheckInterval(config.API_CHECK_INTERVAL);
      setTimeout(runDirectApiCheck, nextInterval);
    }
  };
  
  // Start periodic checks with a slight delay to offset from browser checks
  const initialInterval = config.getRandomizedCheckInterval(config.API_CHECK_INTERVAL) + 2000;
  logger.info(`First direct API check in ${initialInterval / 1000}s`);
  setTimeout(runDirectApiCheck, initialInterval);
}

/**
 * Helper function to attempt booking with coordination
 */
async function attemptBooking(checkFn: () => Promise<boolean>): Promise<boolean> {
  if (bookingInProgress || bookingSuccessful) {
    return false;
  }
  
  try {
    bookingInProgress = true;
    const success = await checkFn();
    
    if (success) {
      bookingSuccessful = true;
      await sendSMS('Appointment booked successfully! Check your email for confirmation.');
      logger.info('Appointment booked successfully!');
      return true;
    }
  } finally {
    bookingInProgress = false;
  }
  
  return false;
}
