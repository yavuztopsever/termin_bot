import { z } from 'zod';

export const PageAnalysisMetadataSchema = z.object({
  url: z.string().url(),
  timestamp: z.string().datetime(),
  duration: z.number().positive(),
  userAgent: z.string().optional(),
  ipAddress: z.string().ip().optional(),
  browser: z.string().optional(),
  os: z.string().optional(),
  device: z.string().optional(),
  screenResolution: z.string().optional(),
  language: z.string().optional(),
  referrer: z.string().url().optional(),
  customFields: z.record(z.unknown()).optional(),
});

export type PageAnalysisMetadata = z.infer<typeof PageAnalysisMetadataSchema>;

export const PageAnalysisResultSchema = z.object({
  success: z.boolean(),
  available: z.boolean(),
  nextAvailableDate: z.string().datetime().optional(),
  nextAvailableTime: z.string().optional(),
  error: z.string().optional(),
  metadata: PageAnalysisMetadataSchema,
  elements: z.array(z.object({
    type: z.string(),
    selector: z.string(),
    text: z.string().optional(),
    attributes: z.record(z.string()).optional(),
    position: z.object({
      x: z.number(),
      y: z.number(),
    }).optional(),
    isVisible: z.boolean().optional(),
    isEnabled: z.boolean().optional(),
    isSelected: z.boolean().optional(),
  })).optional(),
  forms: z.array(z.object({
    id: z.string().optional(),
    action: z.string().url().optional(),
    method: z.enum(['GET', 'POST', 'PUT', 'DELETE']).optional(),
    fields: z.array(z.object({
      name: z.string(),
      type: z.string(),
      value: z.string().optional(),
      required: z.boolean().optional(),
      disabled: z.boolean().optional(),
      readonly: z.boolean().optional(),
    })),
  })).optional(),
  buttons: z.array(z.object({
    text: z.string(),
    type: z.string(),
    action: z.string().optional(),
    isEnabled: z.boolean().optional(),
    isVisible: z.boolean().optional(),
    position: z.object({
      x: z.number(),
      y: z.number(),
    }).optional(),
  })).optional(),
  links: z.array(z.object({
    text: z.string(),
    href: z.string().url(),
    isEnabled: z.boolean().optional(),
    isVisible: z.boolean().optional(),
  })).optional(),
});

export type PageAnalysisResult = z.infer<typeof PageAnalysisResultSchema>;

export interface PageAnalyzer {
  analyze(url: string, options?: {
    waitForSelector?: string;
    timeout?: number;
    metadata?: Partial<PageAnalysisMetadata>;
  }): Promise<PageAnalysisResult>;
  
  analyzeElement(selector: string, options?: {
    waitForVisible?: boolean;
    timeout?: number;
  }): Promise<PageAnalysisResult>;
  
  analyzeForm(formSelector: string, options?: {
    waitForVisible?: boolean;
    timeout?: number;
  }): Promise<PageAnalysisResult>;
  
  analyzeButton(buttonSelector: string, options?: {
    waitForVisible?: boolean;
    timeout?: number;
  }): Promise<PageAnalysisResult>;
  
  analyzeLink(linkSelector: string, options?: {
    waitForVisible?: boolean;
    timeout?: number;
  }): Promise<PageAnalysisResult>;
}

export interface PageAnalyzerConfig {
  defaultTimeout: number;
  defaultWaitForSelector: string;
  userAgent: string;
  viewport: {
    width: number;
    height: number;
  };
  metadata: Partial<PageAnalysisMetadata>;
} 