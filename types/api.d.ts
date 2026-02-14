/**
 * Type definitions for Mac Maintenance API
 *
 * These types provide compile-time type checking for JavaScript code
 * using JSDoc annotations and TypeScript's --checkJs mode.
 *
 * Usage in JavaScript:
 *
 * /** @type {MaintenanceOperation} *\/
 * const operation = await fetchOperation();
 */

// ========================================
// Maintenance API Types
// ========================================

/**
 * WHY section - Problems this operation solves
 */
export interface OperationWhy {
  context: string;
  problems: Array<{
    symptom: string;
    description: string;
  }>;
}

/**
 * WHAT section - Expected outcomes and timeline
 */
export interface OperationWhat {
  outcomes: Array<{
    type: 'positive' | 'warning' | 'temporary' | 'info';
    description: string;
  }>;
  timeline: string;
}

/**
 * Maintenance Operation
 */
export interface MaintenanceOperation {
  id: string;
  name: string;
  description: string;
  category: string;
  recommended: boolean;
  requires_sudo: boolean;
  safe?: boolean;

  // WHY/WHAT guidance
  why?: OperationWhy | null;
  what?: OperationWhat | null;
  when_to_run?: string[] | null;
  safety?: 'low-risk' | 'medium-risk' | 'high-risk' | null;
  guidance?: string | null;
}

/**
 * API Response: List of maintenance operations
 */
export interface OperationsListResponse {
  success: boolean;
  operations: MaintenanceOperation[];
  timestamp: string;
}

/**
 * API Response: Last run information
 */
export interface LastRunResponse {
  success: boolean;
  last_run: string | null;
  operations_count: number | null;
  duration_seconds: number | null;
  timestamp: string;
}

/**
 * Server-Sent Event types for operation streaming
 */
export type OperationEventType =
  | 'start'
  | 'operation_start'
  | 'output'
  | 'operation_complete'
  | 'operation_skipped'
  | 'operation_error'
  | 'summary'
  | 'complete'
  | 'error'
  | 'cancelled';

/**
 * Disk stats for before/after comparison
 */
export interface DiskStats {
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  total_gb: number;
  used_gb: number;
  free_gb: number;
}

/**
 * Operation Event (SSE)
 */
export interface OperationEvent {
  type: OperationEventType;
  operation_id?: string;
  operation_name?: string;
  progress?: string;
  stream?: 'stdout' | 'stderr';
  line?: string;
  success?: boolean;
  returncode?: number;
  message?: string;
  total?: number;
  successful?: number;
  failed?: number;
  // Disk stats for before/after comparison (available in 'start' and 'summary' events)
  disk_before?: DiskStats;
  disk_after?: DiskStats;
  space_recovered_bytes?: number;
  space_recovered_gb?: number;
  space_recovered_display?: string;
  timestamp: string;
}

// ========================================
// System API Types
// ========================================

/**
 * System information
 */
export interface SystemInfo {
  os: string;
  os_version: string;
  hostname: string;
  architecture: string;
  python_version: string;
  uptime_seconds: number;
  uptime_formatted: string;
  boot_time: string;
}

/**
 * System health metrics
 */
export interface SystemHealth {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  load_average: [number, number, number];
  cpu_count: number;
  memory_total_gb: number;
  memory_available_gb: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_free_gb: number;
  swap_total_gb: number;
  swap_used_gb: number;
  network_sent_mb: number;
  network_recv_mb: number;
  timestamp: string;
}

/**
 * Process information
 */
export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
  memory_mb: number;
  status: string;
  username: string;
}

/**
 * API Response: System info
 */
export interface SystemInfoResponse {
  success: boolean;
  system: SystemInfo;
  timestamp: string;
}

/**
 * API Response: System health
 */
export interface SystemHealthResponse {
  success: boolean;
  health: SystemHealth;
  timestamp: string;
}

/**
 * API Response: Sparkline data
 */
export interface SparklineResponse {
  success: boolean;
  data: number[];
  min: number;
  max: number;
  avg: number;
  latest: number;
  timestamp: string;
}

/**
 * API Response: Top processes
 */
export interface ProcessesResponse {
  success: boolean;
  processes: ProcessInfo[];
  total_count: number;
  timestamp: string;
}

// ========================================
// Storage API Types
// ========================================

