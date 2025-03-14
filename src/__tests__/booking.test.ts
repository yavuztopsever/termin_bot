import { jest } from '@jest/globals';
import { config } from '../config';
import { Page } from 'puppeteer';

// Mock the entire puppeteer module
jest.mock('puppeteer', () => ({
  launch: jest.fn().mockResolvedValue({
    newPage: jest.fn().mockResolvedValue({
      goto: jest.fn().mockResolvedValue(undefined),
      evaluate: jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
        // Simulate the page.evaluate function by directly calling the function with args
        return Promise.resolve(fn(...args));
      }),
      close: jest.fn().mockResolvedValue(undefined)
    }),
    close: jest.fn().mockResolvedValue(undefined)
  })
}));

// Mock Twilio
jest.mock('twilio', () => {
  return jest.fn().mockImplementation(() => ({
    messages: {
      create: jest.fn().mockResolvedValue({
        sid: 'test-sid'
      })
    }
  }));
});

// Mock node-notifier
jest.mock('node-notifier', () => ({
  notify: jest.fn()
}));

// Define a type for our mocked fetch response
type MockResponse = {
  ok: boolean;
  json: () => Promise<any>;
};

// Mock fetch in the global scope for testing
global.fetch = jest.fn() as jest.Mock;

// Import the function to test after mocks are set up
import { checkAppointments } from '../services/appointmentService';

describe('Appointment Booking Tests', () => {
  // Create a mock page that mimics the Puppeteer Page interface
  let mockPage: Partial<Page>;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create a mock page object
    mockPage = {
      evaluate: jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
        // Directly call the function with args
        return Promise.resolve(fn(...args));
      })
    };
    
    // Set time window override to true for tests
    config.setTimeWindowOverride(true);
    
    // Mock global fetch for the tests
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      const urlString = url.toString();
      
      if (urlString.includes('/available-days')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(['2025-03-15'])
        } as MockResponse);
      } 
      
      if (urlString.includes('/available-appointments')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([{
            time: '09:00',
            available: true
          }])
        } as MockResponse);
      }
      
      if (urlString.includes('/book-appointment')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            appointmentId: '12345',
            message: 'Appointment booked successfully'
          })
        } as MockResponse);
      }
      
      return Promise.reject(new Error(`Unhandled fetch URL: ${urlString}`));
    });
  });

  afterEach(() => {
    // Reset time window override
    config.setTimeWindowOverride(null);
  });

  test('should successfully book an appointment when slots are available', async () => {
    // Arrange - already set up in beforeEach
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(true);
    expect(mockPage.evaluate).toHaveBeenCalledTimes(3); // Called for each API endpoint
  });

  test('should handle failed booking attempt', async () => {
    // Arrange - override the fetch mock for book-appointment
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      const urlString = url.toString();
      
      if (urlString.includes('/available-days')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(['2025-03-15'])
        } as MockResponse);
      } 
      
      if (urlString.includes('/available-appointments')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([{
            time: '09:00',
            available: true
          }])
        } as MockResponse);
      }
      
      if (urlString.includes('/book-appointment')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: false,
            error: 'Slot no longer available',
            message: 'The selected appointment slot is no longer available'
          })
        } as MockResponse);
      }
      
      return Promise.reject(new Error(`Unhandled fetch URL: ${urlString}`));
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
    expect(mockPage.evaluate).toHaveBeenCalledTimes(3); // Called for each API endpoint
  });

  test('should return false when no appointments are available', async () => {
    // Arrange - override the fetch mock to return empty arrays
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      const urlString = url.toString();
      
      if (urlString.includes('/available-days')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]) // No available days
        } as MockResponse);
      } 
      
      return Promise.reject(new Error(`Unhandled fetch URL: ${urlString}`));
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
    expect(mockPage.evaluate).toHaveBeenCalledTimes(1); // Only called for available days
  });

  test('should handle API errors gracefully', async () => {
    // Arrange - override the fetch mock to throw an error
    (global.fetch as jest.Mock).mockImplementation(() => {
      throw new Error('API error');
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
  });
}); 