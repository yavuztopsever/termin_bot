/**
 * Represents a unique identifier for an AI analysis
 */
export class AnalysisId {
  constructor(private readonly value: string) {
    if (!value) {
      throw new Error('AnalysisId cannot be empty');
    }
  }

  toString(): string {
    return this.value;
  }
}

/**
 * Represents a confidence score between 0 and 1
 */
export class ConfidenceScore {
  constructor(private readonly value: number) {
    if (value < 0 || value > 1) {
      throw new Error('ConfidenceScore must be between 0 and 1');
    }
  }

  toNumber(): number {
    return this.value;
  }
}

/**
 * Represents a page element analyzed by AI
 */
export interface PageElement {
  selector: string;
  type: string;
  purpose: string;
  required: boolean;
  validationRules?: string[];
  errorStates?: string[];
  dynamicBehavior?: string[];
  accessibility?: string[];
}

/**
 * Represents the complete AI analysis of a page or element
 */
export interface AIAnalysis {
  id: AnalysisId;
  elements: PageElement[];
  timestamp: Date;
  metadata: {
    mainPurpose: string;
    interactiveElements: string[];
    formFields: string[];
    bookingElements: string[];
    errorStates: string[];
    dynamicContent: string[];
    navigationPaths: string[];
    accessibility: string[];
  };
} 