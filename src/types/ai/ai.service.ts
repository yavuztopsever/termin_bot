import { AIAnalysis } from './ai-analysis.entity';

export interface AIService {
  analyzePage(html: string): Promise<AIAnalysis>;
  analyzeElement(selector: string, html: string): Promise<AIAnalysis>;
  extractText(html: string): Promise<string>;
  classifyContent(content: string): Promise<string>;
  generateResponse(prompt: string): Promise<string>;
  validateInput(input: string): Promise<boolean>;
} 