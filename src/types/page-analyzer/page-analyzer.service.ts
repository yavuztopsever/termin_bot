import { Page } from 'puppeteer';
import { PageAnalysisResult } from './page-analysis-result';
import { AppointmentConfig } from '../appointment/appointment-config';

export interface PageAnalyzerService {
  analyzeAppointmentPage(page: Page): Promise<PageAnalysisResult>;
  findAvailableSlots(config: AppointmentConfig): Promise<PageAnalysisResult>;
  checkAvailability(config: AppointmentConfig): Promise<PageAnalysisResult>;
  extractText(page: Page, selector: string): Promise<string>;
  extractDate(page: Page, selector: string): Promise<string>;
  extractTime(page: Page, selector: string): Promise<string>;
  isElementVisible(page: Page, selector: string): Promise<boolean>;
  waitForElement(page: Page, selector: string, timeout?: number): Promise<void>;
} 