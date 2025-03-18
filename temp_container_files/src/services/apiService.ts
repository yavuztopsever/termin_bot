import { Page } from 'puppeteer';
import { config } from '../config';
import { sendSMS } from './notificationService';

// Response type definitions
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

// Error types
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly endpoint: string,
    public readonly statusCode?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ConnectionError extends Error {
  constructor(
    message: string,
    public readonly endpoint: string
  ) {
    super(message);
    this.name = 'ConnectionError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly endpoint: string,
    public readonly data: any
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// API Client class
export class ApiClient {
  private readonly MAX_RETRIES = 3;
  private readonly INITIAL_BACKOFF_MS = 1000;
  
  constructor(private readonly page: Page) {}
  
  /**
   * Validates that the response is an array of date strings or a valid "no appointments" response
   */
  private validateAvailableDaysResponse(data: any): data is AvailableDaysResponse {
    // Handle the "no appointments" response format
    if (typeof data === 'object' && data !== null && 'errorCode' in data) {
      if (data.errorCode === 'noAppointmentForThisScope') {
        // This is a valid response indicating no appointments
        return true;
      }
    }
    
    // Original validation for array of dates
    return Array.isArray(data) && 
           (data.length === 0 || 
            (typeof data[0] === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(data[0])));
  }
  
  /**
   * Validates that the response is an array of appointment slots
   */
  private validateAvailableAppointmentsResponse(data: any): data is AvailableAppointmentsResponse {
    return Array.isArray(data) && 
           (data.length === 0 || 
            (typeof data[0] === 'object' && 
             'time' in data[0] && 
             'available' in data[0]));
  }
  
  /**
   * Validates that the response is a booking response
   */
  private validateBookingResponse(data: any): data is BookingResponse {
    return typeof data === 'object' && 
           data !== null && 
           'success' in data && 
           typeof data.success === 'boolean';
  }
  
  /**
   * Makes an API request with retry logic and validation
   */
  private async makeRequest<T>(
    url: string, 
    validator: (data: any) => data is T,
    endpoint: string,
    retryCount = 0
  ): Promise<T> {
    try {
      // Add a small random delay to avoid detection
      const randomDelay = Math.floor(Math.random() * 500) + 100;
      await new Promise(resolve => setTimeout(resolve, randomDelay));
      
      // Make the request
      const response = await this.page.evaluate(async (requestUrl) => {
        try {
          const response = await fetch(requestUrl);
          
          if (!response.ok) {
            return { 
              error: true, 
              status: response.status, 
              message: `HTTP error ${response.status}: ${response.statusText}` 
            };
          }
          
          return { data: await response.json() };
        } catch (error) {
          return { 
            error: true, 
            message: error instanceof Error ? error.message : String(error),
            connectionError: true
          };
        }
      }, url);
      
      // Handle error responses
      if ('error' in response) {
        if ('connectionError' in response) {
          throw new ConnectionError(
            response.message || 'Connection error',
            endpoint
          );
        } else {
          throw new ApiError(
            response.message || 'API error',
            endpoint,
            response.status
          );
        }
      }
      
      // Validate the response
      if (!validator(response.data)) {
        console.error(`Invalid response format from ${endpoint}:`, response.data);
        throw new ValidationError('Invalid response format', endpoint, response.data);
      }
      
      return response.data;
    } catch (error) {
      // Handle retries with exponential backoff
      if (retryCount < this.MAX_RETRIES) {
        const backoffTime = this.INITIAL_BACKOFF_MS * Math.pow(2, retryCount);
        const jitter = Math.floor(Math.random() * 300);
        const waitTime = backoffTime + jitter;
        
        console.warn(`Request to ${endpoint} failed. Retrying in ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        
        return this.makeRequest(url, validator, endpoint, retryCount + 1);
      }
      
      // If we've exhausted retries, rethrow the error
      throw error;
    }
  }
  
  /**
   * Gets available days for appointments
   */
  async getAvailableDays(startDate: string, endDate: string, officeId = config.OFFICE_ID): Promise<AvailableDaysResponse> {
    const url = `${config.AVAILABLE_DAYS_ENDPOINT}?${new URLSearchParams({
      startDate,
      endDate,
      officeId,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    })}`;
    
    const response = await this.makeRequest(url, this.validateAvailableDaysResponse, 'available-days');
    
    // If we got a "no appointments" response object, return an empty array
    if (typeof response === 'object' && !Array.isArray(response) && 'errorCode' in response) {
      if (response.errorCode === 'noAppointmentForThisScope') {
        return [];
      }
    }
    
    return response as string[];
  }
  
  /**
   * Gets available appointments for a specific date
   */
  async getAvailableAppointments(date: string): Promise<AvailableAppointmentsResponse> {
    const url = `${config.AVAILABLE_APPOINTMENTS_ENDPOINT}?${new URLSearchParams({
      date,
      officeId: config.OFFICE_ID,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    })}`;
    
    return this.makeRequest(url, this.validateAvailableAppointmentsResponse, 'available-appointments');
  }
  
  /**
   * Books an appointment
   */
  async bookAppointment(date: string, time: string): Promise<BookingResponse> {
    const url = `${config.BOOK_APPOINTMENT_ENDPOINT}?${new URLSearchParams({
      date,
      time,
      officeId: config.OFFICE_ID,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT,
      name: config.FULL_NAME,
      email: config.EMAIL,
      numberOfPersons: config.PARTY_SIZE
    })}`;
    
    return this.makeRequest(url, this.validateBookingResponse, 'book-appointment');
  }
  
  /**
   * Checks API health by making a simple request
   */
  async checkApiHealth(): Promise<boolean> {
    try {
      // Try to get available days as a health check
      const startDate = new Date().toISOString().split('T')[0];
      const endDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      await this.getAvailableDays(startDate, endDate);
      return true;
    } catch (error) {
      console.error('API health check failed:', error instanceof Error ? error.message : String(error));
      return false;
    }
  }
}
