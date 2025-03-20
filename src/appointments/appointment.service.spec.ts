import { Test, TestingModule } from '@nestjs/testing';
import { AppointmentService } from './appointment.service';
import { ApiClientService } from '../shared/api-client/api-client.service';
import { CacheService } from '../shared/cache/cache.service';
import { LoggerService } from '../shared/logger/logger.service';
import { SearchAppointmentDto } from './dto/search-appointment.dto';
import { BookAppointmentDto } from './dto/book-appointment.dto';
import { AppointmentType } from './dto/search-appointment.dto';

describe('AppointmentService', () => {
  let service: AppointmentService;
  let apiClient: ApiClientService;
  let cacheService: CacheService;
  let loggerService: LoggerService;

  const mockApiClient = {
    searchAppointments: jest.fn(),
    checkAppointmentAvailability: jest.fn(),
    bookAppointment: jest.fn(),
    getAppointmentStatus: jest.fn(),
  };

  const mockCacheService = {
    get: jest.fn(),
    set: jest.fn(),
    deletePattern: jest.fn(),
  };

  const mockLoggerService = {
    debug: jest.fn(),
    error: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AppointmentService,
        {
          provide: ApiClientService,
          useValue: mockApiClient,
        },
        {
          provide: CacheService,
          useValue: mockCacheService,
        },
        {
          provide: LoggerService,
          useValue: mockLoggerService,
        },
      ],
    }).compile();

    service = module.get<AppointmentService>(AppointmentService);
    apiClient = module.get<ApiClientService>(ApiClientService);
    cacheService = module.get<CacheService>(CacheService);
    loggerService = module.get<LoggerService>(LoggerService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('searchAppointments', () => {
    const mockSearchDto: SearchAppointmentDto = {
      type: AppointmentType.PASSPORT,
      preferredDate: '2024-03-25T10:00:00Z',
      location: 'Munich',
    };

    it('should return cached results if available', async () => {
      const cachedResults = [{ id: 1, date: '2024-03-25T10:00:00Z' }];
      mockCacheService.get.mockResolvedValue(cachedResults);

      const result = await service.searchAppointments(mockSearchDto);

      expect(result).toEqual(cachedResults);
      expect(mockCacheService.get).toHaveBeenCalled();
      expect(mockApiClient.searchAppointments).not.toHaveBeenCalled();
    });

    it('should fetch and cache new results if not cached', async () => {
      const apiResults = [{ id: 1, date: '2024-03-25T10:00:00Z' }];
      mockCacheService.get.mockResolvedValue(null);
      mockApiClient.searchAppointments.mockResolvedValue(apiResults);

      const result = await service.searchAppointments(mockSearchDto);

      expect(result).toEqual(apiResults);
      expect(mockCacheService.set).toHaveBeenCalled();
      expect(mockApiClient.searchAppointments).toHaveBeenCalledWith(mockSearchDto);
    });
  });

  describe('bookAppointment', () => {
    const mockBookingDto: BookAppointmentDto = {
      type: AppointmentType.PASSPORT,
      appointmentDateTime: '2024-03-25T10:00:00Z',
      fullName: 'John Doe',
      email: 'john@example.com',
      phoneNumber: '+491234567890',
    };

    it('should successfully book an appointment', async () => {
      mockApiClient.checkAppointmentAvailability.mockResolvedValue(true);
      mockApiClient.bookAppointment.mockResolvedValue({ id: 1, status: 'BOOKED' });

      const result = await service.bookAppointment(mockBookingDto);

      expect(result).toEqual({ id: 1, status: 'BOOKED' });
      expect(mockCacheService.deletePattern).toHaveBeenCalled();
    });

    it('should throw ConflictException if appointment is not available', async () => {
      mockApiClient.checkAppointmentAvailability.mockResolvedValue(false);

      await expect(service.bookAppointment(mockBookingDto)).rejects.toThrow('Appointment is no longer available');
    });
  });

  describe('getAppointmentStatus', () => {
    it('should return appointment status', async () => {
      const mockStatus = { id: 1, status: 'CONFIRMED' };
      mockApiClient.getAppointmentStatus.mockResolvedValue(mockStatus);

      const result = await service.getAppointmentStatus('1');

      expect(result).toEqual(mockStatus);
    });

    it('should throw NotFoundException if appointment not found', async () => {
      mockApiClient.getAppointmentStatus.mockResolvedValue(null);

      await expect(service.getAppointmentStatus('1')).rejects.toThrow('Appointment not found');
    });
  });
}); 