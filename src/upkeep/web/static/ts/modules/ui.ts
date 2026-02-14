/**
 * UI utilities: theme, notifications, loading, modals
 */

import type { ToastType, TabName } from '../types';

// ============================================================================
// Theme Management
// ============================================================================

export function initTheme(): void {
  const savedTheme = localStorage.getItem('theme') || 'system';
  applyTheme(savedTheme);

  // Listen for system theme changes when in system mode
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const currentTheme = localStorage.getItem('theme') || 'system';
    if (currentTheme === 'system') {
      applyTheme('system');
    }
  });
}

export function toggleTheme(): void {
  // Cycle through: light → dark → system → light
  const currentTheme = localStorage.getItem('theme') || 'system';
  let newTheme: string;

  if (currentTheme === 'light') {
    newTheme = 'dark';
  } else if (currentTheme === 'dark') {
    newTheme = 'system';
  } else {
    newTheme = 'light';
  }

  applyTheme(newTheme);
  localStorage.setItem('theme', newTheme);
}

function applyTheme(theme: string): void {
  // If system theme, detect browser preference
  let actualTheme = theme;
  if (theme === 'system') {
    actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  document.documentElement.setAttribute('data-theme', actualTheme);
  const icon = document.getElementById('theme-icon');
  if (icon) {
    // Show icon based on theme mode
    if (theme === 'light') {
      icon.textContent = '☀️';
    } else if (theme === 'dark') {
      icon.textContent = '🌙';
    } else {
      icon.textContent = '🖥️';  // System mode
    }
  }
}

// ============================================================================
// Toast Notifications
// ============================================================================

export function showToast(message: string, type: ToastType = 'info', duration: number = 3000): void {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  const container = document.getElementById('toast-container');
  if (!container) {
    console.error('Toast container not found');
    return;
  }

  container.appendChild(toast);

  // Trigger animation
  setTimeout(() => toast.classList.add('show'), 10);

  // Auto-remove after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ============================================================================
// Loading Indicator
// ============================================================================

export function showLoading(message: string = 'Loading...'): void {
  const loading = document.getElementById('loading-indicator');
  const loadingMessage = document.getElementById('loading-message');
  if (loading) {
    loading.classList.add('active');
    if (loadingMessage) {
      loadingMessage.textContent = message;
    }
  }
}

export function hideLoading(): void {
  const loading = document.getElementById('loading-indicator');
  if (loading) {
    loading.classList.remove('active');
  }
}

// ============================================================================
// Progress Overlay Modal
// ============================================================================

let progressOverlayActive = false;
let progressCancelCallback: (() => void) | null = null;
let progressStartTime: number | null = null;

export function showProgressOverlay(title: string, total: number, cancelCallback: () => void): void {
  const overlay = document.getElementById('progress-overlay');
  const titleEl = document.getElementById('progress-title');
  const percentEl = document.getElementById('progress-percent');
  const currentEl = document.getElementById('progress-current');
  const barEl = document.getElementById('progress-bar');

  if (!overlay || !titleEl || !percentEl || !currentEl || !barEl) {
    console.error('Progress overlay elements not found');
    return;
  }

  titleEl.textContent = title;
  percentEl.textContent = '0%';
  currentEl.textContent = '0';
  const remainingEl = document.getElementById('progress-remaining');
  if (remainingEl) {
    remainingEl.textContent = '--';
  }
  barEl.style.width = '0%';

  overlay.classList.add('active');
  progressOverlayActive = true;
  progressCancelCallback = cancelCallback;
  progressStartTime = Date.now();

  // ESC key to close
  document.addEventListener('keydown', handleProgressEscape);
}

export function updateProgressOverlay(current: number, total: number, message: string = ''): void {
  if (!progressOverlayActive) return;

  const percent = Math.round((current / total) * 100);
  const percentEl = document.getElementById('progress-percent');
  const currentEl = document.getElementById('progress-current');
  const barEl = document.getElementById('progress-bar');
  const remainingEl = document.getElementById('progress-remaining');
  const messageEl = document.getElementById('progress-message');

  if (!percentEl || !currentEl || !barEl) return;

  // Animate values
  const currentPercent = parseInt(percentEl.textContent || '0');
  animateValue(percentEl, currentPercent, percent, 200, 0, '%');
  currentEl.textContent = String(current);
  barEl.style.width = percent + '%';

  // Calculate time remaining
  if (current > 0 && progressStartTime && remainingEl) {
    const elapsed = (Date.now() - progressStartTime) / 1000; // seconds
    const rate = current / elapsed; // items per second
    const remaining = total - current;
    const eta = remaining / rate; // seconds

    if (eta < 60) {
      remainingEl.textContent = Math.round(eta) + 's';
    } else {
      const minutes = Math.floor(eta / 60);
      const seconds = Math.round(eta % 60);
      remainingEl.textContent = `${minutes}m ${seconds}s`;
    }
  }

  if (message && messageEl) {
    messageEl.textContent = message;
  }
}

export function hideProgressOverlay(): void {
  const overlay = document.getElementById('progress-overlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
  progressOverlayActive = false;
  progressCancelCallback = null;
  progressStartTime = null;
  document.removeEventListener('keydown', handleProgressEscape);
}

export function cancelProgress(): void {
  if (progressCancelCallback) {
    progressCancelCallback();
  }
  hideProgressOverlay();
  showToast('Operation cancelled', 'warning');
}

function handleProgressEscape(e: KeyboardEvent): void {
  if (e.key === 'Escape' && progressOverlayActive) {
    cancelProgress();
  }
}

// ============================================================================
// Value Animation
// ============================================================================

/**
 * Animate a number from old value to new value
 */
export function animateValue(
  element: HTMLElement,
  start: number,
  end: number,
  duration: number = 300,
  decimals: number = 1,
  suffix: string = ''
): void {
  const startTime = performance.now();
  const delta = end - start;

  function update(currentTime: number): void {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const current = start + (delta * easeProgress);

    element.textContent = current.toFixed(decimals) + suffix;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

// ============================================================================
// System Configuration
// ============================================================================

export async function reloadScripts(): Promise<void> {
  const btn = document.getElementById('reload-scripts-btn') as HTMLButtonElement;
  const statusEl = document.getElementById('reload-scripts-status');

  if (!btn || !statusEl) return;

  // Disable button and show loading state
  btn.disabled = true;
  btn.textContent = '⏳ Reloading...';
  statusEl.textContent = 'Copying updated scripts to system location...';
  statusEl.style.color = 'var(--text-secondary)';

  try {
    const response = await fetch('/api/system/reload-scripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reload scripts');
    }

    const result = await response.json();

    // Success
    btn.textContent = '✓ Reloaded';
    statusEl.textContent = result.message || 'Scripts reloaded successfully. Changes will take effect immediately.';
    statusEl.style.color = 'var(--success)';
    showToast('Scripts reloaded successfully', 'success');

    // Reset button after 3 seconds
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '🔄 Reload Scripts';
      statusEl.textContent = '';
    }, 3000);

  } catch (error) {
    // Error
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    btn.textContent = '✗ Failed';
    statusEl.textContent = `Error: ${errorMessage}`;
    statusEl.style.color = 'var(--danger)';
    showToast(`Failed to reload scripts: ${errorMessage}`, 'error');

    // Reset button after 5 seconds
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '🔄 Reload Scripts';
    }, 5000);
  }
}

