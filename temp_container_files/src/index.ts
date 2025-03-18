/// <reference lib="dom" />
import puppeteer, { Browser } from 'puppeteer';
import { config } from './config';
import { setupTerminationHandler } from './utils/processUtils';
import { sendSMS } from './services/notificationService';
import { logger } from './services/loggingService';
import { formatTimeRemaining } from './utils/timeUtils';
import { startBrowserApproach, startDirectApiApproach } from './services/coordinationService';
import { 
  initializeDebugDirs, 
  takeScreenshot, 
  savePageHtml, 
  monitorNetworkRequests,
  debugConfig
} from './utils/debugUtils';
import { applyUserAgentProfile } from './utils/browserUtils';
import { startHealthCheckServer, updateHealthStatus } from './healthCheck';

// Maximum number of browser launch retries
const MAX_BROWSER_RETRIES = 3;

// Debug mode flag (set to false in production)
const DEBUG_MODE = true;

// Flag to track if we've already sent a startup notification
let startupNotificationSent = false;

/**
 * Main function to run the appointment checker
 */
async function runAppointmentChecker() {
  let browser: Browser | null = null;
  let retryCount = 0;
  
  logger.info('Starting appointment checker with dual approach...');
  
  // Start health check server for Docker
  startHealthCheckServer();
  
  // Initialize debug directories if in debug mode
  if (DEBUG_MODE) {
    debugConfig.enabled = true;
    initializeDebugDirs();
    logger.info('Debug mode enabled');
  }
  
  while (retryCount < MAX_BROWSER_RETRIES) {
    try {
      // Launch browser with Docker-compatible configuration
      logger.info('Launching browser...');
      browser = await puppeteer.launch({ 
        headless: true, // Always use headless mode for reliability
        defaultViewport: null,
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--disable-gpu',
          '--window-size=1280,720',
          '--disable-extensions',
          '--disable-features=site-per-process',
          '--disable-web-security'
        ],
        ignoreHTTPSErrors: true,
        timeout: 60000 // Increase timeout to 60 seconds
      });
      
      // Set up browser page
      const page = await browser.newPage();
      page.setDefaultNavigationTimeout(60000); // 60 seconds
      
      // Apply user agent profile to avoid detection
      await applyUserAgentProfile(page);
      
      // Set up network monitoring in debug mode
      if (DEBUG_MODE) {
        await monitorNetworkRequests(page);
      }
      
      // Navigate to the main URL once
      logger.info(`Navigating to ${config.URL}...`);
      await page.goto(config.URL, { waitUntil: 'networkidle2' });
      
      // Take screenshot and save HTML in debug mode
      if (DEBUG_MODE) {
        await takeScreenshot(page, 'initial_page_load');
        await savePageHtml(page, 'initial_page_load');
      }
      
      logger.info('Browser initialized successfully');
      
      // Update health status for browser
      updateHealthStatus('browserInitialized', true);

      // Send startup notification (only once)
      if (!startupNotificationSent) {
        const smsResult = await sendSMS('Appointment checker started with dual approach. Will notify when an appointment is found.');
        if (!smsResult) {
          logger.warn('SMS notification disabled or failed. Continuing without SMS notifications.');
        }
        startupNotificationSent = true;
      }
      
      // Handle process termination
      setupTerminationHandler(browser);
      
      // Start both approaches
      logger.info('Starting browser-based approach...');
      await startBrowserApproach(browser, page);
      
      logger.info('Starting direct API approach...');
      await startDirectApiApproach();
      
      // Keep the process running
      logger.info('Both approaches running. Waiting for available appointments...');
      
      // Break out of retry loop since we've successfully started
      break;
    } catch (error) {
      retryCount++;
      logger.error(`Browser launch attempt ${retryCount} failed:`, error as Error);
      
      // Update health status to indicate browser initialization failed
      updateHealthStatus('browserInitialized', false);
      
      if (browser) {
        try {
          await browser.close();
        } catch (closeError) {
          logger.error('Error closing browser:', closeError as Error);
        }
      }
      
      if (retryCount >= MAX_BROWSER_RETRIES) {
        logger.error('Maximum browser launch retries exceeded. Exiting.');
        await sendSMS(`Error in appointment checker: Maximum browser launch retries exceeded.`);
        process.exit(1);
      }
      
      // Wait before retrying with a random delay
      const retryDelay = 5000 + Math.floor(Math.random() * 2000);
      logger.info(`Retrying in ${formatTimeRemaining(retryDelay)}...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
}

// Only run the main function if this file is being run directly
if (require.main === module) {
  runAppointmentChecker().catch(async (error) => {
    logger.error('Unhandled error in appointment checker:', error as Error);
    
    // Update health status to indicate both components are unhealthy
    updateHealthStatus('browserInitialized', false);
    updateHealthStatus('apiConnected', false);
    
    if (error instanceof Error) {
      logger.error('Error details:', error);
      await sendSMS(`Critical error in appointment checker: ${error.message}`);
    }
    
    process.exit(1);
  });
}
