import { Browser } from 'puppeteer';

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
    // Clear all intervals
    intervals.forEach(interval => clearInterval(interval));
    
    // Close browser and exit
    await browser.close();
    process.exit(0);
  });
} 