// Configuration
export interface LocationConfig {
  id: string;
  name: string;
}

class AppConfig {
  // URL and personal information
  readonly URL = 'https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/10339027/locations/10187259';
  readonly FULL_NAME = 'Yavuz Topsever';
  readonly EMAIL = 'yavuz.topsever@windowslive.com';
  readonly PARTY_SIZE = '1';
  readonly PHONE_NUMBER = '+491627621469';

  // Twilio Configuration
  readonly TWILIO_ACCOUNT_SID = 'AC3c84c2b2526cd9737db40f722f6c7dd9';
  readonly TWILIO_AUTH_TOKEN = '3e29c18b58fa0c67315a1fe28ddc5868';
  readonly TWILIO_PHONE_NUMBER = '+19205042794';

  // API Endpoints
  readonly API_BASE_URL = 'https://www48.muenchen.de/buergeransicht/api/backend';
  get AVAILABLE_DAYS_ENDPOINT() { return `${this.API_BASE_URL}/available-days`; }
  get AVAILABLE_APPOINTMENTS_ENDPOINT() { return `${this.API_BASE_URL}/available-appointments`; }
  get BOOK_APPOINTMENT_ENDPOINT() { return `${this.API_BASE_URL}/book-appointment`; }

  // Constants for API requests
  readonly OFFICE_ID = '10187259';
  readonly SERVICE_ID = '10339027';
  readonly SERVICE_COUNT = '1';

  // Check intervals
  readonly BROWSER_CHECK_INTERVAL = 8 * 1000;  // 8 seconds for browser checks
  readonly API_CHECK_INTERVAL = 5 * 1000;      // 5 seconds for direct API checks
  readonly CHECK_INTERVAL = 5 * 1000;          // Default check interval (5 seconds)
  readonly MIN_CHECK_INTERVAL = 3 * 1000;      // Minimum interval during aggressive mode
  
  // Timing strategy
  readonly AGGRESSIVE_MODE_HOURS = [8, 9, 12, 13, 16, 17]; // Hours when slots typically appear
  readonly JITTER_FACTOR = 0.3;                // Randomization factor to avoid detection
  
  // Retry strategy
  readonly MAX_RETRIES = 3;
  readonly INITIAL_BACKOFF_MS = 1000;
  readonly MAX_BACKOFF_MS = 30000;
  
  // Multiple locations to check
  readonly LOCATIONS: LocationConfig[] = [
    { id: '10187259', name: 'Main Office' },
    // Add other locations if available
  ];
  
  // User agents for rotation
  readonly USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15'
  ];

  // For testing purposes
  private _isWithinTimeWindowOverride: boolean | null = null;

  // Always return true for time window check
  isWithinTimeWindow(): boolean {
    if (this._isWithinTimeWindowOverride !== null) {
      return this._isWithinTimeWindowOverride;
    }
    return true; // Always return true to continuously check
  }

  // For testing purposes
  setTimeWindowOverride(override: boolean | null): void {
    this._isWithinTimeWindowOverride = override;
  }
  
  // Get a randomized check interval based on current time
  getRandomizedCheckInterval(baseInterval = this.CHECK_INTERVAL): number {
    const now = new Date();
    const currentHour = now.getHours();
    
    // Use more aggressive timing during peak hours
    let interval = baseInterval;
    if (this.AGGRESSIVE_MODE_HOURS.includes(currentHour)) {
      interval = this.MIN_CHECK_INTERVAL;
    }
    
    // Add random jitter (±JITTER_FACTOR of base interval)
    const jitter = Math.floor(interval * this.JITTER_FACTOR * (Math.random() * 2 - 1));
    
    return Math.max(this.MIN_CHECK_INTERVAL, interval + jitter);
  }
}

export const config = new AppConfig();