/**
 * Storage entry (file or directory)
 */
export interface StorageEntry {
  path: string;
  size: number;
  size_gb: number;
  is_dir: boolean;
  percentage: number;
}

/**
 * Category breakdown
 */
export interface CategoryBreakdown {
  size: number;
  size_gb: number;
  percentage: number;
}

/**
 * API Response: Storage analysis
 */
export interface StorageAnalyzeResponse {
  success: boolean;
  path: string;
  total_size_gb: number;
  total_size_bytes: number;
  file_count: number;
  dir_count: number;
  largest_entries: StorageEntry[];
  category_sizes: Record<string, number>;  // category -> bytes
  error?: string;
}

/**
 * API Response: Delete operation
 */
export interface DeleteResponse {
  success: boolean;
  deleted: number;
  failed: number;
  errors: string[];
  space_freed_gb: number;
  timestamp: string;
}

// ========================================
// Schedule API Types
// ========================================

/**
 * Schedule for automated maintenance
 */
export interface Schedule {
  id: string;
  name: string;
  description: string;
  operations: string[];
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
  time_of_day: string;
  days_of_week?: string[] | null;
  day_of_month?: number | null;
  enabled: boolean;

  // Behavior
  wake_mac?: boolean;
  notify?: boolean;

  created_at: string;
  updated_at: string;
  last_run?: string | null;
  next_run?: string | null;
}

/**
 * Schedule create request
 */
export interface ScheduleCreate {
  name: string;
  description?: string;
  operations: string[];
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
  time_of_day: string;
  days_of_week?: string[] | null;
  day_of_month?: number | null;
  enabled?: boolean;
  wake_mac?: boolean;
  notify?: boolean;
}

/**
 * Schedule update request
 */
export interface ScheduleUpdate {
  name?: string;
  description?: string;
  operations?: string[];
  frequency?: 'daily' | 'weekly' | 'monthly' | 'custom';
  time_of_day?: string;
  days_of_week?: string[] | null;
  day_of_month?: number | null;
  enabled?: boolean;
  wake_mac?: boolean;
  notify?: boolean;
}

/**
 * API Response: Schedule list
 */
export interface ScheduleListResponse {
  success: boolean;
  schedules: Schedule[];
  count: number;
  timestamp: string;
}

/**
 * API Response: Single schedule
 */
export interface ScheduleResponse {
  success: boolean;
  schedule: Schedule;
  timestamp: string;
}

/**
 * API Response: Schedule deletion
 */
export interface ScheduleDeleteResponse {
  success: boolean;
  deleted_id: string;
  message: string;
  timestamp: string;
}

/**
 * API Response: Schedule toggle
 */
export interface ScheduleToggleResponse {
  success: boolean;
  schedule: Schedule;
  message: string;
  timestamp: string;
}

// ========================================
// Common Types
// ========================================

/**
 * Generic success response
 */
export interface SuccessResponse {
  success: true;
  message?: string;
  timestamp: string;
}

/**
 * Generic error response
 */
export interface ErrorResponse {
  success: false;
  error: string;
  detail?: string;
  timestamp: string;
}

/**
 * API Response (union of success/error)
 */
export type APIResponse<T = any> =
  | (SuccessResponse & T)
  | ErrorResponse;

// ========================================
// Utility Types
// ========================================

/**
 * Tab names in the application
 */
export type TabName = 'dashboard' | 'storage' | 'maintenance' | 'schedule' | 'about';

/**
 * Toast notification types
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Sort direction
 */
export type SortDirection = 'asc' | 'desc';

// ========================================
// Global Functions (for JSDoc)
// ========================================

/**
 * Show toast notification
 */
export function showToast(message: string, type?: ToastType, duration?: number): void;

/**
 * Show loading indicator
 */
export function showLoading(message: string): void;

/**
 * Hide loading indicator
 */
export function hideLoading(): void;

/**
 * Switch to a specific tab
 */
export function switchTab(tabName: TabName): void;

/**
 * Fetch API helper
 */
export function fetchAPI<T = any>(
  url: string,
  options?: RequestInit
): Promise<T>;

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number, decimals?: number): string;

/**
 * Format duration in seconds to human-readable string
 */
export function formatDuration(seconds: number): string;

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text: string): string;
