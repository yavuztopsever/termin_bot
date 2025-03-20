import { Test, TestingModule } from '@nestjs/testing';
import { BookingService } from './booking.service';
import { ApiClientService } from '../../shared/api-client/api-client.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { BookingRequest, BookingResult } from './booking.types';

describe('BookingService', () => {
  let service: BookingService;
  let apiClient: ApiClientService;
  let monitoringService: MonitoringService;

  const mockApiClient = {
    bookAppointment: jest.fn()
  };

  const mockMonitoringService = {
    recordSuccess: jest.fn(),
    recordError: jest.fn()
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        BookingService,
        {
          provide: ApiClientService,
          useValue: mockApiClient
        },
        {
          provide: MonitoringService,
          useValue: mockMonitoringService
        }
      ]
    }).compile();

    service = module.get<BookingService>(BookingService);
    apiClient = module.get<ApiClientService>(ApiClientService);
    monitoringService = module.get<MonitoringService>(MonitoringService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('bookAppointment', () => {
    const mockRequest: BookingRequest = {
      type: 'PASSPORT',
      preferredDate: '2024-03-25T10:00:00Z',
      location: 'Munich',
      fullName: 'John Doe',
      email: 'john@example.com',
      phoneNumber: '+491234567890'
    };

    it('should successfully book an appointment through API', async () => {
      const mockResult: BookingResult = {
        success: true,
        appointmentId: '123'
      };
      mockApiClient.bookAppointment.mockResolvedValue(mockResult);

      const result = await service.bookAppointment(mockRequest);

      expect(result).toEqual(mockResult);
      expect(mockApiClient.bookAppointment).toHaveBeenCalledWith(mockRequest);
      expect(mockMonitoringService.recordSuccess).toHaveBeenCalledWith('api_booking');
    });

    it('should handle API booking failure', async () => {
      mockApiClient.bookAppointment.mockResolvedValue({
        success: false,
        error: 'API Error'
      });

      const result = await service.bookAppointment(mockRequest);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to book appointment');
      expect(mockMonitoringService.recordError).toHaveBeenCalledWith('booking_failed', expect.any(Error));
    });
  });
}); 