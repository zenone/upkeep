/**
 * Maintenance module - Operations execution and progress tracking
 */

import type { MaintenanceOperation, OperationEvent } from '../types';
import { showToast } from './ui';
import { formatDuration } from './utils';
import { escapeHtml } from './utils';
import { recordOperationTime, calculateETA, getAverageDuration, getTypicalDurationDisplay, getMedianDuration } from './operation-times';

// ============================================================================
// Global State
// ============================================================================

export let runningOperations = false;
export let operationInvocationId = 0; // Track which invocation is current (prevents race conditions)
export let allOperations: MaintenanceOperation[] = [];

// Progress tracking
export let operationStartTime = 0;
export let batchStartTime = 0;  // Track when entire batch started
export let currentOperationIndex = 0;
export let totalOperations = 0;
export let operationTimes: number[] = [];
export let progressTimerInterval: number | null = null;
export let queueStatusInterval: number | null = null;
export let currentOperationId: string | null = null;
export let selectedOperationIds: string[] = [];  // Track which operations were selected

// Per-operation stats from server (last run + typical runtime)
let operationStats: Record<string, any> = {};

// ============================================================================
// Load Operations
// ============================================================================

/**
 * Load and display available maintenance operations
 */
export async function loadOperations(): Promise<void> {
  try {
    // Add cache-busting parameter to force fresh data
    const cacheBuster = Date.now();
    const response = await fetch(`/api/maintenance/operations?_=${cacheBuster}`);
    const data = await response.json();

    if (!data.operations || data.operations.length === 0) {
      const operationsDiv = document.getElementById('operations-list');
      if (operationsDiv) {
        operationsDiv.innerHTML = '<div class="error">No operations available</div>';
      }
      return;
    }

    allOperations = data.operations;

    console.log('=== WHY/WHAT DEBUG ===');
    console.log('Total operations loaded:', allOperations.length);
    console.log('First operation full data:', allOperations[0]);

    const opsWithData = allOperations.filter(op => op.why && op.what);
    const opsWithoutData = allOperations.filter(op => !op.why || !op.what);
    console.log(`Operations WITH why/what: ${opsWithData.length}`);
    console.log(`Operations WITHOUT why/what: ${opsWithoutData.length}`);
    if (opsWithoutData.length > 0) {
      console.log('Operations missing why/what:', opsWithoutData.map(op => op.id));
    }
    console.log('=== END DEBUG ===');

    // Sort by category
    allOperations.sort((a, b) => {
      if (a.category === b.category) {
        return a.name.localeCompare(b.name);
      }
      return a.category.localeCompare(b.category);
    });

    // Fetch per-operation last run data
    let operationsHistory: Record<string, any> = {};
    try {
      const lastRunResponse = await fetch('/api/maintenance/last-run');
      const lastRunData = await lastRunResponse.json();
      operationsHistory = lastRunData.operations || {};
      operationStats = operationsHistory;
    } catch (error) {
      console.warn('Could not fetch per-operation history:', error);
    }

    const html = allOperations.map(op => {
      const opHistory = operationsHistory[op.id];

      // Typical duration (server-provided preferred; fallback to localStorage)
      const typicalDuration = opHistory?.typical_display || getTypicalDurationDisplay(op.id);
      const durationHtml = typicalDuration
        ? ` | ⏱️ Typically <strong>${typicalDuration}</strong>`
        : '';

      let lastRunHtml = '';
      if (opHistory && opHistory.last_run_relative) {
        const statusIcon = opHistory.success ? '✓' : '✗';
        const statusColor = opHistory.success ? 'var(--success-color)' : 'var(--error-color)';
        lastRunHtml = `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          📅 Last run: <strong>${opHistory.last_run_relative}</strong> <span style="color: ${statusColor}">${statusIcon}</span>${durationHtml}
        </div>`;
      } else {
        const typicalFallback = durationHtml || ' | ⏱️ Typically <strong>—</strong> <span style="opacity:0.7;">(first run)</span>';
        lastRunHtml = `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          📅 Last run: <strong>Never run</strong>${durationHtml || typicalFallback}
        </div>`;
      }

      // Build WHY/WHAT accordion if data is available
      let whyWhatHtml = '';
      console.log(`Operation ${op.id}: has why=${!!op.why}, has what=${!!op.what}`);
      if (op.why && op.what) {
        let whenToRunHtml = '';
        if (op.when_to_run && op.when_to_run.length > 0) {
          whenToRunHtml = `
            <div class="operation-when">
              <h5>📅 When to Run This</h5>
              <ul>
                ${op.when_to_run.map(when => `<li>${when}</li>`).join('')}
              </ul>
            </div>
          `;
        }

        let contextHtml = '';
        if (op.why.context) {
          contextHtml = `<p class="operation-context">${op.why.context}</p>`;
        }

        let problemsHtml = '';
        if (op.why.problems && op.why.problems.length > 0) {
          problemsHtml = op.why.problems.map(problem =>
            `<li><strong>${problem.symptom}</strong><br>${problem.description}</li>`
          ).join('');
        }

        let outcomesHtml = '';
        if (op.what.outcomes && op.what.outcomes.length > 0) {
          outcomesHtml = op.what.outcomes.map(outcome => {
            const icon = outcome.type === 'positive' ? '✅' :
                        outcome.type === 'warning' ? '⚠️' :
                        outcome.type === 'temporary' ? '⏱️' : 'ℹ️';
            return `<li>${icon} ${outcome.description}</li>`;
          }).join('');
        }

        let timelineHtml = '';
        if (op.what.timeline) {
          timelineHtml = `<p class="operation-timeline"><strong>⏱️ How Long:</strong> ${op.what.timeline}</p>`;
        }

        whyWhatHtml = `
          <details class="operation-details">
            <summary>ℹ️ Why run this & What to expect</summary>
            <div class="operation-details-content">
              ${whenToRunHtml}
              ${contextHtml}
              <div class="operation-why">
                <h5>🔍 Problems This Solves</h5>
                <ul>${problemsHtml}</ul>
              </div>
              <div class="operation-what">
                <h5>✨ What Happens After Running</h5>
                <ul>${outcomesHtml}</ul>
                ${timelineHtml}
              </div>
            </div>
          </details>
        `;
      }

      return `
        <div class="operation-item" data-operation-id="${op.id}">
          <input type="checkbox" id="op-${op.id}" value="${op.id}"
                 ${op.recommended ? 'checked' : ''}>
          <div class="operation-info">
            <h4>
              ${op.name}
              ${op.recommended ? '<span class="badge recommended">Recommended</span>' : '<span class="badge optional">Optional</span>'}
            </h4>
            <p>${op.description}</p>
            ${whyWhatHtml}
            ${lastRunHtml}
          </div>
        </div>
      `;
    }).join('');

    const operationsDiv = document.getElementById('operations-list');
    if (operationsDiv) {
      operationsDiv.innerHTML = html;
    }

    const selectedCount = allOperations.filter(op => op.recommended).length;
    showToast(`Loaded ${allOperations.length} operations (${selectedCount} recommended)`, 'success', 2000);

    // Fetch and display global last maintenance run timestamp
    try {
      const lastRunResponse = await fetch('/api/maintenance/last-run');
      const lastRunData = await lastRunResponse.json();

      // Remove any existing info-banner to prevent duplicates
      const existingBanners = document.querySelectorAll('.info-banner');
      existingBanners.forEach(banner => banner.remove());

      if (lastRunData.success && lastRunData.status === 'completed') {
        const banner = document.createElement('div');
        banner.className = 'info-banner';
        banner.style.cssText = 'padding: 0.75rem; background: var(--success-bg); color: var(--success-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;';
        const relative = lastRunData.global_last_run_relative || 'Recently';
        banner.innerHTML = `📅 Last maintenance run: <strong>${relative}</strong>`;
        operationsDiv?.insertAdjacentElement('beforebegin', banner);
      } else if (lastRunData.status === 'never') {
        const banner = document.createElement('div');
        banner.className = 'info-banner';
        banner.style.cssText = 'padding: 0.75rem; background: var(--warning-bg); color: var(--warning-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;';
        banner.innerHTML = `ℹ️ Maintenance has never been run`;
        operationsDiv?.insertAdjacentElement('beforebegin', banner);
      }
    } catch (error) {
      console.warn('Could not fetch last run info:', error);
    }
  } catch (error) {
    console.error('Error loading operations:', error);
    const operationsDiv = document.getElementById('operations-list');
    if (operationsDiv) {
      operationsDiv.innerHTML = `<div class="error">Error loading operations: ${(error as Error).message}</div>`;
    }
    showToast('Failed to load operations', 'error');
  }
}

