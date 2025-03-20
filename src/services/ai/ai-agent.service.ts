import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../common/logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { BrowserService } from '../../core/browser/browser.service';
import { PageAnalyzerService } from '../../core/page-analyzer/page-analyzer.service';
import { LangchainAgentService } from './langchain-agent.service';

@Injectable()
export class AIAgentService {
  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
    private readonly browserService: BrowserService,
    private readonly pageAnalyzerService: PageAnalyzerService,
    private readonly langchainAgentService: LangchainAgentService
  ) {}

  async analyzeAndUpdateConfig(url: string): Promise<void> {
    try {
      const startTime = Date.now();
      this.loggingService.info('Starting AI agent analysis', { url });

      // Use Langchain agent to analyze the page
      const langchainAnalysis = await this.langchainAgentService.analyzePage(url);

      // Initialize browser for additional analysis
      await this.browserService.initialize();
      const page = await this.browserService.navigate(url);

      // Analyze page structure
      const pageAnalysis = await this.pageAnalyzerService.analyzeAppointmentPage(page);

      if (pageAnalysis.success && pageAnalysis.available) {
        // Combine Langchain and page analysis results
        const combinedAnalysis = {
          ...langchainAnalysis,
          pageAnalysis: {
            success: pageAnalysis.success,
            available: pageAnalysis.available,
            elements: pageAnalysis.elements,
            metadata: pageAnalysis.metadata
          }
        };

        // Update configuration based on combined analysis
        await this.updateConfiguration(combinedAnalysis);
      }

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric(
        'ai_agent_analysis_duration',
        duration,
        { url }
      );
    } catch (error) {
      this.loggingService.error('AI agent analysis failed', {
        url,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric(
        'ai_agent_analysis_error',
        1,
        { url }
      );

      throw error;
    } finally {
      await this.browserService.close();
    }
  }

  private async updateConfiguration(analysis: any): Promise<void> {
    // Update selectors and other configuration based on combined analysis
    const config = {
      selectors: {
        datePicker: analysis.selectors.datePicker,
        timePicker: analysis.selectors.timePicker,
        submitButton: analysis.selectors.submitButton,
        locationSelect: analysis.selectors.locationSelect,
        serviceSelect: analysis.selectors.serviceSelect,
        confirmationMessage: analysis.selectors.confirmationMessage
      },
      validation: {
        requiredFields: analysis.validationRules.requiredFields,
        dateFormat: analysis.validationRules.dateFormat,
        timeFormat: analysis.validationRules.timeFormat
      },
      api: {
        baseUrl: analysis.apiEndpoints.baseUrl,
        endpoints: {
          appointment: analysis.apiEndpoints.appointmentEndpoint,
          location: analysis.apiEndpoints.locationEndpoint,
          service: analysis.apiEndpoints.serviceEndpoint
        }
      },
      booking: {
        maxAttempts: this.configService.get('BOOKING_MAX_ATTEMPTS'),
        retryDelay: this.configService.get('BOOKING_RETRY_DELAY'),
        timeout: this.configService.get('BOOKING_TIMEOUT'),
        maxPartySize: analysis.metadata.maxPartySize,
        bookingWindow: analysis.metadata.bookingWindow
      }
    };

    // Update configuration in Redis or other storage
    this.loggingService.info('Updating configuration', { config });
    // TODO: Implement configuration update logic
    // await this.configService.set('BOOKING_CONFIG', config);
  }
} 