import { Page } from 'puppeteer';
import { config } from '../config';
import { sendSMS } from './notificationService';

/**
 * Checks for available appointments and attempts to book one if found
 * @param page Puppeteer page instance
 * @returns Promise that resolves to true if an appointment was booked, false otherwise
 */
export async function checkAppointments(page: Page): Promise<boolean> {
  try {
    // Calculate date range (6 months from today)
    const startDate = new Date().toISOString().split('T')[0];
    const endDate = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    console.log(`\nChecking for appointments at ${new Date().toLocaleTimeString()}...`);

    // First API request to get available days
    const availableDaysUrl = `${config.AVAILABLE_DAYS_ENDPOINT}?${new URLSearchParams({
      startDate,
      endDate,
      officeId: config.OFFICE_ID,
      serviceId: config.SERVICE_ID,
      serviceCount: config.SERVICE_COUNT
    })}`;

    const availableDaysResponse = await page.evaluate(async (url) => {
      const response = await fetch(url);
      return response.json();
    }, availableDaysUrl);

    if (availableDaysResponse && Array.isArray(availableDaysResponse) && availableDaysResponse.length > 0) {
      // Get the first available date
      const firstAvailableDate = availableDaysResponse[0];

      // Second API request to get available appointments for that date
      const availableAppointmentsUrl = `${config.AVAILABLE_APPOINTMENTS_ENDPOINT}?${new URLSearchParams({
        date: firstAvailableDate,
        officeId: config.OFFICE_ID,
        serviceId: config.SERVICE_ID,
        serviceCount: config.SERVICE_COUNT
      })}`;

      const availableAppointmentsResponse = await page.evaluate(async (url) => {
        const response = await fetch(url);
        return response.json();
      }, availableAppointmentsUrl);

      if (availableAppointmentsResponse && Array.isArray(availableAppointmentsResponse) && availableAppointmentsResponse.length > 0) {
        // Get the first available appointment
        const firstAppointment = availableAppointmentsResponse[0];

        // Send SMS about available appointment
        await sendSMS(`Found available appointment on ${firstAvailableDate} at ${firstAppointment.time}`);

        // Try to book the appointment
        const bookingUrl = `${config.BOOK_APPOINTMENT_ENDPOINT}?${new URLSearchParams({
          date: firstAvailableDate,
          time: firstAppointment.time,
          officeId: config.OFFICE_ID,
          serviceId: config.SERVICE_ID,
          serviceCount: config.SERVICE_COUNT,
          name: config.FULL_NAME,
          email: config.EMAIL,
          numberOfPersons: config.PARTY_SIZE
        })}`;

        const bookingResponse = await page.evaluate(async (url) => {
          const response = await fetch(url);
          return response.json();
        }, bookingUrl);

        if (bookingResponse && bookingResponse.success) {
          // Send SMS about successful booking
          await sendSMS(`Successfully booked appointment for ${firstAvailableDate} at ${firstAppointment.time}`);
          return true;
        }
      }
    }

    console.log('No appointments available');
    return false;
  } catch (error) {
    if (error instanceof Error) {
      console.error('Error checking appointments:', error.message);
      await sendSMS(`Error checking appointments: ${error.message}`);
    }
    return false;
  }
} 