// ============================================================================
// Operation Selection & Templates
// ============================================================================

/**
 * Select all operations
 */
export function selectAllOperations(): void {
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#operations-list input[type="checkbox"]');
  checkboxes.forEach(cb => cb.checked = true);
  showToast(`Selected all ${checkboxes.length} operations`, 'info', 2000);
}

/**
 * Deselect all operations
 */
export function deselectAllOperations(): void {
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#operations-list input[type="checkbox"]');
  checkboxes.forEach(cb => cb.checked = false);
  showToast('Deselected all operations', 'info', 2000);
}

/**
 * Apply template selection
 */
export function applyTemplate(template: { name: string; operations: string[] }): void {
  console.log('Applying template:', template);

  // First, deselect all operations
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#operations-list input[type="checkbox"]');
  checkboxes.forEach(cb => cb.checked = false);

  // Then select operations from the template
  if (template.operations && template.operations.length > 0) {
    let selectedCount = 0;
    template.operations.forEach(opId => {
      const checkbox = document.getElementById(`op-${opId}`) as HTMLInputElement | null;
      if (checkbox) {
        checkbox.checked = true;
        selectedCount++;
      } else {
        console.warn(`Operation not found: ${opId}`);
      }
    });

    showToast(`Applied "${template.name}" - ${selectedCount} operations selected`, 'success', 3000);
  } else {
    showToast(`Applied "${template.name}"`, 'info', 2000);
  }
}

