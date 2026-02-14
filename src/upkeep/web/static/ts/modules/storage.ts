/**
 * Storage module - Storage analysis and file management
 */

import type { StorageAnalyzeResponse } from '../types';
import { showToast, showProgressOverlay, updateProgressOverlay, hideProgressOverlay } from './ui';
import { escapeHtml } from './utils';

// ============================================================================
// Global State
// ============================================================================

export const selectedFiles: Set<string> = new Set();

// ============================================================================
// Storage Analysis
// ============================================================================

/**
 * Analyze storage at specified path
 */
export async function analyzeStorage(): Promise<void> {
  const pathInput = document.getElementById('path-input') as HTMLInputElement | null;
  const path = pathInput?.value || '/Users';
  const resultsDiv = document.getElementById('storage-results');
  const analyzeBtn = document.getElementById('analyze-btn-text');

  if (!resultsDiv || !analyzeBtn) return;

  resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div> Analyzing storage...</div>';
  analyzeBtn.innerHTML = '<div class="spinner"></div>';
  selectedFiles.clear();
  updateBreadcrumbs(path);

  try {
    const response = await fetch(`/api/storage/analyze?path=${encodeURIComponent(path)}`);

    if (!response.ok) {
      let errorMsg = `Server error: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorMsg;
      } catch {
        // Response is not JSON
      }
      analyzeBtn.textContent = 'Analyze';
      resultsDiv.innerHTML = `<div class="error">${errorMsg}</div>`;
      showToast(errorMsg, 'error');
      return;
    }

    const data: StorageAnalyzeResponse = await response.json();
    analyzeBtn.textContent = 'Analyze';

    if (!data.success) {
      const errorMsg = (data as any).error || 'Unknown error occurred';
      resultsDiv.innerHTML = `<div class="error">${errorMsg}</div>`;
      showToast(errorMsg, 'error');
      return;
    }

    showToast(`Analyzed: ${data.file_count} files, ${data.total_size_gb.toFixed(2)} GB`, 'success');

    resultsDiv.innerHTML = `
      <h3 style="margin-top: 2rem;">Results for ${data.path || path}</h3>
      <div class="metric-grid" style="margin-top: 1rem;">
        <div class="metric-card">
          <h3>Total Size</h3>
          <div class="value">${data.total_size_gb.toFixed(2)} GB</div>
        </div>
        <div class="metric-card">
          <h3>Files</h3>
          <div class="value">${data.file_count.toLocaleString()}</div>
        </div>
        <div class="metric-card">
          <h3>Directories</h3>
          <div class="value">${data.dir_count.toLocaleString()}</div>
        </div>
      </div>
      <h3 style="margin-top: 2rem;">Largest Items</h3>
      <p style="color: var(--text-secondary); margin-top: 0.5rem;">Select items to delete</p>
      <div class="file-list">
        ${data.largest_entries.map((entry, idx) => {
          const displayName = entry.path.split('/').pop();
          return `
          <div class="file-item">
            <input type="checkbox" id="file-${idx}" data-path="${entry.path.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}">
            <div class="file-info">
              <strong>${displayName}</strong><br>
              <small style="color: var(--text-secondary);">${entry.path}</small>
            </div>
            <div class="file-size">
              <strong>${entry.size_gb.toFixed(2)} GB</strong><br>
              <small style="color: var(--text-secondary);">${entry.is_dir ? 'Directory' : 'File'}</small>
            </div>
          </div>
        `;
        }).join('')}
      </div>
      <div class="button-group">
        <button class="primary" id="trash-btn">
          🗑️ Move to Trash (<span id="selected-count">0</span>)
        </button>
        <button class="danger" id="permanent-delete-btn">
          ⚠️ Permanently Delete (<span id="selected-count-permanent">0</span>)
        </button>
        <button class="secondary" id="select-all-btn">Select All</button>
        <button class="secondary" id="deselect-all-btn">Deselect All</button>
      </div>
    `;

    // Attach event listeners
    console.log('=== ATTACHING EVENT LISTENERS ===');
    const trashBtn = document.getElementById('trash-btn');
    const permBtn = document.getElementById('permanent-delete-btn');
    const selAllBtn = document.getElementById('select-all-btn');
    const deselAllBtn = document.getElementById('deselect-all-btn');

    console.log('Trash button found:', trashBtn);
    console.log('Permanent button found:', permBtn);

    if (trashBtn) {
      trashBtn.addEventListener('click', () => {
        console.log('TRASH BUTTON CLICKED!');
        deleteSelected('trash');
      });
      console.log('✓ Trash button listener attached');
    }

    if (permBtn) {
      permBtn.addEventListener('click', () => {
        console.log('PERMANENT DELETE BUTTON CLICKED!');
        deleteSelected('permanent');
      });
      console.log('✓ Permanent button listener attached');
    }

    if (selAllBtn) {
      selAllBtn.addEventListener('click', selectAllFiles);
      console.log('✓ Select all button listener attached');
    }

    if (deselAllBtn) {
      deselAllBtn.addEventListener('click', deselectAllFiles);
      console.log('✓ Deselect all button listener attached');
    }

    // Attach checkbox event listeners
    const checkboxes = document.querySelectorAll<HTMLInputElement>('#storage-results input[type="checkbox"]');
    console.log('Found checkboxes:', checkboxes.length);
    checkboxes.forEach((checkbox, idx) => {
      checkbox.addEventListener('change', () => {
        console.log(`Checkbox ${idx} changed, path:`, checkbox.dataset.path);
        if (checkbox.dataset.path) {
          toggleFileSelection(checkbox.dataset.path);
        }
      });
    });
    console.log('✓ All checkbox listeners attached');

  } catch (error) {
    const errorMsg = (error as Error).message || 'Failed to analyze storage';
    resultsDiv.innerHTML = `<div class="error">Error: ${errorMsg}</div>`;
    analyzeBtn.textContent = 'Analyze';
    showToast(errorMsg, 'error');
  }
}

// ============================================================================
// File Selection
// ============================================================================

/**
 * Toggle file selection
 */
export function toggleFileSelection(path: string): void {
  console.log('toggleFileSelection called with:', path);
  console.log('selectedFiles before:', Array.from(selectedFiles));
  if (selectedFiles.has(path)) {
    selectedFiles.delete(path);
    console.log('Removed path');
  } else {
    selectedFiles.add(path);
    console.log('Added path');
  }
  console.log('selectedFiles after:', Array.from(selectedFiles));
  updateSelectedCount();
}

/**
 * Update selected file count display
 */
export function updateSelectedCount(): void {
  const count = selectedFiles.size;
  const countEl = document.getElementById('selected-count');
  const countElPermanent = document.getElementById('selected-count-permanent');
  if (countEl) countEl.textContent = String(count);
  if (countElPermanent) countElPermanent.textContent = String(count);
}

/**
 * Select all files
 */
export function selectAllFiles(): void {
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#storage-results input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = true;
    if (cb.dataset.path) {
      selectedFiles.add(cb.dataset.path);
    }
  });
  updateSelectedCount();
}

/**
 * Deselect all files
 */
export function deselectAllFiles(): void {
  const checkboxes = document.querySelectorAll<HTMLInputElement>('#storage-results input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = false;
  });
  selectedFiles.clear();
  updateSelectedCount();
}

// ============================================================================
// File Deletion
// ============================================================================

/**
 * Delete selected files (move to trash or permanent)
 */
export async function deleteSelected(mode: 'trash' | 'permanent' = 'trash'): Promise<void> {
  console.log('=== deleteSelected CALLED ===');
  console.log('Mode:', mode);
  console.log('selectedFiles.size:', selectedFiles.size);
  console.log('selectedFiles contents:', Array.from(selectedFiles));

  if (selectedFiles.size === 0) {
    console.log('No files selected, showing toast');
    showToast('No files selected', 'warning');
    return;
  }

  // Different confirmation messages based on mode
  let confirmMessage: string;
  if (mode === 'permanent') {
    confirmMessage = `⚠️ PERMANENTLY DELETE ${selectedFiles.size} item(s)?\n\n` +
                    `This CANNOT be undone! Files will be deleted forever.\n\n` +
                    `Consider using "Move to Trash" instead (recoverable).`;
  } else {
    confirmMessage = `Move ${selectedFiles.size} item(s) to Trash?\n\n` +
                    `You can recover them from macOS Trash if needed.`;
  }

  console.log('Showing confirmation dialog');
  const confirmed = confirm(confirmMessage);
  console.log('User confirmed:', confirmed);

  if (!confirmed) {
    console.log('User cancelled');
    return;
  }

  console.log('Proceeding with delete...');

  const totalFiles = selectedFiles.size;
  let deleted = 0;
  let failed = 0;
  const failedPaths: Array<{ path: string; error: string }> = [];
  let operationCancelled = false;

  // Disable both buttons
  const trashBtn = document.getElementById('trash-btn') as HTMLButtonElement | null;
  const permanentBtn = document.getElementById('permanent-delete-btn') as HTMLButtonElement | null;
  if (trashBtn) trashBtn.disabled = true;
  if (permanentBtn) permanentBtn.disabled = true;

  // Show progress overlay
  const actionTitle = mode === 'permanent' ? '⚠️ Permanently Deleting Files...' : '🗑️ Moving Files to Trash...';
  showProgressOverlay(actionTitle, totalFiles, () => {
    operationCancelled = true;
  });

  // Delete each file sequentially with progress updates
  let current = 0;
  for (const path of selectedFiles) {
    if (operationCancelled) {
      break;
    }

    current++;
    const fileName = path.split('/').pop();
    updateProgressOverlay(current, totalFiles, `Processing: ${fileName}`);

    try {
      const response = await fetch(`/api/storage/delete?path=${encodeURIComponent(path)}&mode=${mode}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        deleted++;
      } else {
        failed++;
        failedPaths.push({ path, error: result.error || 'Unknown error' });
        console.error(`Failed to ${mode === 'permanent' ? 'delete' : 'move to trash'} ${path}:`, result.error);
      }
    } catch (error) {
      failed++;
      failedPaths.push({ path, error: (error as Error).message });
      console.error(`Error processing ${path}:`, error);
    }
  }

  // Hide progress overlay
  hideProgressOverlay();

  // Re-enable buttons
  if (trashBtn) trashBtn.disabled = false;
  if (permanentBtn) permanentBtn.disabled = false;

  // Clear selection
  selectedFiles.clear();
  updateSelectedCount();

  // Show final results
  const successVerb = mode === 'permanent' ? 'deleted' : 'moved to Trash';
  const failedVerb = mode === 'permanent' ? 'delete' : 'move';

  if (operationCancelled) {
    showToast(`⚠️ Operation cancelled. Processed ${deleted + failed}/${totalFiles} items.`, 'warning', 4000);
  } else if (deleted > 0 && failed === 0) {
    showToast(`✅ Successfully ${successVerb} ${deleted} item(s)`, 'success', 4000);
    if (mode === 'trash') {
      showToast('💡 Tip: You can recover files from macOS Trash', 'info', 3000);
    }
  } else if (deleted > 0 && failed > 0) {
    showToast(`⚠️ ${successVerb.charAt(0).toUpperCase() + successVerb.slice(1)} ${deleted}, failed to ${failedVerb} ${failed} item(s)`, 'warning', 6000);
    console.error('Failed operations:', failedPaths);
  } else {
    showToast(`❌ Failed to ${failedVerb} all ${failed} item(s)`, 'error', 6000);
    console.error('Failed operations:', failedPaths);
  }

  // Refresh storage view to verify actual filesystem state
  showToast('Refreshing view...', 'info', 2000);
  await analyzeStorage();
}

