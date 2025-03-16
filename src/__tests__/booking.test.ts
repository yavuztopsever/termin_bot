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
      close: jest.fn().mockResolvedValue(undefined),
      setUserAgent: jest.fn().mockResolvedValue(undefined),
      setDefaultNavigationTimeout: jest.fn()
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

// Mock fs for logging
jest.mock('fs', () => ({
  existsSync: jest.fn().mockReturnValue(true),
  mkdirSync: jest.fn(),
  appendFileSync: jest.fn()
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

// Mock the logger to avoid console output during tests
jest.mock('../services/loggingService', () => ({
  logger: {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn()
  }
}));

describe('Appointment Booking Tests', () => {
  // Create a mock page that mimics the Puppeteer Page interface
  let mockPage: Partial<Page>;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create a mock page object
    mockPage = {
      evaluate: jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
        // For our new API client, we need to mock the response format
        if (typeof args[0] === 'string' && args[0].includes('/available-days')) {
          return Promise.resolve({ data: ['2025-03-15'] });
        }
        
        if (typeof args[0] === 'string' && args[0].includes('/available-appointments')) {
          return Promise.resolve({ 
            data: [{
              time: '09:00',
              available: true
            }]
          });
        }
        
        if (typeof args[0] === 'string' && args[0].includes('/book-appointment')) {
          return Promise.resolve({ 
            data: {
              success: true,
              appointmentId: '12345',
              message: 'Appointment booked successfully'
            }
          });
        }
        
        // Default case - call the function with args
        return Promise.resolve(fn(...args));
      }),
      setUserAgent: jest.fn(),
      setDefaultNavigationTimeout: jest.fn()
    };
    
    // Set time window override to true for tests
    config.setTimeWindowOverride(true);
  });

  afterEach(() => {
    // Reset time window override
    config.setTimeWindowOverride(null);
    jest.clearAllMocks();
  });

  test('should successfully book an appointment when slots are available', async () => {
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(true);
  });

  test('should handle failed booking attempt', async () => {
    // Arrange - override the evaluate mock for book-appointment
    mockPage.evaluate = jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
      if (typeof args[0] === 'string' && args[0].includes('/available-days')) {
        return Promise.resolve({ data: ['2025-03-15'] });
      }
      
      if (typeof args[0] === 'string' && args[0].includes('/available-appointments')) {
        return Promise.resolve({ 
          data: [{
            time: '09:00',
            available: true
          }]
        });
      }
      
      if (typeof args[0] === 'string' && args[0].includes('/book-appointment')) {
        return Promise.resolve({ 
          data: {
            success: false,
            error: 'Slot no longer available',
            message: 'The selected appointment slot is no longer available'
          }
        });
      }
      
      return Promise.resolve(fn(...args));
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
  });

  test('should return false when no appointments are available', async () => {
    // Arrange - override the evaluate mock to return empty arrays
    mockPage.evaluate = jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
      if (typeof args[0] === 'string' && args[0].includes('/available-days')) {
        return Promise.resolve({ data: [] }); // No available days
      }
      
      return Promise.resolve(fn(...args));
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
  });

  test('should handle API errors gracefully', async () => {
    // Arrange - override the evaluate mock to throw an error
    mockPage.evaluate = jest.fn().mockImplementation((fn: Function, ...args: any[]) => {
      if (typeof args[0] === 'string' && args[0].includes('/available-days')) {
        return Promise.resolve({ 
          error: true, 
          message: 'API error',
          connectionError: true
        });
      }
      
      return Promise.resolve(fn(...args));
    });
    
    // Act
    const result = await checkAppointments(mockPage as Page);
    
    // Assert
    expect(result).toBe(false);
  }, 10000); // Increase timeout for this test
});
