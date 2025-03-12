/// <reference lib="dom" />
import puppeteer from 'puppeteer';
import notifier from 'node-notifier';
import twilio from 'twilio';

// Configuration
const URL = 'https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/10339027/locations/10187259';
const FULL_NAME = 'Yavuz Topsever';
const EMAIL = 'yavuz.topsever@windowslive.com';
const PARTY_SIZE = '1';
const PHONE_NUMBER = '+491627621469';

// Twilio Configuration
const TWILIO_ACCOUNT_SID = 'YOUR_TWILIO_ACCOUNT_SID'; // Replace with your Twilio Account SID
const TWILIO_AUTH_TOKEN = 'YOUR_TWILIO_AUTH_TOKEN';   // Replace with your Twilio Auth Token
const TWILIO_PHONE_NUMBER = 'YOUR_TWILIO_PHONE_NUMBER'; // Replace with your Twilio phone number
const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);

// API Endpoints
const API_BASE_URL = 'https://www48.muenchen.de/buergeransicht/api/backend';
const AVAILABLE_DAYS_ENDPOINT = `${API_BASE_URL}/available-days`;
const AVAILABLE_APPOINTMENTS_ENDPOINT = `${API_BASE_URL}/available-appointments`;
const BOOK_APPOINTMENT_ENDPOINT = `${API_BASE_URL}/book-appointment`;

// Constants for API requests
const OFFICE_ID = '10187259';
const SERVICE_ID = '10339027';
const SERVICE_COUNT = '1';

// Check interval in milliseconds (8 seconds)
const CHECK_INTERVAL = 8 * 1000;

// Time window configuration
const START_HOUR = 6;  // 6 AM
const END_HOUR = 8;    // 8 AM

// Function to check if current time is within the allowed window
function isWithinTimeWindow(): boolean {
  const now = new Date();
  const hour = now.getHours();
  return hour >= START_HOUR && hour < END_HOUR;
}

// Function to send SMS notification
async function sendSMS(message: string) {
  try {
    const sms = await twilioClient.messages.create({
      body: message,
      from: TWILIO_PHONE_NUMBER,
      to: PHONE_NUMBER
    });
    console.log('SMS sent successfully:', sms.sid);
  } catch (error) {
    console.error('Failed to send SMS:', error);
  }
}

// Function to send notifications
async function sendNotifications(title: string, message: string) {
  // Send desktop notification
  notifier.notify({
    title,
    message,
    sound: true,
    wait: true
  });

  // Send SMS notification
  await sendSMS(message);
}

