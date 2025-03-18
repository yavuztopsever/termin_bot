import fs from 'fs';
import path from 'path';

// Log levels
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR'
}

export class Logger {
  private static instance: Logger;
  private logDir: string;
  private logFile: string;
  
  private constructor() {
    this.logDir = path.join(process.cwd(), 'logs');
    
    // Create logs directory if it doesn't exist
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
    
    // Create a log file with the current date
    const date = new Date().toISOString().split('T')[0];
    this.logFile = path.join(this.logDir, `appointment-checker-${date}.log`);
  }
  
  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }
  
  private formatLogMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}] ${message}`;
  }
  
  private writeToLog(level: LogLevel, message: string): void {
    const formattedMessage = this.formatLogMessage(level, message);
    
    // Log to console
    switch (level) {
      case LogLevel.ERROR:
        console.error(formattedMessage);
        break;
      case LogLevel.WARN:
        console.warn(formattedMessage);
        break;
      case LogLevel.INFO:
      case LogLevel.DEBUG:
      default:
        console.log(formattedMessage);
        break;
    }
    
    // Write to log file
    fs.appendFileSync(this.logFile, formattedMessage + '\n');
  }
  
  public debug(message: string): void {
    this.writeToLog(LogLevel.DEBUG, message);
  }
  
  public info(message: string): void {
    this.writeToLog(LogLevel.INFO, message);
  }
  
  public warn(message: string): void {
    this.writeToLog(LogLevel.WARN, message);
  }
  
  public error(message: string, error?: Error): void {
    let errorMessage = message;
    
    if (error) {
      errorMessage += `: ${error.message}`;
      if (error.stack) {
        errorMessage += `\nStack trace: ${error.stack}`;
      }
    }
    
    this.writeToLog(LogLevel.ERROR, errorMessage);
  }
}

// Export a singleton instance
export const logger = Logger.getInstance();
