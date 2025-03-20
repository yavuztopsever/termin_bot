import { z } from 'zod';

export const ButtonElementSchema = z.object({
  text: z.string(),
  type: z.string(),
  action: z.string().optional(),
  selector: z.string().optional(),
  position: z.object({
    x: z.number(),
    y: z.number(),
  }).optional(),
  isEnabled: z.boolean().optional(),
  isVisible: z.boolean().optional(),
  attributes: z.record(z.string()).optional(),
});

export type ButtonElement = z.infer<typeof ButtonElementSchema>;

export const PageActionSchema = z.object({
  type: z.enum(['click', 'input', 'select', 'scroll', 'wait', 'navigate']),
  target: z.string(),
  value: z.string().optional(),
  priority: z.number().positive(),
  timeout: z.number().positive().optional(),
  retryCount: z.number().nonnegative().optional(),
  retryDelay: z.number().positive().optional(),
  waitForSelector: z.string().optional(),
  waitForTimeout: z.number().positive().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type PageAction = z.infer<typeof PageActionSchema>;

export interface AIAnalyzer {
  analyzePage(url: string, options?: {
    waitForSelector?: string;
    timeout?: number;
  }): Promise<{
    buttons: ButtonElement[];
    forms: Array<{
      id: string;
      action: string;
      method: string;
      fields: Array<{
        name: string;
        type: string;
        value?: string;
        required: boolean;
        disabled: boolean;
        readonly: boolean;
      }>;
    }>;
    links: Array<{
      text: string;
      href: string;
      isEnabled: boolean;
      isVisible: boolean;
    }>;
  }>;
  
  analyzeElement(selector: string, options?: {
    waitForVisible?: boolean;
    timeout?: number;
  }): Promise<{
    type: string;
    text?: string;
    attributes: Record<string, string>;
    position?: {
      x: number;
      y: number;
    };
    isVisible: boolean;
    isEnabled: boolean;
    isSelected: boolean;
  }>;
  
  generateActions(goal: string, context: {
    currentUrl: string;
    availableElements: ButtonElement[];
    previousActions: PageAction[];
  }): Promise<PageAction[]>;
  
  validateAction(action: PageAction, context: {
    currentUrl: string;
    availableElements: ButtonElement[];
  }): Promise<boolean>;
}

export interface AIConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
  stop: string[];
  timeout: number;
  retryConfig: {
    maxRetries: number;
    retryDelay: number;
  };
  validationConfig: {
    strictMode: boolean;
    validateSelectors: boolean;
    validateActions: boolean;
  };
}

export interface PageAnalysis {
  elements: PageElement[];
  content: string;
  structure: PageStructure;
  actions: PageAction[];
}

export interface PageElement {
  type: string;
  content: string;
  location: ElementLocation;
  attributes: Record<string, string>;
}

export interface ElementLocation {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PageStructure {
  title?: string;
  headings: string[];
  forms: FormElement[];
  buttons: ButtonElement[];
  links: LinkElement[];
}

export interface FormElement {
  id: string;
  type: string;
  fields: FormField[];
}

export interface FormField {
  name: string;
  type: string;
  required: boolean;
  value?: string;
}

export interface LinkElement {
  text: string;
  href: string;
  target?: string;
} 