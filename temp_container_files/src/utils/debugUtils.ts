import fs from 'fs';
import path from 'path';
import { Page, Browser, ElementHandle } from 'puppeteer';
import { logger } from '../services/loggingService';

// Debug configuration
export const debugConfig = {
  enabled: true,
  screenshotDir: path.join(process.cwd(), 'debug', 'screenshots'),
  logRequestsAndResponses: true,
  saveHtml: true,
  htmlDir: path.join(process.cwd(), 'debug', 'html'),
  networkLogDir: path.join(process.cwd(), 'debug', 'network')
};

/**
 * Initialize debug directories
 */
export function initializeDebugDirs(): void {
  if (!debugConfig.enabled) return;
  
  // Create debug directories if they don't exist
  const dirs = [
    debugConfig.screenshotDir,
    debugConfig.htmlDir,
    debugConfig.networkLogDir
  ];
  
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
  
  logger.info('Debug directories initialized');
}

/**
 * Take a screenshot of the current page state
 */
export async function takeScreenshot(page: Page, name: string): Promise<string | null> {
  if (!debugConfig.enabled) return null;
  
  try {
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const filename = `${timestamp}_${name}.png`;
    const filepath = path.join(debugConfig.screenshotDir, filename);
    
    await page.screenshot({ path: filepath, fullPage: true });
    logger.info(`Screenshot saved: ${filepath}`);
    
    return filepath;
  } catch (error) {
    logger.error(`Failed to take screenshot: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  }
}

/**
 * Save the current page HTML
 */
export async function savePageHtml(page: Page, name: string): Promise<string | null> {
  if (!debugConfig.enabled || !debugConfig.saveHtml) return null;
  
  try {
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const filename = `${timestamp}_${name}.html`;
    const filepath = path.join(debugConfig.htmlDir, filename);
    
    const html = await page.content();
    fs.writeFileSync(filepath, html);
    
    logger.info(`HTML saved: ${filepath}`);
    return filepath;
  } catch (error) {
    logger.error(`Failed to save HTML: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  }
}

/**
 * Log network request and response
 */
export function logNetworkExchange(
  method: string,
  url: string,
  requestData: any,
  responseData: any,
  statusCode?: number
): void {
  if (!debugConfig.enabled || !debugConfig.logRequestsAndResponses) return;
  
  try {
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const urlObj = new URL(url);
    const pathname = urlObj.pathname.replace(/\//g, '_');
    const filename = `${timestamp}_${method}_${pathname}.json`;
    const filepath = path.join(debugConfig.networkLogDir, filename);
    
    const logData = {
      timestamp: new Date().toISOString(),
      method,
      url,
      requestData,
      responseData,
      statusCode
    };
    
    fs.writeFileSync(filepath, JSON.stringify(logData, null, 2));
    logger.info(`Network exchange logged: ${filepath}`);
  } catch (error) {
    logger.error(`Failed to log network exchange: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Set up network request monitoring for a page
 */
export async function monitorNetworkRequests(page: Page): Promise<void> {
  if (!debugConfig.enabled || !debugConfig.logRequestsAndResponses) return;
  
  try {
    // Monitor network requests
    await page.setRequestInterception(true);
    
    page.on('request', request => {
      try {
        const url = request.url();
        
        // Only log API requests
        if (url.includes('/api/')) {
          logger.debug(`Request: ${request.method()} ${url}`);
          
          // Log request details
          const requestData = {
            method: request.method(),
            url: request.url(),
            headers: request.headers(),
            postData: request.postData()
          };
          
          // Store request data for later correlation with response
          (request as any)._debugData = requestData;
        }
        
        // Continue the request
        request.continue();
      } catch (error) {
        // If there's an error, still continue the request to avoid hanging
        request.continue();
        logger.error(`Error in request handler: ${error instanceof Error ? error.message : JSON.stringify(error)}`);
      }
    });
    
    page.on('response', async response => {
      try {
        const url = response.url();
        
        // Only log API responses
        if (url.includes('/api/')) {
          const request = response.request();
          const requestData = (request as any)._debugData;
          
          if (!requestData) return;
          
          // Get response data
          let responseData;
          try {
            responseData = await response.json();
          } catch (e) {
            responseData = { error: 'Could not parse response as JSON' };
          }
          
          // Log the complete exchange
          logNetworkExchange(
            request.method(),
            url,
            requestData,
            responseData,
            response.status()
          );
          
          logger.debug(`Response: ${response.status()} ${url}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
        logger.error(`Error processing response: ${errorMessage}`);
      }
    });
    
    logger.info('Network request monitoring set up successfully');
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
    logger.error(`Failed to set up network monitoring: ${errorMessage}`);
  }
}

/**
 * Create a validation report for API endpoints
 */
export async function validateApiEndpoints(page: Page): Promise<void> {
  if (!debugConfig.enabled) return;
  
  logger.info('Validating API endpoints...');
  
  // Take a screenshot of the initial page
  await takeScreenshot(page, 'initial_page');
  
  // Save the initial HTML
  await savePageHtml(page, 'initial_page');
  
  // Set up network monitoring
  await monitorNetworkRequests(page);
  
  logger.info('API endpoint validation complete');
}