// ============================================================================
// Settings Management
// ============================================================================

// Dashboard refresh interval ID (for clearing/resetting)
let dashboardRefreshInterval: ReturnType<typeof setInterval> | null = null;
let processRefreshInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Set theme explicitly (called from settings panel)
 */
export function setTheme(theme: string): void {
  applyTheme(theme);
  localStorage.setItem('theme', theme);
  updateThemeSelector(theme);
  showToast(`Theme set to ${theme}`, 'success', 2000);
}

/**
 * Update theme selector UI to show active selection
 */
function updateThemeSelector(activeTheme: string): void {
  const selector = document.getElementById('theme-selector');
  if (!selector) return;

  selector.querySelectorAll('.theme-option').forEach(btn => {
    const btnTheme = btn.getAttribute('data-theme');
    if (btnTheme === activeTheme) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

/**
 * Toggle auto-refresh on/off
 */
export function toggleAutoRefresh(enabled: boolean): void {
  localStorage.setItem('autoRefresh', String(enabled));

  if (enabled) {
    const interval = parseInt(localStorage.getItem('refreshInterval') || '10', 10);
    startAutoRefresh(interval);
    showToast('Auto-refresh enabled', 'success', 2000);
  } else {
    stopAutoRefresh();
    showToast('Auto-refresh disabled', 'info', 2000);
  }
}

/**
 * Set refresh interval (in seconds)
 */
export function setRefreshInterval(seconds: number): void {
  localStorage.setItem('refreshInterval', String(seconds));

  // Update UI
  const selector = document.getElementById('interval-selector');
  if (selector) {
    selector.querySelectorAll('.interval-option').forEach(btn => {
      const btnInterval = parseInt(btn.getAttribute('data-interval') || '0', 10);
      if (btnInterval === seconds) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Restart auto-refresh if enabled
  const autoRefresh = localStorage.getItem('autoRefresh') !== 'false';
  if (autoRefresh) {
    startAutoRefresh(seconds);
  }

  showToast(`Refresh interval set to ${seconds}s`, 'success', 2000);
}

/**
 * Start auto-refresh with given interval
 */
function startAutoRefresh(seconds: number): void {
  stopAutoRefresh(); // Clear existing intervals

  const ms = seconds * 1000;

  dashboardRefreshInterval = setInterval(() => {
    const dashboardTab = document.getElementById('dashboard');
    if (dashboardTab && dashboardTab.classList.contains('active')) {
      const loadSystemInfo = (window as any).loadSystemInfo;
      const loadHealthScore = (window as any).loadHealthScore;
      if (loadSystemInfo) loadSystemInfo();
      if (loadHealthScore) loadHealthScore();
    }
  }, ms);

  // Processes refresh at 2x the interval (minimum 10s)
  const processMs = Math.max(ms * 2, 10000);
  processRefreshInterval = setInterval(() => {
    const dashboardTab = document.getElementById('dashboard');
    if (dashboardTab && dashboardTab.classList.contains('active')) {
      const loadTopProcesses = (window as any).loadTopProcesses;
      if (loadTopProcesses) loadTopProcesses();
    }
  }, processMs);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh(): void {
  if (dashboardRefreshInterval) {
    clearInterval(dashboardRefreshInterval);
    dashboardRefreshInterval = null;
  }
  if (processRefreshInterval) {
    clearInterval(processRefreshInterval);
    processRefreshInterval = null;
  }
}

/**
 * Toggle default preview mode for maintenance
 */
export function togglePreviewMode(enabled: boolean): void {
  localStorage.setItem('defaultPreviewMode', String(enabled));
  showToast(enabled ? 'Preview mode enabled by default' : 'Preview mode disabled', 'info', 2000);
}

/**
 * Toggle confirmation dialogs
 */
export function toggleConfirmations(enabled: boolean): void {
  localStorage.setItem('requireConfirmation', String(enabled));
  showToast(enabled ? 'Confirmations enabled' : 'Confirmations disabled', 'info', 2000);
}

/**
 * Get whether preview mode is default
 */
export function isDefaultPreviewMode(): boolean {
  return localStorage.getItem('defaultPreviewMode') === 'true';
}

/**
 * Get whether confirmations are required
 */
export function requiresConfirmation(): boolean {
  return localStorage.getItem('requireConfirmation') !== 'false';
}

/**
 * Initialize settings panel with saved values
 */
export function initSettings(): void {
  // Theme selector
  const savedTheme = localStorage.getItem('theme') || 'system';
  updateThemeSelector(savedTheme);

  // Auto-refresh toggle
  const autoRefresh = localStorage.getItem('autoRefresh') !== 'false';
  const autoRefreshToggle = document.getElementById('auto-refresh-toggle') as HTMLInputElement;
  if (autoRefreshToggle) {
    autoRefreshToggle.checked = autoRefresh;
  }

  // Refresh interval selector
  const interval = parseInt(localStorage.getItem('refreshInterval') || '10', 10);
  const intervalSelector = document.getElementById('interval-selector');
  if (intervalSelector) {
    intervalSelector.querySelectorAll('.interval-option').forEach(btn => {
      const btnInterval = parseInt(btn.getAttribute('data-interval') || '0', 10);
      if (btnInterval === interval) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Preview mode toggle
  const previewMode = localStorage.getItem('defaultPreviewMode') === 'true';
  const previewToggle = document.getElementById('preview-mode-toggle') as HTMLInputElement;
  if (previewToggle) {
    previewToggle.checked = previewMode;
  }

  // Confirmations toggle
  const confirmations = localStorage.getItem('requireConfirmation') !== 'false';
  const confirmToggle = document.getElementById('confirm-toggle') as HTMLInputElement;
  if (confirmToggle) {
    confirmToggle.checked = confirmations;
  }

  // Load about info
  loadAboutInfo();

  // Start auto-refresh if enabled
  if (autoRefresh) {
    startAutoRefresh(interval);
  }
}

/**
 * Load about section info (version, counts)
 */
async function loadAboutInfo(): Promise<void> {
  const versionEl = document.getElementById('app-version');
  const opsCountEl = document.getElementById('ops-count');
  const schedulesCountEl = document.getElementById('schedules-count');

  // Get version from meta tag
  const versionMeta = document.querySelector('meta[name="app-version"]');
  if (versionEl && versionMeta) {
    versionEl.textContent = versionMeta.getAttribute('content') || '--';
  }

  // Get operations count
  try {
    const opsResponse = await fetch('/api/maintenance/operations');
    if (opsResponse.ok && opsCountEl) {
      const data = await opsResponse.json();
      opsCountEl.textContent = String(data.operations?.length || 0);
    }
  } catch {
    // Ignore errors
  }

  // Get schedules count
  try {
    const schedResponse = await fetch('/api/schedules');
    if (schedResponse.ok && schedulesCountEl) {
      const data = await schedResponse.json();
      schedulesCountEl.textContent = String(data.schedules?.length || 0);
    }
  } catch {
    // Ignore errors
  }
}

/**
 * Show keyboard shortcuts modal
 */
export function showKeyboardShortcuts(): void {
  // Trigger the existing shortcuts modal if available
  const event = new KeyboardEvent('keydown', { key: '?' });
  document.dispatchEvent(event);
}

// ============================================================================
// Tab Switching
// ============================================================================

export function switchTab(tabName: TabName): void {
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.tabs button').forEach(btn => btn.classList.remove('active'));

  const tabContent = document.getElementById(tabName);
  if (tabContent) {
    tabContent.classList.add('active');
  }

  // Find and activate the corresponding tab button
  const tabButtons = document.querySelectorAll('.tabs button');
  tabButtons.forEach(btn => {
    if (btn.textContent?.toLowerCase().includes(tabName)) {
      btn.classList.add('active');
    }
  });

  // Load data for the tab
  if (tabName === 'dashboard') {
    // Load dashboard data
    const loadSystemInfo = (window as any).loadSystemInfo;
    if (loadSystemInfo) loadSystemInfo();
  } else if (tabName === 'maintenance') {
    // Load operations
    const loadOperations = (window as any).loadOperations;
    if (loadOperations) loadOperations();
  } else if (tabName === 'schedule') {
    // Initialize schedule tab
    const onScheduleTabShow = (window as any).onScheduleTabShow;
    if (onScheduleTabShow) onScheduleTabShow();
  }
}
