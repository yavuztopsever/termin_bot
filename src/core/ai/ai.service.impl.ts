import { Injectable } from '@nestjs/common';
import { ConfigService } from '../../config/config.service';
import { LoggingService } from '../../services/common/logging.service';
import { MonitoringService } from '../../services/monitoring/monitoring.service';
import { AIService } from './ai.service';
import { AIAnalysis, AnalysisId, PageElement } from '../../types/ai/ai-analysis.entity';
import { ChatOpenAI } from 'langchain/chat_models/openai';
import { HumanMessage, SystemMessage } from 'langchain/schema';
import { StructuredOutputParser } from 'langchain/output_parsers';
import { PromptTemplate } from 'langchain/prompts';
import { Document } from 'langchain/document';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { OpenAIEmbeddings } from 'langchain/embeddings/openai';
import { MemoryVectorStore } from 'langchain/vectorstores/memory';
import { RunnableSequence } from 'langchain/runnables';
import { StringOutputParser } from 'langchain/schema/output_parser';

@Injectable()
export class AIServiceImpl implements AIService {
  private readonly llm: ChatOpenAI;
  private readonly embeddings: OpenAIEmbeddings;
  private readonly vectorStore: MemoryVectorStore;
  private readonly textSplitter: RecursiveCharacterTextSplitter;