// ============================================================================
// Run Operations
// ============================================================================

/**
 * Run selected maintenance operations
 */
export async function runSelectedOperations(): Promise<void> {
  console.log('=== runSelectedOperations CALLED ===');
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#operations-list input[type="checkbox"]:checked');
  console.log('Found checked checkboxes:', checkboxes.length);
  const selected = Array.from(checkboxes).map(cb => cb.value);
  console.log('Selected operations:', selected);

  // Store selected operations for historical ETA calculation
  selectedOperationIds = selected;

  if (selected.length === 0) {
    console.log('No operations selected');
    alert('No operations selected');
    return;
  }

  // Increment invocation ID to track this specific run
  operationInvocationId++;
  const thisInvocationId = operationInvocationId;
  console.log('Operation invocation ID:', thisInvocationId);

  runningOperations = true;
  const runBtn = document.getElementById('run-btn') as HTMLButtonElement | null;
  if (runBtn) runBtn.disabled = true;

  // Disable Select All/Deselect All buttons during operations
  // UX Best Practice: Disable (don't hide) to maintain layout stability
  // Research: Nielsen Norman Group, Material Design, Microsoft HIG
  // Benefits: Prevents CLS (Cumulative Layout Shift), better accessibility, clear state communication
  const selectAllBtn = document.getElementById('select-all-btn') as HTMLButtonElement | null;
  const deselectAllBtn = document.getElementById('deselect-all-btn') as HTMLButtonElement | null;
  if (selectAllBtn) {
    selectAllBtn.disabled = true;
    selectAllBtn.setAttribute('aria-disabled', 'true');
    selectAllBtn.title = 'Selection locked while operations are running';
  }
  if (deselectAllBtn) {
    deselectAllBtn.disabled = true;
    deselectAllBtn.setAttribute('aria-disabled', 'true');
    deselectAllBtn.title = 'Selection locked while operations are running';
  }

  // Show Skip/Cancel buttons
  const skipBtn = document.getElementById('skip-btn') as HTMLElement | null;
  const cancelBtn = document.getElementById('cancel-btn') as HTMLElement | null;
  if (skipBtn) skipBtn.style.display = 'inline-block';
  if (cancelBtn) cancelBtn.style.display = 'inline-block';
  console.log('Showing Skip/Cancel buttons for invocation', thisInvocationId);

  // Show progress container and initialize progress
  const progressContainer = document.getElementById('progress-container');
  if (progressContainer) progressContainer.style.display = 'block';
  currentOperationIndex = 0;
  totalOperations = selected.length;
  operationTimes = [];
  batchStartTime = Date.now();  // Track batch start time for elapsed metric
  updateProgress();
  startProgressTimer();
  startQueueStatusPolling();

  // Show and populate output area
  const progressText = document.getElementById('progress-text') as HTMLElement | null;
  if (progressText) {
    progressText.style.display = 'block';
    progressText.textContent = 'Connecting to server...\n';
    progressText.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  try {
    const response = await fetch('/api/maintenance/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        operation_ids: selected
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start operations');
    }

    // Handle Server-Sent Events stream
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get response reader');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      // Decode and process SSE data
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonData = line.slice(6);
          try {
            const event: OperationEvent = JSON.parse(jsonData);
            handleOperationEvent(event);
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }

  } catch (error) {
    if (progressText) {
      progressText.textContent += `\n\nError: ${(error as Error).message}\n`;
    }
    console.error('Error running operations:', error);
  } finally {
    // Only cleanup if this is still the current invocation
    if (thisInvocationId === operationInvocationId) {
      console.log('Cleaning up invocation', thisInvocationId, '(current)');
      if (runBtn) runBtn.disabled = false;
      if (skipBtn) skipBtn.style.display = 'none';
      if (cancelBtn) cancelBtn.style.display = 'none';
      runningOperations = false;

      stopProgressTimer();
      stopQueueStatusPolling();
      batchStartTime = 0;  // Reset batch timer
      if (progressContainer) progressContainer.style.display = 'none';

      // Re-enable Select All/Deselect All buttons
      if (selectAllBtn) {
        selectAllBtn.disabled = false;
        selectAllBtn.removeAttribute('aria-disabled');
        selectAllBtn.title = '';
      }
      if (deselectAllBtn) {
        deselectAllBtn.disabled = false;
        deselectAllBtn.removeAttribute('aria-disabled');
        deselectAllBtn.title = '';
      }
    } else {
      console.log('Skipping cleanup for invocation', thisInvocationId, '(superseded by', operationInvocationId, ')');
    }
  }
}

/**
 * Skip the current operation
 */
export async function skipCurrentOperation(): Promise<void> {
  // No confirmation needed - skipping is a routine, reversible action
  // UX Research: https://www.nngroup.com/articles/confirmation-dialog/
  // "Confirmatory dialogs for routine actions cause habituation"

  try {
    const response = await fetch('/api/maintenance/skip', {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();

    const progressText = document.getElementById('progress-text');
    if (progressText) {
      const message = result.message || 'Skipped by user';
      progressText.textContent += `\n\n⏭️ ${message}\n`;
    }

    showToast('Operation skipped', 'info', 2000);

  } catch (error) {
    console.error('Error skipping operation:', error);
    alert('Error skipping operation: ' + (error as Error).message);
  }
}

/**
 * Cancel all running operations
 */
export async function cancelOperations(): Promise<void> {
  if (!confirm('Cancel all running operations?')) {
    return;
  }

  try {
    const response = await fetch('/api/maintenance/cancel', {
      method: 'POST'
    });

    const result = await response.json();

    const progressText = document.getElementById('progress-text');
    if (progressText) {
      progressText.textContent += `\n\n⚠️ ${result.message}\n`;
    }

    // Hide buttons and increment invocation ID
    operationInvocationId++;
    runningOperations = false;
    const runBtn = document.getElementById('run-btn') as HTMLButtonElement | null;
    const skipBtn = document.getElementById('skip-btn') as HTMLElement | null;
    const cancelBtn = document.getElementById('cancel-btn') as HTMLElement | null;
    if (runBtn) runBtn.disabled = false;
    if (skipBtn) skipBtn.style.display = 'none';
    if (cancelBtn) cancelBtn.style.display = 'none';

    stopProgressTimer();
    stopQueueStatusPolling();
    batchStartTime = 0;  // Reset batch timer
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) progressContainer.style.display = 'none';

    const selectAllBtn = document.getElementById('select-all-btn') as HTMLButtonElement | null;
    const deselectAllBtn = document.getElementById('deselect-all-btn') as HTMLButtonElement | null;
    if (selectAllBtn) {
      selectAllBtn.disabled = false;
      selectAllBtn.removeAttribute('aria-disabled');
      selectAllBtn.title = '';
    }
    if (deselectAllBtn) {
      deselectAllBtn.disabled = false;
      deselectAllBtn.removeAttribute('aria-disabled');
      deselectAllBtn.title = '';
    }

    console.log('Operations cancelled, incremented invocation ID to', operationInvocationId);

  } catch (error) {
    console.error('Error cancelling operations:', error);
    alert('Error cancelling operations: ' + (error as Error).message);
  }
}

// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Handle operation event from SSE stream
 */
export function handleOperationEvent(event: OperationEvent): void {
  const progressText = document.getElementById('progress-text');
  if (!progressText) return;

  switch (event.type) {
    case 'start':
      progressText.textContent += `\n${event.message}\n`;
      progressText.textContent += `${'='.repeat(60)}\n\n`;

      // Hide copy button when starting new operations
      const inlineActionsStart = document.getElementById('inline-progress-actions');
      if (inlineActionsStart) {
        inlineActionsStart.style.display = 'none';
        inlineActionsStart.innerHTML = '';
      }

      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }, 50);
      break;

    case 'operation_start':
      progressText.textContent += `\n[${event.progress}] Starting: ${event.operation_name}\n`;
      progressText.textContent += `${'-'.repeat(60)}\n`;

      operationStartTime = Date.now();
      currentOperationId = event.operation_id || null;
      currentOperationIndex++;
      updateProgress();
      break;

    case 'output':
      progressText.textContent += `${event.line}\n`;
      progressText.scrollTop = progressText.scrollHeight;
      break;

    case 'operation_complete':
      const status = event.success ? '✓ Success' : '✗ Failed';
      progressText.textContent += `\n${status} (exit code: ${event.returncode})\n`;

      if (operationStartTime > 0 && currentOperationId) {
        const durationMs = Date.now() - operationStartTime;
        const durationSec = durationMs / 1000;

        // Record to historical tracking (successful runs only for a cleaner median)
        if (event.success) {
          recordOperationTime(currentOperationId, durationSec);
        }

        // Also track for current batch average
        operationTimes.push(durationMs);

        updateProgress();
      }
      currentOperationId = null;
      break;

    case 'operation_skipped':
      progressText.textContent += `\n⏭️  Skipped by user\n`;
      break;

    case 'operation_error':
      progressText.textContent += `\nError: ${event.message}\n`;
      break;

    case 'summary':
      progressText.textContent += `\n${'='.repeat(60)}\n`;
      progressText.textContent += `\nSummary:\n`;
      progressText.textContent += `  Total operations: ${event.total}\n`;
      progressText.textContent += `  Successful: ${event.successful}\n`;
      progressText.textContent += `  Failed: ${event.failed}\n`;
      break;

    case 'complete':
      progressText.textContent += `\n${event.message}\n`;
      progressText.textContent += `${'='.repeat(60)}\n`;

      refreshLastRunTimestamp();

      // Add copy button
      const inlineActions = document.getElementById('inline-progress-actions');
      if (inlineActions) {
        inlineActions.innerHTML = '';
        inlineActions.style.display = 'flex';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'primary';
        copyBtn.id = 'copy-output-btn';
        copyBtn.innerHTML = '📋 Copy Output to Clipboard';
        copyBtn.onclick = () => copyOutputToClipboard();
        inlineActions.appendChild(copyBtn);

        setTimeout(() => {
          copyBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
      }
      break;

    case 'cancelled':
      progressText.textContent += `\n${event.message}\n`;
      break;

    case 'error':
      progressText.textContent += `\nError: ${event.message}\n`;
      break;
  }

  progressText.scrollTop = progressText.scrollHeight;
}

/**
 * Copy operation output to clipboard
 */
export async function copyOutputToClipboard(): Promise<void> {
  const progressText = document.getElementById('progress-text');
  const copyBtn = document.getElementById('copy-output-btn') as HTMLButtonElement | null;

  if (!progressText || !copyBtn) return;

  try {
    await navigator.clipboard.writeText(progressText.textContent || '');

    const originalText = copyBtn.innerHTML;
    copyBtn.innerHTML = '✓ Copied to Clipboard!';
    copyBtn.className = 'primary success-flash';

    setTimeout(() => {
      copyBtn.innerHTML = originalText;
      copyBtn.className = 'primary';
    }, 2000);

  } catch (error) {
    console.error('Failed to copy to clipboard:', error);

    const originalText = copyBtn.innerHTML;
    copyBtn.innerHTML = '✗ Copy Failed';
    copyBtn.className = 'danger';

    setTimeout(() => {
      copyBtn.innerHTML = originalText;
      copyBtn.className = 'primary';
    }, 2000);
  }
}

// ============================================================================
// Progress Tracking
// ============================================================================

/**
 * Update elapsed time for entire batch
 */
function updateElapsedTime(): void {
  if (batchStartTime > 0) {
    const elapsed = Date.now() - batchStartTime;
    const elapsedEl = document.getElementById('total-elapsed');
    if (elapsedEl) {
      elapsedEl.textContent = formatDuration(elapsed / 1000);
    }
  }
}

/**
 * Start progress timer
 */
export function startProgressTimer(): void {
  if (progressTimerInterval) {
    clearInterval(progressTimerInterval);
  }

  progressTimerInterval = window.setInterval(() => {
    // Update current operation timer
    if (operationStartTime > 0) {
      const elapsed = Date.now() - operationStartTime;
      const timerEl = document.getElementById('current-op-timer');
      if (timerEl) {
        const currentDuration = formatDuration(elapsed / 1000);

        // Show typical duration if available (server preferred; fallback to localStorage)
        if (currentOperationId) {
          const serverTypicalSec = operationStats?.[currentOperationId]?.typical_seconds;
          const medianSec = typeof serverTypicalSec === 'number' ? serverTypicalSec : getMedianDuration(currentOperationId);

          if (medianSec !== null && typeof medianSec === 'number' && !Number.isNaN(medianSec)) {
            const typicalDuration = formatDuration(medianSec);
            timerEl.textContent = `${currentDuration} / Typically ${typicalDuration}`;
            timerEl.setAttribute('title', 'Typical runtime (median of recent runs)');
          } else {
            timerEl.textContent = `${currentDuration} / Typically —`;
            timerEl.setAttribute('title', 'No historical runtime yet (first run)');
          }
        } else {
          timerEl.textContent = currentDuration;
        }
      }
    }

    // Update total elapsed time
    updateElapsedTime();
  }, 1000);
}

/**
 * Stop progress timer
 */
export function stopProgressTimer(): void {
  if (progressTimerInterval) {
    clearInterval(progressTimerInterval);
    progressTimerInterval = null;
  }
}

/**
 * Update progress display
 */
export function updateProgress(): void {
  const percent = totalOperations > 0
    ? Math.round((currentOperationIndex / totalOperations) * 100)
    : 0;

  console.log('updateProgress:', { currentOperationIndex, totalOperations, percent });

  // Use unique IDs to avoid conflicts with progress-overlay modal
  const progressBar = document.getElementById('maintenance-progress-bar') as HTMLElement | null;
  const progressPercent = document.getElementById('maintenance-progress-percent');

  if (progressBar) {
    progressBar.style.width = percent + '%';
    console.log('Set maintenance-progress-bar width to:', percent + '%');
  } else {
    console.error('maintenance-progress-bar element not found!');
  }

  if (progressPercent) {
    progressPercent.textContent = percent + '%';
    console.log('Set maintenance-progress-percent text to:', percent + '%');
  } else {
    console.error('maintenance-progress-percent element not found!');
  }

  const progressLabel = document.getElementById('progress-label');
  if (progressLabel) {
    progressLabel.textContent = `Operation ${currentOperationIndex} of ${totalOperations}`;
  }

  const opsProgress = document.getElementById('ops-progress');
  if (opsProgress) {
    opsProgress.textContent = `${currentOperationIndex}/${totalOperations}`;
  }

  // Calculate estimated remaining time using historical data
  const estRemaining = document.getElementById('est-remaining');
  if (estRemaining) {
    if (currentOperationIndex >= totalOperations) {
      estRemaining.textContent = 'Complete';
    } else if (selectedOperationIds.length > 0) {
      // Calculate remaining operations
      const remainingOps = selectedOperationIds.slice(currentOperationIndex);

      // Calculate progress of current operation (if any)
      const currentProgress = currentOperationId && operationStartTime > 0
        ? Math.min((Date.now() - operationStartTime) / (getAverageDuration(currentOperationId) * 1000), 0.99)
        : 0;

      // Use historical averages for accurate ETA
      const etaSeconds = calculateETA(remainingOps, currentOperationId, currentProgress);
      estRemaining.textContent = formatDuration(etaSeconds);
    } else {
      estRemaining.textContent = 'Calculating...';
    }
  }
}

/**
 * Start queue status polling
 */
export function startQueueStatusPolling(): void {
  if (queueStatusInterval) {
    clearInterval(queueStatusInterval);
  }

  queueStatusInterval = window.setInterval(async () => {
    try {
      const response = await fetch('/api/maintenance/queue');
      const data = await response.json();

      const queueDiv = document.getElementById('queue-status');
      if (data.queued_count > 0) {
        if (queueDiv) queueDiv.style.display = 'flex';
        const queueCount = document.getElementById('queue-count');
        if (queueCount) queueCount.textContent = String(data.queued_count);
      } else {
        if (queueDiv) queueDiv.style.display = 'none';
      }

      if (data.current_operation) {
        console.log('Current operation:', data.current_operation);
      }
    } catch (error) {
      console.error('Error polling queue status:', error);
    }
  }, 2000);
}

/**
 * Stop queue status polling
 */
export function stopQueueStatusPolling(): void {
  if (queueStatusInterval) {
    clearInterval(queueStatusInterval);
    queueStatusInterval = null;
  }
}

/**
 * Refresh last run timestamp after operations complete
 */
async function refreshLastRunTimestamp(): Promise<void> {
  try {
    const response = await fetch('/api/maintenance/last-run');
    const data = await response.json();

    const banners = document.querySelectorAll('.last-run-banner');
    banners.forEach(banner => {
      if (data.last_run) {
        const statusIcon = data.status === 'completed' ? '✓' : '✗';
        banner.innerHTML = `📅 Last run: ${data.last_run_relative} ${statusIcon}`;
      }
    });
  } catch (error) {
    console.error('Error refreshing timestamp:', error);
  }
}

// ============================================================================
// Quick Start Wizard
// ============================================================================

// Research-based presets for Mac maintenance (2025-2026 best practices)
const WIZARD_PRESETS: Record<string, string[]> = {
  // Quick Clean: Fast cleanup for weekly/biweekly use (5 min)
  quick: ['browser-cache', 'trim-caches'],

  // Weekly Routine: Comprehensive weekly maintenance (15 min)
  weekly: ['brew-update', 'mas-update', 'disk-verify', 'browser-cache', 'trim-caches', 'trim-logs', 'spotlight-status'],

  // Full Checkup: All recommended + comprehensive safe operations (30 min)
  full: ['brew-update', 'mas-update', 'disk-verify', 'browser-cache', 'dev-cache', 'trim-caches', 'trim-logs', 'smart-check', 'spotlight-status', 'dns-flush']
};

export function showQuickStartWizard(): void {
  const modal = document.getElementById('wizard-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

export function closeWizard(): void {
  const modal = document.getElementById('wizard-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

export async function selectWizardOption(option: string): Promise<void> {
  closeWizard();

  if (option === 'custom') {
    showToast('Select operations below', 'info', 2000);
    return;
  }

  // Get operations for this preset
  const operationsToRun = WIZARD_PRESETS[option] || [];

  // Select the operations
  document.querySelectorAll('#operations-list input[type="checkbox"]').forEach((cb) => {
    const checkbox = cb as HTMLInputElement;
    checkbox.checked = operationsToRun.includes(checkbox.value);
  });

  // Show confirmation
  const optionNames: Record<string, string> = {
    quick: 'Quick Clean',
    weekly: 'Weekly Routine',
    full: 'Full Checkup'
  };

  showToast(`✨ Selected: ${optionNames[option]} (${operationsToRun.length} operations)`, 'success', 3000);

  // Scroll to operations list
  const operationsList = document.getElementById('operations-list');
  if (operationsList) {
    operationsList.scrollIntoView({ behavior: 'smooth' });
  }

  // Hide wizard prompt after first use
  const wizardPrompt = document.getElementById('wizard-prompt');
  if (wizardPrompt) {
    wizardPrompt.style.display = 'none';
  }
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

function isTypingInField(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el) return false;
  const tag = (el.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || el.isContentEditable;
}

export function closeShortcuts(): void {
  const modal = document.getElementById('shortcuts-modal');
  if (modal) modal.classList.remove('active');
}

function openShortcuts(): void {
  const modal = document.getElementById('shortcuts-modal');
  if (modal) modal.classList.add('active');
}

export function initKeyboardShortcuts(): void {
  document.addEventListener('keydown', (e: KeyboardEvent) => {
    // Don't trigger global shortcuts while typing
    if (isTypingInField(e.target)) return;

    // "?" opens shortcuts
    if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
      e.preventDefault();
      openShortcuts();
      return;
    }

    // "/" focuses operation search
    if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey) {
      const search = document.getElementById('operation-search') as HTMLInputElement | null;
      if (search) {
        e.preventDefault();
        search.focus();
      }
      return;
    }

    // Escape closes modals
    if (e.key === 'Escape') {
      closeShortcuts();
      closeWizard();
      const closeScheduleModalFn = (window as any).closeScheduleModal as undefined | (() => void);
      if (closeScheduleModalFn) closeScheduleModalFn();
    }
  });
}

