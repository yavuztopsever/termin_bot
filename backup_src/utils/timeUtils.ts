/**
 * Formats time remaining in milliseconds to seconds
 * @param milliseconds Time in milliseconds
 * @returns Formatted time in seconds
 */
export function formatTimeRemaining(milliseconds: number): string {
  return `${Math.ceil(milliseconds / 1000)}s`;
} 