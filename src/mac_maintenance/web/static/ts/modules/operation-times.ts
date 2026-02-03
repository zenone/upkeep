/**
 * Operation Time Tracking
 *
 * Tracks historical execution times for maintenance operations
 * to provide accurate ETA calculations.
 */

interface OperationTimeData {
  runs: number[];  // Last N run times in seconds
  average: number; // Average of runs
}

interface OperationTimesStorage {
  [operationId: string]: OperationTimeData;
}

const STORAGE_KEY = 'mac-maintenance-operation-times';
const MAX_STORED_RUNS = 5;  // Keep last 5 runs for rolling average
const DEFAULT_DURATION = 30; // Default 30 seconds if no history

/**
 * Load operation times from localStorage
 */
export function loadOperationTimes(): OperationTimesStorage {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return {};
    return JSON.parse(data);
  } catch (error) {
    console.error('Failed to load operation times:', error);
    return {};
  }
}

/**
 * Save operation times to localStorage
 */
function saveOperationTimes(times: OperationTimesStorage): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(times));
  } catch (error) {
    console.error('Failed to save operation times:', error);
  }
}

/**
 * Record operation duration
 */
export function recordOperationTime(operationId: string, durationSeconds: number): void {
  const times = loadOperationTimes();

  // Get existing data or create new
  const data = times[operationId] || { runs: [], average: 0 };

  // Add new duration
  data.runs.push(Math.round(durationSeconds));

  // Keep only last N runs
  if (data.runs.length > MAX_STORED_RUNS) {
    data.runs = data.runs.slice(-MAX_STORED_RUNS);
  }

  // Calculate average (round to 2 decimals for stable display/testing)
  const avg = data.runs.reduce((sum, time) => sum + time, 0) / data.runs.length;
  data.average = Math.round(avg * 100) / 100;

  times[operationId] = data;
  saveOperationTimes(times);
}

/**
 * Get average duration for an operation
 */
export function getAverageDuration(operationId: string): number {
  const times = loadOperationTimes();
  const data = times[operationId];

  if (!data || data.runs.length === 0) {
    return DEFAULT_DURATION;
  }

  return data.average;
}

/**
 * Get median duration for an operation (more resistant to outliers than average)
 */
export function getMedianDuration(operationId: string): number | null {
  const times = loadOperationTimes();
  const data = times[operationId];

  if (!data || data.runs.length === 0) {
    return null;  // No data available
  }

  // Sort runs to find median
  const sorted = [...data.runs].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 0) {
    // Even number: average of two middle values
    return (sorted[mid - 1] + sorted[mid]) / 2;
  } else {
    // Odd number: middle value
    return sorted[mid];
  }
}

/**
 * Get formatted typical duration string for display
 * Returns null if no historical data exists
 */
export function getTypicalDurationDisplay(operationId: string): string | null {
  const median = getMedianDuration(operationId);

  if (median === null) {
    return null;  // No data - don't show anything
  }

  // Format as human-readable duration
  if (median < 60) {
    return `${Math.round(median)}s`;
  } else if (median < 3600) {
    const minutes = Math.floor(median / 60);
    const seconds = Math.round(median % 60);
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
  } else {
    const hours = Math.floor(median / 3600);
    const minutes = Math.round((median % 3600) / 60);
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }
}

/**
 * Calculate ETA for remaining operations
 */
export function calculateETA(
  remainingOperationIds: string[],
  currentOperationId: string | null,
  currentOperationProgress: number
): number {
  let eta = 0;

  // Add time for remaining operations (not yet started)
  for (const opId of remainingOperationIds) {
    eta += getAverageDuration(opId);
  }

  // Add remaining time for current operation
  if (currentOperationId) {
    const avgDuration = getAverageDuration(currentOperationId);

    // Defensive: clamp progress to [0, 1] so weird UI states don't inflate ETA
    const progress = Math.max(0, Math.min(1, currentOperationProgress));
    const remainingProgress = 1 - progress;

    eta += avgDuration * remainingProgress;
  }

  return Math.round(eta);
}

/**
 * Get historical data for an operation (for debugging/display)
 */
export function getOperationHistory(operationId: string): OperationTimeData | null {
  const times = loadOperationTimes();
  return times[operationId] || null;
}

/**
 * Clear all historical data (for testing/reset)
 */
export function clearOperationTimes(): void {
  localStorage.removeItem(STORAGE_KEY);
}
