import { Browser } from 'puppeteer';
import { logger } from '../services/loggingService';

/**
 * Sets up a handler for process termination
 * @param browser Puppeteer browser instance
 * @param intervals Array of interval IDs to clear on termination
 */
export function setupTerminationHandler(
  browser: Browser, 
  ...intervals: NodeJS.Timeout[]
): void {
  process.on('SIGINT', async () => {
    logger.info('Received termination signal. Shutting down gracefully...');
    
    // Clear all intervals
    intervals.forEach(interval => clearInterval(interval));
    
    // Close browser and exit
    try {
      logger.info('Closing browser...');
      await browser.close();
      logger.info('Browser closed successfully');
    } catch (error) {
      logger.error('Error closing browser:', error as Error);
    }
    
    logger.info('Appointment checker terminated');
    process.exit(0);
  });
}
