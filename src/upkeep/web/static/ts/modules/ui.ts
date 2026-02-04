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
