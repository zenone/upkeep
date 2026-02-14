/**
 * Utility functions for formatting, sanitization, and logging
 */

// Debug mode - set to false for production
const DEBUG_MODE = false;

/**
 * Debug logger - only logs when DEBUG_MODE is true
 * Use this instead of console.log for development debugging
 */
export function debug(...args: unknown[]): void {
  if (DEBUG_MODE) {
    console.log('[DEBUG]', ...args);
  }
}

/**
 * Error logger - always logs errors
 */
export function logError(message: string, error?: unknown): void {
  console.error(`[Upkeep Error] ${message}`, error ?? '');
}

/**
 * Warning logger - for non-critical issues
 */
export function logWarn(message: string, ...args: unknown[]): void {
  console.warn(`[Upkeep] ${message}`, ...args);
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration in seconds to human-readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Format time remaining
 */
export function formatTimeRemaining(seconds: number): string {
  if (seconds < 60) {
    return Math.round(seconds) + 's';
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Escape HTML to prevent XSS
 * WARNING: Only use for element text content, not for attributes
 */
export function escapeHtml(str: string): string {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Handle search key events
 */
export function handleSearchKey(event: KeyboardEvent, searchInputId: string, searchFunction: () => void): void {
  if (event.key === 'Enter') {
    searchFunction();
  } else if (event.key === 'Escape') {
    const searchInput = document.getElementById(searchInputId) as HTMLInputElement;
    if (searchInput) {
      searchInput.value = '';
      searchFunction();
    }
  }
}
