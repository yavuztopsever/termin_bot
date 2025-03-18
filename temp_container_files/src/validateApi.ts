import puppeteer from 'puppeteer';
import { config } from './config';
import { logger } from './services/loggingService';
import { 
  initializeDebugDirs, 
  takeScreenshot, 
  savePageHtml, 
  monitorNetworkRequests,
  validateApiEndpoints
} from './utils/debugUtils';
import { applyUserAgentProfile, getRandomUserAgentProfile } from './utils/browserUtils';

/**
 * Validate API endpoints and requests
 */
async function validateApi() {
  let browser = null;
  
  try {
    // Initialize debug directories
    initializeDebugDirs();
    
    logger.info('Starting API validation...');
    
    // Launch browser in non-headless mode for visual verification
    logger.info('Launching browser...');
    browser = await puppeteer.launch({ 
      headless: false, // Set to false for visual verification
      defaultViewport: null,
      args: [
        '--window-size=1280,720'
      ]
    }).catch(error => {
      logger.error(`Failed to launch browser: ${error instanceof Error ? error.message : JSON.stringify(error)}`);
      throw error;
    });
    
    logger.info('Browser launched successfully');
    
    // Set up browser page
    const page = await browser.newPage();
    
    // Apply random user agent
    await applyUserAgentProfile(page);
    
    // Set up network request monitoring
    await monitorNetworkRequests(page);
    
    // Navigate to the main URL
    logger.info(`Navigating to ${config.URL}...`);
    await page.goto(config.URL, { waitUntil: 'networkidle2' });
    
    // Take a screenshot after initial load
    await takeScreenshot(page, 'initial_page_load');
    
    // Save the HTML after initial load
    await savePageHtml(page, 'initial_page_load');
    
    // Wait for user to see the page
    logger.info('Page loaded. Waiting 5 seconds...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Validate API endpoints
    await validateApiEndpoints(page);
    
    // Test API requests manually
    logger.info('Testing API requests...');
    
    // Calculate date range (6 months from today)
    const startDate = new Date().toISOString().split('T')[0];
    const endDate = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    // Test available days endpoint
    logger.info('Testing available days endpoint...');
    const availableDaysUrl = `${config.AVAILABLE_DAYS_ENDPOINT}?${new URLSearchParams({
      startDate,
      endDate,
      officeId: config.OFFICE_ID,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    })}`;
    
    const availableDaysResponse = await page.evaluate(async (url) => {
      try {
        const response = await fetch(url);
        return {
          ok: response.ok,
          status: response.status,
          data: await response.json()
        };
      } catch (error) {
        return {
          ok: false,
          error: error instanceof Error ? error.message : String(error)
        };
      }
    }, availableDaysUrl);
    
    logger.info(`Available days response: ${JSON.stringify(availableDaysResponse, null, 2)}`);
    
    // Take a screenshot after available days request
    await takeScreenshot(page, 'after_available_days_request');
    
    // If we got available days, test the available appointments endpoint
    if (availableDaysResponse.ok && 
        availableDaysResponse.data && 
        Array.isArray(availableDaysResponse.data) && 
        availableDaysResponse.data.length > 0) {
      
      const firstAvailableDate = availableDaysResponse.data[0];
      logger.info(`Testing available appointments endpoint for date: ${firstAvailableDate}`);
      
      const availableAppointmentsUrl = `${config.AVAILABLE_APPOINTMENTS_ENDPOINT}?${new URLSearchParams({
        date: firstAvailableDate,
        officeId: config.OFFICE_ID,
        serviceId: config.SERVICE_ID,
        serviceCount: config.SERVICE_COUNT
      })}`;
      
      const availableAppointmentsResponse = await page.evaluate(async (url) => {
        try {
          const response = await fetch(url);
          return {
            ok: response.ok,
            status: response.status,
            data: await response.json()
          };
        } catch (error) {
          return {
            ok: false,
            error: error instanceof Error ? error.message : String(error)
          };
        }
      }, availableAppointmentsUrl);
      
      logger.info(`Available appointments response: ${JSON.stringify(availableAppointmentsResponse, null, 2)}`);
      
      // Take a screenshot after available appointments request
      await takeScreenshot(page, 'after_available_appointments_request');
    } else if (availableDaysResponse.ok && 
               availableDaysResponse.data && 
               typeof availableDaysResponse.data === 'object' && 
               'errorCode' in availableDaysResponse.data) {
      
      // Handle the "no appointments" response format
      logger.info(`No appointments available: ${availableDaysResponse.data.errorMessage}`);
    }
    
    // Wait for user to see the results
    logger.info('API validation complete. Waiting 10 seconds before closing...');
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Close the browser
    await browser.close();
    
    logger.info('API validation finished successfully');
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
    logger.error(`Error during API validation: ${errorMessage}`);
    
    if (browser) {
      try {
        await browser.close();
      } catch (closeError) {
        const closeErrorMessage = closeError instanceof Error ? closeError.message : JSON.stringify(closeError);
        logger.error(`Error closing browser: ${closeErrorMessage}`);
      }
    }
    
    process.exit(1);
  }
}

// Run the validation script
validateApi().catch(error => {
  const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
  logger.error(`Unhandled error in API validation: ${errorMessage}`);
  process.exit(1);
});