  constructor(
    private readonly configService: ConfigService,
    private readonly loggingService: LoggingService,
    private readonly monitoringService: MonitoringService,
  ) {
    // Initialize LangChain components
    this.llm = new ChatOpenAI({
      modelName: this.configService.get('ai.model'),
      temperature: this.configService.get('ai.temperature'),
      maxTokens: this.configService.get('ai.maxTokens'),
      openAIApiKey: this.configService.get('ai.apiKey'),
    });

    this.embeddings = new OpenAIEmbeddings({
      openAIApiKey: this.configService.get('ai.apiKey'),
    });

    this.vectorStore = new MemoryVectorStore(this.embeddings);
    this.textSplitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1000,
      chunkOverlap: 200,
    });
  }

  async analyzePage(html: string): Promise<AIAnalysis> {
    try {
      this.loggingService.info('Starting page analysis');
      
      // Split HTML into chunks for processing
      const docs = await this.textSplitter.createDocuments([html]);
      
      // Create analysis chain
      const analysisChain = RunnableSequence.from([
        {
          content: (input: { docs: Document[] }) => input.docs.map(doc => doc.pageContent).join('\n'),
          metadata: (input: { docs: Document[] }) => input.docs[0].metadata,
        },
        {
          prompt: PromptTemplate.fromTemplate(`
            Analyze the following webpage content and extract key information:
            {content}
            
            Provide a structured analysis including:
            1. Main purpose of the page
            2. Key interactive elements
            3. Form fields and their purposes
            4. Potential booking-related elements
            5. Any error states or warnings
            6. Dynamic content patterns
            7. Navigation paths
            8. Accessibility considerations
            
            Format the response as a structured JSON object.
          `),
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute analysis chain
      const result = await analysisChain.invoke({ docs });
      
      // Parse and validate the analysis result
      const parsedResult = JSON.parse(result);
      
      // Create AIAnalysis object
      const analysis: AIAnalysis = {
        id: new AnalysisId(crypto.randomUUID()),
        elements: [],
        timestamp: new Date(),
        metadata: parsedResult
      };
      
      this.loggingService.info('Page analysis completed successfully');
      this.monitoringService.recordMetric({
        name: 'ai_page_analysis_completed',
        value: 1,
        timestamp: new Date(),
      });
      
      return analysis;
    } catch (error) {
      this.loggingService.error('Failed to analyze page', { error });
      this.monitoringService.recordError('ai_page_analysis_failed', error);
      throw error;
    }
  }

  async analyzeElement(selector: string, html: string): Promise<AIAnalysis> {
    try {
      this.loggingService.info('Starting element analysis', { selector });
      
      // Create element analysis chain
      const analysisChain = RunnableSequence.from([
        {
          content: (input: { html: string; selector: string }) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(input.html, 'text/html');
            const element = doc.querySelector(input.selector);
            return element ? element.outerHTML : '';
          },
          selector: (input: { selector: string }) => input.selector,
        },
        {
          prompt: PromptTemplate.fromTemplate(`
            Analyze the following HTML element and provide detailed information:
            {content}
            
            Element selector: {selector}
            
            Provide a structured analysis including:
            1. Element type and purpose
            2. Input requirements and validation rules
            3. Expected user interactions
            4. Potential error states
            5. Accessibility considerations
            6. Dynamic behavior patterns
            
            Format the response as a structured JSON object.
          `),
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute analysis chain
      const result = await analysisChain.invoke({ html, selector });
      
      // Parse and validate the analysis result
      const parsedResult = JSON.parse(result);
      
      // Create AIAnalysis object
      const analysis: AIAnalysis = {
        id: new AnalysisId(crypto.randomUUID()),
        elements: [parsedResult as PageElement],
        timestamp: new Date(),
        metadata: {
          mainPurpose: parsedResult.purpose,
          interactiveElements: [selector],
          formFields: [],
          bookingElements: [],
          errorStates: parsedResult.errorStates || [],
          dynamicContent: parsedResult.dynamicBehavior || [],
          navigationPaths: [],
          accessibility: parsedResult.accessibility || []
        }
      };
      
      this.loggingService.info('Element analysis completed successfully', { selector });
      this.monitoringService.recordMetric({
        name: 'ai_element_analysis_completed',
        value: 1,
        timestamp: new Date(),
        tags: { selector },
      });
      
      return analysis;
    } catch (error) {
      this.loggingService.error('Failed to analyze element', { selector, error });
      this.monitoringService.recordError('ai_element_analysis_failed', error);
      throw error;
    }
  }

  async extractText(html: string): Promise<string> {
    try {
      this.loggingService.info('Starting text extraction');
      
      // Create text extraction chain
      const extractionChain = RunnableSequence.from([
        {
          content: (input: { html: string }) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(input.html, 'text/html');
            return doc.body.textContent || '';
          },
        },
        {
          prompt: PromptTemplate.fromTemplate(`
            Extract and clean the text content from the following HTML:
            {content}
            
            Remove any unnecessary whitespace, formatting, and special characters.
            Preserve important text structure and readability.
          `),
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute extraction chain
      const result = await extractionChain.invoke({ html });
      
      this.loggingService.info('Text extraction completed successfully');
      this.monitoringService.recordMetric({
        name: 'ai_text_extraction_completed',
        value: 1,
        timestamp: new Date(),
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to extract text', { error });
      this.monitoringService.recordError('ai_text_extraction_failed', error);
      throw error;
    }
  }

  async classifyContent(content: string): Promise<string> {
    try {
      this.loggingService.info('Starting content classification');
      
      // Create classification chain
      const classificationChain = RunnableSequence.from([
        {
          content: (input: { content: string }) => input.content,
        },
        {
          prompt: PromptTemplate.fromTemplate(`
            Classify the following content into one of these categories:
            - FORM: Contains input forms or fields
            - ERROR: Contains error messages or warnings
            - CALENDAR: Contains date/time selection elements
            - NAVIGATION: Contains navigation links or menus
            - CONFIRMATION: Contains confirmation or success messages
            - UNKNOWN: Does not fit into any other category
            
            Content: {content}
            
            Provide only the category name as the response.
          `),
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute classification chain
      const result = await classificationChain.invoke({ content });
      
      this.loggingService.info('Content classification completed successfully');
      this.monitoringService.recordMetric({
        name: 'ai_content_classification_completed',
        value: 1,
        timestamp: new Date(),
        tags: { category: result },
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to classify content', { error });
      this.monitoringService.recordError('ai_content_classification_failed', error);
      throw error;
    }
  }

  async generateResponse(prompt: string): Promise<string> {
    try {
      this.loggingService.info('Starting response generation');
      
      // Create response generation chain
      const responseChain = RunnableSequence.from([
        {
          prompt: (input: { prompt: string }) => input.prompt,
        },
        {
          messages: (input: { prompt: string }) => [
            new SystemMessage('You are a helpful AI assistant.'),
            new HumanMessage(input.prompt),
          ],
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute response generation chain
      const result = await responseChain.invoke({ prompt });
      
      this.loggingService.info('Response generation completed successfully');
      this.monitoringService.recordMetric({
        name: 'ai_response_generation_completed',
        value: 1,
        timestamp: new Date(),
      });
      
      return result;
    } catch (error) {
      this.loggingService.error('Failed to generate response', { error });
      this.monitoringService.recordError('ai_response_generation_failed', error);
      throw error;
    }
  }

  async validateInput(input: string): Promise<boolean> {
    try {
      this.loggingService.info('Starting input validation');
      
      // Create validation chain
      const validationChain = RunnableSequence.from([
        {
          input: (input: { input: string }) => input.input,
        },
        {
          prompt: PromptTemplate.fromTemplate(`
            Validate the following input and determine if it is valid:
            {input}
            
            Consider:
            1. Required format
            2. Required fields
            3. Data types
            4. Length constraints
            5. Special characters
            
            Respond with either "VALID" or "INVALID".
          `),
        },
        this.llm,
        new StringOutputParser(),
      ]);

      // Execute validation chain
      const result = await validationChain.invoke({ input });
      
      const isValid = result.trim().toUpperCase() === 'VALID';
      
      this.loggingService.info('Input validation completed successfully', { isValid });
      this.monitoringService.recordMetric({
        name: 'ai_input_validation_completed',
        value: 1,
        timestamp: new Date(),
        tags: { isValid: isValid.toString() },
      });
      
      return isValid;
    } catch (error) {
      this.loggingService.error('Failed to validate input', { error });
      this.monitoringService.recordError('ai_input_validation_failed', error);
      throw error;
    }
  }
} 