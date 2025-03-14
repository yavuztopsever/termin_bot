// Configuration
export const config = {
  // URL and personal information
  URL: 'https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/10339027/locations/10187259',
  FULL_NAME: 'Yavuz Topsever',
  EMAIL: 'yavuz.topsever@windowslive.com',
  PARTY_SIZE: '1',
  PHONE_NUMBER: '+491627621469',

  // Twilio Configuration
  TWILIO_ACCOUNT_SID: 'AC3c84c2b2526cd9737db40f722f6c7dd9',
  TWILIO_AUTH_TOKEN: 'ab313932ca8fb7c39b715e7efa2c35af',
  TWILIO_PHONE_NUMBER: '+19205042794',

  // API Endpoints
  API_BASE_URL: 'https://www48.muenchen.de/buergeransicht/api/backend',
  get AVAILABLE_DAYS_ENDPOINT() { return `${this.API_BASE_URL}/available-days`; },
  get AVAILABLE_APPOINTMENTS_ENDPOINT() { return `${this.API_BASE_URL}/available-appointments`; },
  get BOOK_APPOINTMENT_ENDPOINT() { return `${this.API_BASE_URL}/book-appointment`; },

  // Constants for API requests
  OFFICE_ID: '10187259',
  SERVICE_ID: '10339027',
  SERVICE_COUNT: '1',

  // Check interval in milliseconds (15 seconds)
  CHECK_INTERVAL: 15 * 1000,

  // For testing purposes
  _isWithinTimeWindowOverride: null as boolean | null,

  // Always return true for time window check
  isWithinTimeWindow(): boolean {
    if (this._isWithinTimeWindowOverride !== null) {
      return this._isWithinTimeWindowOverride;
    }
    return true; // Always return true to continuously check
  },

  // For testing purposes
  setTimeWindowOverride(override: boolean | null) {
    this._isWithinTimeWindowOverride = override;
  }
}; 