// ============================================================================
// Path Navigation
// ============================================================================

/**
 * Update breadcrumbs navigation
 */
export function updateBreadcrumbs(path: string): void {
  const breadcrumbsDiv = document.getElementById('breadcrumbs');
  if (!breadcrumbsDiv) return;

  const parts = path.split('/').filter(p => p);
  if (parts.length === 0) {
    breadcrumbsDiv.innerHTML = '<span class="breadcrumb" onclick="setPath(\'/\')">Root</span>';
    return;
  }

  let html = '<span class="breadcrumb" onclick="setPath(\'/\')">🏠 Root</span>';
  let currentPath = '';

  parts.forEach((part, index) => {
    currentPath += '/' + part;
    const fullPath = currentPath;
    html += ` <span class="breadcrumb-separator">/</span> `;
    html += `<span class="breadcrumb" onclick="setPath('${fullPath}')">${part}</span>`;
  });

  breadcrumbsDiv.innerHTML = html;
}

/**
 * Navigate to a specific path
 */
export function navigateToPath(path: string): void {
  const pathInput = document.getElementById('path-input') as HTMLInputElement | null;
  if (pathInput) {
    pathInput.value = path;
    updateBreadcrumbs(path);
    showToast(`Path set to: ${path}`, 'info', 2000);
  }
}

/**
 * Alias for navigateToPath (used by HTML onclick handlers)
 */
export function setPath(path: string): void {
  navigateToPath(path);
}

/**
 * Get current username from stored system info
 */
export function getUsername(): string {
  // Access global state from dashboard module
  return (window as any)._currentUsername || 'username';
}
