import { config } from '../config';
import { logger } from '../services/loggingService';
import { Page } from 'puppeteer';

// Extended user agent data with browser fingerprinting properties
export interface UserAgentProfile {
  userAgent: string;
  platform: string;
  vendor: string;
  languages: string[];
  screenSize: { width: number; height: number };
  colorDepth: number;
}

// Define a set of realistic user agent profiles
export const userAgentProfiles: UserAgentProfile[] = [
  {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    platform: 'Win32',
    vendor: 'Google Inc.',
    languages: ['de-DE', 'de', 'en-US', 'en'],
    screenSize: { width: 1920, height: 1080 },
    colorDepth: 24
  },
  {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    platform: 'MacIntel',
    vendor: 'Google Inc.',
    languages: ['de-DE', 'de', 'en-US', 'en'],
    screenSize: { width: 1680, height: 1050 },
    colorDepth: 24
  },
  {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
    platform: 'Win32',
    vendor: '',
    languages: ['de-DE', 'de', 'en-US', 'en'],
    screenSize: { width: 1366, height: 768 },
    colorDepth: 24
  },
  {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    platform: 'MacIntel',
    vendor: 'Apple Computer, Inc.',
    languages: ['de-DE', 'de', 'en-US', 'en'],
    screenSize: { width: 1440, height: 900 },
    colorDepth: 24
  }
];

/**
 * Get a random user agent profile
 */
export function getRandomUserAgentProfile(): UserAgentProfile {
  return userAgentProfiles[Math.floor(Math.random() * userAgentProfiles.length)];
}

/**
 * Apply a user agent profile to a Puppeteer page
 */
export async function applyUserAgentProfile(page: Page, profile?: UserAgentProfile): Promise<void> {
  const userAgentProfile = profile || getRandomUserAgentProfile();
  logger.debug(`Applying user agent profile: ${userAgentProfile.userAgent.substring(0, 50)}...`);
  
  // Set the user agent
  await page.setUserAgent(userAgentProfile.userAgent);
  
  // Override browser fingerprinting properties
  await page.evaluateOnNewDocument((profile) => {
    // Override navigator properties
    Object.defineProperty(navigator, 'userAgent', { get: () => profile.userAgent });
    Object.defineProperty(navigator, 'platform', { get: () => profile.platform });
    Object.defineProperty(navigator, 'vendor', { get: () => profile.vendor });
    
    // Override language properties
    Object.defineProperty(navigator, 'language', { get: () => profile.languages[0] });
    Object.defineProperty(navigator, 'languages', { get: () => profile.languages });
    
    // Override screen properties
    Object.defineProperty(screen, 'width', { get: () => profile.screenSize.width });
    Object.defineProperty(screen, 'height', { get: () => profile.screenSize.height });
    Object.defineProperty(screen, 'colorDepth', { get: () => profile.colorDepth });
    
    // Add random variations to make fingerprinting harder
    const randomOffset = (max: number) => Math.floor(Math.random() * max);
    Object.defineProperty(screen, 'availWidth', { get: () => profile.screenSize.width - randomOffset(20) });
    Object.defineProperty(screen, 'availHeight', { get: () => profile.screenSize.height - randomOffset(40) - 40 });
    
  }, userAgentProfile);
}

/**
 * Get HTTP headers for a user agent profile
 */
export function getHeadersForUserAgentProfile(profile?: UserAgentProfile): Record<string, string> {
  const userAgentProfile = profile || getRandomUserAgentProfile();
  
  return {
    'User-Agent': userAgentProfile.userAgent,
    'Accept-Language': userAgentProfile.languages.join(','),
    'Sec-CH-UA-Platform': `"${userAgentProfile.platform}"`,
    'Sec-CH-UA': `"Not A;Brand";v="99", "Chromium";v="96"`,
    'Accept': 'application/json, text/plain, */*',
    'Referer': config.URL,
    'Origin': new URL(config.URL).origin
  };
}

/**
 * Class to manage user agent rotation
 */
export class UserAgentRotator {
  private usedProfiles: Set<string> = new Set();
  private currentProfile: UserAgentProfile;
  
  constructor() {
    this.currentProfile = getRandomUserAgentProfile();
    this.usedProfiles.add(this.currentProfile.userAgent);
  }
  
  public getCurrentProfile(): UserAgentProfile {
    return this.currentProfile;
  }
  
  public rotate(): UserAgentProfile {
    // If we've used all profiles, reset the used set
    if (this.usedProfiles.size >= userAgentProfiles.length) {
      this.usedProfiles.clear();
    }
    
    // Get a profile we haven't used recently
    let newProfile: UserAgentProfile;
    do {
      newProfile = getRandomUserAgentProfile();
    } while (this.usedProfiles.has(newProfile.userAgent));
    
    this.currentProfile = newProfile;
    this.usedProfiles.add(newProfile.userAgent);
    
    logger.debug(`Rotated to new user agent: ${newProfile.userAgent.substring(0, 30)}...`);
    return newProfile;
  }
}