// Function to check for available appointments
async function checkAppointments(page: puppeteer.Page): Promise<boolean> {
  try {
    if (!isWithinTimeWindow()) {
      console.log(`[${new Date().toLocaleString()}] Outside checking window (${START_HOUR}:00-${END_HOUR}:00). Waiting...`);
      return false;
    }

    // Calculate date range (6 months from today)
    const startDate = new Date().toISOString().split('T')[0];
    const endDate = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    // First API request to get available days
    console.log(`[${new Date().toLocaleString()}] Checking available days...`);
    const availableDaysUrl = `${AVAILABLE_DAYS_ENDPOINT}?${new URLSearchParams({
      startDate,
      endDate,
      officeId: OFFICE_ID,
      serviceId: SERVICE_ID,
      serviceCount: SERVICE_COUNT
    })}`;

    const availableDaysResponse = await page.goto(availableDaysUrl);
    const availableDaysData = await availableDaysResponse?.json();

    if (availableDaysData && Array.isArray(availableDaysData) && availableDaysData.length > 0) {
      // Get the first available date
      const firstAvailableDate = availableDaysData[0];
      console.log('First available date:', firstAvailableDate);

      // Second API request to get available appointments for that date
      console.log('Checking available appointments for the first available date...');
      const availableAppointmentsUrl = `${AVAILABLE_APPOINTMENTS_ENDPOINT}?${new URLSearchParams({
        date: firstAvailableDate,
        officeId: OFFICE_ID,
        serviceId: SERVICE_ID,
        serviceCount: SERVICE_COUNT
      })}`;

      const availableAppointmentsResponse = await page.goto(availableAppointmentsUrl);
      const availableAppointmentsData = await availableAppointmentsResponse?.json();

      if (availableAppointmentsData && Array.isArray(availableAppointmentsData) && availableAppointmentsData.length > 0) {
        // Get the first available appointment
        const firstAppointment = availableAppointmentsData[0];
        console.log('Found appointment:', firstAppointment);

        const notificationMessage = `Found appointment on ${firstAvailableDate} at ${firstAppointment.time}`;
        await sendNotifications('Appointment Available!', notificationMessage);

        // Try to book the appointment
        console.log('Attempting to book the appointment...');
        const bookingUrl = `${BOOK_APPOINTMENT_ENDPOINT}?${new URLSearchParams({
          date: firstAvailableDate,
          time: firstAppointment.time,
          officeId: OFFICE_ID,
          serviceId: SERVICE_ID,
          serviceCount: SERVICE_COUNT,
          name: FULL_NAME,
          email: EMAIL,
          numberOfPersons: PARTY_SIZE
        })}`;

        const bookingResponse = await page.goto(bookingUrl);
        const bookingData = await bookingResponse?.json();

        if (bookingData && bookingData.success) {
          console.log('Successfully booked appointment!');
          const successMessage = `Successfully booked appointment for ${firstAvailableDate} at ${firstAppointment.time}`;
          await sendNotifications('Appointment Booked!', successMessage);
          return true; // Stop checking after successful booking
        } else {
          console.log('Failed to book appointment:', bookingData);
          await sendSMS(`Failed to book appointment for ${firstAvailableDate} at ${firstAppointment.time}. Will keep trying.`);
          return false; // Continue checking if booking failed
        }
      }
    }

    console.log(`[${new Date().toLocaleString()}] No available appointments found.`);
    return false;
  } catch (error) {
    console.error('Error checking appointments:', error);
    await sendSMS(`Error occurred while checking appointments: ${error.message}`);
    return false;
  }
}

// Main function
(async () => {
  try {
    const browser = await puppeteer.launch({ 
      headless: false,
      defaultViewport: null,
      args: ['--start-maximized', '--disable-features=site-per-process']
    });
    const page = await browser.newPage();
    
    // Enable request interception
    await page.setRequestInterception(true);
    
    // Log all requests
    page.on('request', request => {
      console.log('Request:', request.url());
      request.continue();
    });
    
    // Log all responses
    page.on('response', response => {
      console.log('Response:', response.url(), response.status());
    });
    
    // Set a longer default timeout
    page.setDefaultTimeout(60000);

    console.log('Starting periodic appointment checker...');
    console.log(`Will check every ${CHECK_INTERVAL / 1000} seconds between ${START_HOUR}:00 and ${END_HOUR}:00.`);

    // Send initial notification
    await sendSMS(`Appointment checker started. Will check every ${CHECK_INTERVAL / 1000} seconds between ${START_HOUR}:00 and ${END_HOUR}:00.`);

    // Initial check
    let success = await checkAppointments(page);

    // If initial check didn't succeed, start periodic checking
    if (!success) {
      const intervalId = setInterval(async () => {
        success = await checkAppointments(page);
        if (success) {
          clearInterval(intervalId);
          await browser.close();
          process.exit(0);
        }
      }, CHECK_INTERVAL);

      // Handle process termination
      process.on('SIGINT', async () => {
        clearInterval(intervalId);
        await browser.close();
        await sendSMS('Appointment checker stopped by user.');
        process.exit(0);
      });
    } else {
      await browser.close();
      process.exit(0);
    }
  } catch (error) {
    console.error('An error occurred:', error);
    
    if (error instanceof Error) {
      console.error('Error details:', error.message);
      console.error('Stack trace:', error.stack);
      await sendSMS(`Critical error in appointment checker: ${error.message}`);
    }
    
    process.exit(1);
  }
})();