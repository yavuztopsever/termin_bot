import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { config } from '../config';
import { logger } from './loggingService';
import { withRetry } from '../utils/retryUtils';
import { getHeadersForUserAgentProfile, UserAgentRotator } from '../utils/browserUtils';
import { updateHealthStatus } from '../healthCheck';

// Response type definitions (same as in apiService.ts)
export type AvailableDaysResponse = string[] | {
  errorCode: string;
  errorMessage: string;
  lastModified: number;
};

export interface AppointmentSlot {
  time: string;
  available: boolean;
}

export interface AvailableAppointmentsResponse extends Array<AppointmentSlot> {}

export interface BookingResponse {
  success: boolean;
  appointmentId?: string;
  message?: string;
  error?: string;
}

/**
 * Direct API client for making requests without using a browser
 */
export class DirectApiClient {
  private axiosInstance: AxiosInstance;
  private userAgentRotator: UserAgentRotator;
  
  constructor() {
    this.userAgentRotator = new UserAgentRotator();
    
    // Create axios instance with common configuration
    this.axiosInstance = axios.create({
      timeout: 10000,
      headers: getHeadersForUserAgentProfile(this.userAgentRotator.getCurrentProfile())
    });
    
    // Add request interceptor for logging
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Log the request
        logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        logger.error(`API Request Error: ${error.message}`);
        return Promise.reject(error);
      }
    );
    
    // Add response interceptor for logging
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // Log the response
        logger.debug(`API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
        return response;
      },
      (error) => {
        if (error.response) {
          logger.error(`API Response Error: ${error.response.status} ${error.config.method?.toUpperCase()} ${error.config.url}`);
        } else if (error.request) {
          logger.error(`API No Response: ${error.config.method?.toUpperCase()} ${error.config.url}`);
        } else {
          logger.error(`API Error: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Rotate the user agent for the next request
   */
  private rotateUserAgent(): void {
    const profile = this.userAgentRotator.rotate();
    this.axiosInstance.defaults.headers = {
      ...this.axiosInstance.defaults.headers,
      ...getHeadersForUserAgentProfile(profile)
    };
  }
  
  /**
   * Add a random delay to avoid detection
   */
  private async randomDelay(min: number, max: number): Promise<void> {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  /**
   * Gets available days for appointments
   */
  async getAvailableDays(startDate: string, endDate: string, officeId = config.OFFICE_ID): Promise<string[]> {
    const url = `${config.AVAILABLE_DAYS_ENDPOINT}`;
    
    const params = {
      startDate,
      endDate,
      officeId,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    };
    
    try {
      // Add a small random delay to avoid detection
      await this.randomDelay(100, 300);
      
      // Rotate user agent before request
      this.rotateUserAgent();
      
      // Make the request with retry logic
      const response = await withRetry(
        async () => this.axiosInstance.get(url, { params }),
        {
          initialDelayMs: config.INITIAL_BACKOFF_MS,
          maxDelayMs: config.MAX_BACKOFF_MS,
          maxRetries: config.MAX_RETRIES
        },
        `getAvailableDays(${officeId})`
      );
      
      const data = response.data;
      
      // Handle the "no appointments" response format
      if (typeof data === 'object' && !Array.isArray(data) && 'errorCode' in data) {
        if (data.errorCode === 'noAppointmentForThisScope') {
          logger.info(`No appointments available for office ${officeId}`);
          return [];
        }
        
        logger.warn(`Unexpected error code from API: ${data.errorCode} - ${data.errorMessage}`);
        return [];
      }
      
      // Validate the response is an array of dates
      if (!Array.isArray(data)) {
        logger.error(`Invalid response format from getAvailableDays: ${JSON.stringify(data)}`);
        return [];
      }
      
      logger.info(`Found ${data.length} available days for office ${officeId}`);
      return data;
    } catch (error) {
      logger.error(`Error getting available days: ${error instanceof Error ? error.message : String(error)}`);
      return [];
    }
  }
  
  /**
   * Gets available appointments for a specific date
   */
  async getAvailableAppointments(date: string, officeId = config.OFFICE_ID): Promise<AppointmentSlot[]> {
    const url = `${config.AVAILABLE_APPOINTMENTS_ENDPOINT}`;
    
    const params = {
      date,
      officeId,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    };
    
    try {
      // Add a small random delay to avoid detection
      await this.randomDelay(100, 300);
      
      // Rotate user agent before request
      this.rotateUserAgent();
      
      // Make the request with retry logic
      const response = await withRetry(
        async () => this.axiosInstance.get(url, { params }),
        {
          initialDelayMs: config.INITIAL_BACKOFF_MS,
          maxDelayMs: config.MAX_BACKOFF_MS,
          maxRetries: config.MAX_RETRIES
        },
        `getAvailableAppointments(${date}, ${officeId})`
      );
      
      const data = response.data;
      
      // Validate the response is an array of appointment slots
      if (!Array.isArray(data)) {
        logger.error(`Invalid response format from getAvailableAppointments: ${JSON.stringify(data)}`);
        return [];
      }
      
      // Validate each appointment slot has the required properties
      const validAppointments = data.filter(slot => 
        typeof slot === 'object' && slot !== null && 'time' in slot && 'available' in slot
      );
      
      logger.info(`Found ${validAppointments.length} available appointments for ${date} at office ${officeId}`);
      return validAppointments;
    } catch (error) {
      logger.error(`Error getting available appointments: ${error instanceof Error ? error.message : String(error)}`);
      return [];
    }
  }
  
  /**
   * Books an appointment
   */
  async bookAppointment(date: string, time: string, officeId = config.OFFICE_ID): Promise<BookingResponse> {
    const url = `${config.BOOK_APPOINTMENT_ENDPOINT}`;
    
    const params = {
      date,
      time,
      officeId,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT,
      name: config.FULL_NAME,
      email: config.EMAIL,
      numberOfPersons: config.PARTY_SIZE
    };
    
    try {
      // No delay for booking - we want to be as fast as possible
      
      // Rotate user agent before request
      this.rotateUserAgent();
      
      // Make the request with retry logic
      const response = await withRetry(
        async () => this.axiosInstance.get(url, { params }),
        {
          initialDelayMs: config.INITIAL_BACKOFF_MS,
          maxDelayMs: config.MAX_BACKOFF_MS,
          maxRetries: config.MAX_RETRIES
        },
        `bookAppointment(${date}, ${time}, ${officeId})`
      );
      
      const data = response.data;
      
      // Validate the response is a booking response
      if (typeof data !== 'object' || data === null || !('success' in data)) {
        logger.error(`Invalid response format from bookAppointment: ${JSON.stringify(data)}`);
        return { success: false, error: 'Invalid response format' };
      }
      
      if (data.success) {
        logger.info(`Successfully booked appointment for ${date} at ${time} (Office: ${officeId})`);
      } else {
        logger.warn(`Failed to book appointment: ${data.error || data.message || 'Unknown error'}`);
      }
      
      return data;
    } catch (error) {
      logger.error(`Error booking appointment: ${error instanceof Error ? error.message : String(error)}`);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }
  
  /**
   * Checks API health by making a simple request
   */
  async checkApiHealth(): Promise<boolean> {
    try {
      // Try to get available days as a health check
      const startDate = new Date().toISOString().split('T')[0];
      const endDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      const days = await this.getAvailableDays(startDate, endDate);
      
      // If we got here, the API is healthy
      const isHealthy = true;
      
      // Update health status
      updateHealthStatus('apiConnected', isHealthy);
      
      return isHealthy;
    } catch (error) {
      logger.error(`API health check failed: ${error instanceof Error ? error.message : String(error)}`);
      
      // Update health status to indicate API is not connected
      updateHealthStatus('apiConnected', false);
      
      return false;
    }
  }
}
