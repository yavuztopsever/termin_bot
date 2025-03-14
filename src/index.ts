/// <reference lib="dom" />
import puppeteer, { Browser } from 'puppeteer';
import { checkAppointments } from './services/appointmentService';
import { config } from './config';
import { setupTerminationHandler } from './utils/processUtils';
import { sendSMS } from './services/notificationService';

// Maximum number of browser launch retries
const MAX_BROWSER_RETRIES = 3;

/**
 * Main function to run the appointment checker
 */
async function runAppointmentChecker() {
  let browser: Browser | null = null;
  let retryCount = 0;
  
  while (retryCount < MAX_BROWSER_RETRIES) {
    try {
      // Launch browser with Docker-compatible configuration
      browser = await puppeteer.launch({ 
        headless: true,
        defaultViewport: null,
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--disable-gpu',
          '--window-size=1280,720'
        ],
        ignoreHTTPSErrors: true,
        timeout: 30000 // Increase timeout to 30 seconds
      });
      
      const page = await browser.newPage();
      
      // Set a longer navigation timeout
      page.setDefaultNavigationTimeout(60000); // 60 seconds
      
      // Navigate to the main URL once
      await page.goto(config.URL, { waitUntil: 'networkidle2' });
      
      console.log('Starting appointment checker...');
      console.log(`Will check every ${config.CHECK_INTERVAL / 1000} seconds continuously`);

      // Send startup notification
      await sendSMS('Appointment checker started. Will notify when an appointment is found.');

      // Initial check
      let success = await checkAppointments(page);
      let checkCount = 1;

      // If initial check didn't succeed, start periodic checking
      if (!success) {
        let nextCheckTime = Date.now() + config.CHECK_INTERVAL;
        
        // Display countdown timer
        const countdownInterval = setInterval(() => {
          const now = Date.now();
          const timeRemaining = nextCheckTime - now;
          if (timeRemaining > 0) {
            process.stdout.write(`\rWaiting for next check (${checkCount}): ${Math.ceil(timeRemaining / 1000)}s`);
          }
        }, 1000);

        // Periodic check interval
        const checkInterval = setInterval(async () => {
          try {
            success = await checkAppointments(page);
            checkCount++;
            if (success) {
              clearInterval(checkInterval);
              clearInterval(countdownInterval);
              await browser!.close();
              process.exit(0);
            }
            nextCheckTime = Date.now() + config.CHECK_INTERVAL;
          } catch (error) {
            console.error('Error during check:', error);
            // Continue checking despite errors
          }
        }, config.CHECK_INTERVAL);

        // Handle process termination
        setupTerminationHandler(browser, checkInterval, countdownInterval);
        
        // Break out of retry loop since we've successfully started
        break;
      } else {
        await browser.close();
        process.exit(0);
      }
    } catch (error) {
      retryCount++;
      console.error(`Browser launch attempt ${retryCount} failed:`, error);
      
      if (browser) {
        try {
          await browser.close();
        } catch (closeError) {
          console.error('Error closing browser:', closeError);
        }
      }
      
      if (retryCount >= MAX_BROWSER_RETRIES) {
        console.error('Maximum browser launch retries exceeded. Exiting.');
        await sendSMS(`Error in appointment checker: Maximum browser launch retries exceeded.`);
        process.exit(1);
      }
      
      // Wait before retrying
      console.log(`Retrying in 5 seconds...`);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// Only run the main function if this file is being run directly
if (require.main === module) {
  runAppointmentChecker().catch(async (error) => {
    console.error('Unhandled error in appointment checker:', error);
    
    if (error instanceof Error) {
      console.error('Error details:', error.message);
      console.error('Stack trace:', error.stack);
      await sendSMS(`Critical error in appointment checker: ${error.message}`);
    }
    
    process.exit(1);
  });
}