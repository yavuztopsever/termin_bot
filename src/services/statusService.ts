import { EventEmitter } from 'events';
import { logger } from './loggingService';

/**
 * Enum representing possible appointment status states
 */
export enum AppointmentStatus {
  CHECKING = 'CHECKING',
  API_ERROR = 'API_ERROR',
  NO_APPOINTMENTS = 'NO_APPOINTMENTS',
  APPOINTMENT_FOUND = 'APPOINTMENT_FOUND',
  BOOKING_IN_PROGRESS = 'BOOKING_IN_PROGRESS',
  BOOKING_FAILED = 'BOOKING_FAILED',
  BOOKING_SUCCESSFUL = 'BOOKING_SUCCESSFUL'
}

/**
 * Interface for status change events
 */
export interface StatusChangeEvent {
  previousStatus: AppointmentStatus;
  newStatus: AppointmentStatus;
  timestamp: Date;
  details?: Record<string, any>;
}

/**
 * Service for tracking and managing appointment status changes
 */
export class StatusService {
  private currentStatus: AppointmentStatus = AppointmentStatus.CHECKING;
  private lastStatusChange: StatusChangeEvent | null = null;
  private eventEmitter: EventEmitter;

  constructor() {
    this.eventEmitter = new EventEmitter();
    // Increase max listeners to prevent memory leak warnings
    this.eventEmitter.setMaxListeners(20);
  }

  /**
   * Get the current appointment status
   */
  getCurrentStatus(): AppointmentStatus {
    return this.currentStatus;
  }

  /**
   * Get the last status change event
   */
  getLastStatusChange(): StatusChangeEvent | null {
    return this.lastStatusChange;
  }

  /**
   * Update the current status
   * @param newStatus The new status to set
   * @param details Optional details about the status change
   */
  updateStatus(newStatus: AppointmentStatus, details?: Record<string, any>): void {
    const previousStatus = this.currentStatus;
    
    // Don't emit if status hasn't changed
    if (previousStatus === newStatus) {
      return;
    }

    this.currentStatus = newStatus;
    
    const event: StatusChangeEvent = {
      previousStatus,
      newStatus,
      timestamp: new Date(),
      details
    };

    this.lastStatusChange = event;
    
    logger.info(`Status changed from ${previousStatus} to ${newStatus}${details ? `: ${JSON.stringify(details)}` : ''}`);
    
    this.eventEmitter.emit('statusChange', event);
  }

  /**
   * Add a listener for status changes
   * @param listener The callback function to be called when status changes
   */
  onStatusChange(listener: (event: StatusChangeEvent) => void): void {
    this.eventEmitter.on('statusChange', listener);
  }

  /**
   * Remove a status change listener
   * @param listener The listener function to remove
   */
  removeStatusChangeListener(listener: (event: StatusChangeEvent) => void): void {
    this.eventEmitter.removeListener('statusChange', listener);
  }
}

// Export a singleton instance
export const statusService = new StatusService(); 