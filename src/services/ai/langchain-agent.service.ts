import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../common/logging.service';
import { MonitoringService } from '../monitoring/monitoring.service';
import { ChatOpenAI } from 'langchain/chat_models/openai';
import { AgentExecutor, createOpenAIFunctionsAgent } from 'langchain/agents';
import { ChatPromptTemplate, MessagesPlaceholder } from 'langchain/prompts';
import { SystemMessage } from 'langchain/schema';
import { RunnableSequence } from 'langchain/runnables';
import { StructuredOutputParser } from 'langchain/output_parsers';
import { z } from 'zod';

@Injectable()
export class LangchainAgentService {
  private readonly model: ChatOpenAI;
  private readonly parser: StructuredOutputParser;

  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService
  ) {
    this.model = new ChatOpenAI({
      modelName: this.configService.get('AI_MODEL'),
      temperature: this.configService.get('AI_TEMPERATURE'),
      maxTokens: this.configService.get('AI_MAX_TOKENS'),
      openAIApiKey: this.configService.get('AI_API_KEY')
    });

    this.parser = StructuredOutputParser.fromZodSchema(
      z.object({
        apiEndpoints: z.object({
          baseUrl: z.string(),
          appointmentEndpoint: z.string(),
          locationEndpoint: z.string(),
          serviceEndpoint: z.string()
        }),
        selectors: z.object({
          datePicker: z.string(),
          timePicker: z.string(),
          locationSelect: z.string(),
          serviceSelect: z.string(),
          submitButton: z.string(),
          confirmationMessage: z.string()
        }),
        validationRules: z.object({
          dateFormat: z.string(),
          timeFormat: z.string(),
          requiredFields: z.array(z.string())
        }),
        metadata: z.object({
          officeId: z.string(),
          serviceId: z.string(),
          maxPartySize: z.number(),
          bookingWindow: z.number()
        })
      })
    );
  }

  async analyzePage(url: string): Promise<any> {
    try {
      const startTime = Date.now();
      this.loggingService.info('Starting Langchain agent analysis', { url });

      const prompt = ChatPromptTemplate.fromMessages([
        new SystemMessage(
          `You are an expert web scraping and API analysis agent. Your task is to analyze the Munich city appointment booking page and extract:
          1. API endpoints and their structure
          2. HTML selectors for form elements
          3. Validation rules and formats
          4. Metadata about the booking system
          
          URL: ${url}
          
          Please provide detailed information about the page structure and API endpoints.`
        ),
        new MessagesPlaceholder('agent_scratchpad')
      ]);

      const agent = await createOpenAIFunctionsAgent({
        llm: this.model,
        prompt,
        tools: [
          // Add tools for analyzing the page
          {
            name: 'analyze_page_structure',
            description: 'Analyzes the HTML structure of the page',
            parameters: {
              type: 'object',
              properties: {
                url: { type: 'string' }
              },
              required: ['url']
            }
          },
          {
            name: 'extract_api_endpoints',
            description: 'Extracts API endpoints from network requests',
            parameters: {
              type: 'object',
              properties: {
                url: { type: 'string' }
              },
              required: ['url']
            }
          },
          {
            name: 'analyze_form_elements',
            description: 'Analyzes form elements and their validation rules',
            parameters: {
              type: 'object',
              properties: {
                url: { type: 'string' }
              },
              required: ['url']
            }
          }
        ]
      });

      const agentExecutor = new AgentExecutor({
        agent,
        tools: [],
        verbose: true
      });

      const result = await agentExecutor.invoke({
        input: `Analyze the Munich city appointment booking page at ${url}`
      });

      const parsedResult = await this.parser.parse(result.output);

      const duration = Date.now() - startTime;
      this.monitoringService.recordMetric(
        'langchain_agent_analysis_duration',
        duration,
        { url }
      );

      return parsedResult;
    } catch (error) {
      this.loggingService.error('Langchain agent analysis failed', {
        url,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      this.monitoringService.recordMetric(
        'langchain_agent_analysis_error',
        1,
        { url }
      );

      throw error;
    }
  }

  async updateConfiguration(analysis: any): Promise<void> {
    try {
      // Update configuration in Redis or other storage
      const config = {
        api: {
          baseUrl: analysis.apiEndpoints.baseUrl,
          endpoints: {
            appointment: analysis.apiEndpoints.appointmentEndpoint,
            location: analysis.apiEndpoints.locationEndpoint,
            service: analysis.apiEndpoints.serviceEndpoint
          }
        },
        selectors: analysis.selectors,
        validation: analysis.validationRules,
        metadata: analysis.metadata
      };

      this.loggingService.info('Updating configuration with Langchain analysis', { config });
      
      // TODO: Implement configuration update logic
      // await this.configService.set('BOOKING_CONFIG', config);
    } catch (error) {
      this.loggingService.error('Failed to update configuration', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }
} 