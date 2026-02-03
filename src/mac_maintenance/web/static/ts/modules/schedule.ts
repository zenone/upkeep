/**
 * Schedule module - Schedule management and automation
 */

import type { Schedule } from '../types';
import { showToast } from './ui';
import { escapeHtml } from './utils';

// ============================================================================
// Schedule Templates
// ============================================================================

/**
 * Load and display schedule templates
 */
export async function loadScheduleTemplates(): Promise<void> {
  try {
    console.log('Loading schedule templates...');
    const response = await fetch('/api/schedules/templates');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Templates loaded:', data);

    const container = document.getElementById('templates-list');
    if (!container) return;

    if (!data.templates || data.templates.length === 0) {
      container.innerHTML = '<p style="color: var(--text-secondary);">No templates available</p>';
      return;
    }

    container.innerHTML = data.templates.map((template: any) => {
      const templateJson = JSON.stringify(template).replace(/'/g, "\\'");
      return `
        <div class="template-card ${template.recommended ? 'recommended' : ''}"
             onclick='applyScheduleTemplate(${templateJson})'>
          <div class="template-icon">${template.icon}</div>
          <div class="template-name">${escapeHtml(template.name)}</div>
          <div class="template-desc">${escapeHtml(template.description)}</div>
          ${template.recommended ? '<span class="template-badge">RECOMMENDED</span>' : ''}
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error('Failed to load templates:', error);
    const container = document.getElementById('templates-list');
    if (container) {
      container.innerHTML = `<p style="color: var(--danger);">Error loading templates: ${(error as Error).message}</p>`;
    }
    showToast('Failed to load templates: ' + (error as Error).message, 'error');
  }
}

// ============================================================================
// Schedule Management
// ============================================================================

/**
 * Load and display schedules
 */
export async function loadSchedules(): Promise<void> {
  try {
    const response = await fetch('/api/schedules');
    const data = await response.json();

    const container = document.getElementById('schedules-list');
    if (!container) return;

    if (!data.success || !data.schedules || data.schedules.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">📅</div>
          <p>No schedules yet</p>
          <p style="font-size: 0.875rem;">Click "New Schedule" or use a template to get started</p>
        </div>
      `;
      return;
    }

    container.innerHTML = data.schedules.map((schedule: Schedule) => {
      const nextRun = schedule.next_run ? formatDateTime(schedule.next_run) : 'Not scheduled';
      const lastRun = schedule.last_run ? formatDateTime(schedule.last_run) : 'Never';
      const statusClass = schedule.enabled ? 'enabled' : 'disabled';
      const statusText = schedule.enabled ? '● Enabled' : '○ Disabled';

      return `
        <div class="schedule-card ${schedule.enabled ? '' : 'disabled'}">
          <div class="schedule-header">
            <div>
              <div class="schedule-title">${escapeHtml(schedule.name)}</div>
              ${schedule.description ? `<div class="schedule-desc">${escapeHtml(schedule.description)}</div>` : ''}
            </div>
            <div class="schedule-actions">
              <button class="secondary" onclick="editSchedule('${schedule.id}')" title="Edit">
                ✏️
              </button>
              <button class="secondary" onclick="toggleScheduleEnabled('${schedule.id}', ${!schedule.enabled})"
                      title="${schedule.enabled ? 'Disable' : 'Enable'}">
                ${schedule.enabled ? '⏸️' : '▶️'}
              </button>
              <button class="warning" onclick="runScheduleNow('${schedule.id}')" title="Run now">
                ▶️ Run
              </button>
              <button class="danger" onclick="deleteSchedule('${schedule.id}')" title="Delete schedule">
                🗑️ Delete
              </button>
            </div>
          </div>
          <div class="schedule-info">
            <div class="schedule-info-item">
              <div class="schedule-info-label">Status</div>
              <div class="schedule-info-value">
                <span class="schedule-status ${statusClass}">${statusText}</span>
              </div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Frequency</div>
              <div class="schedule-info-value">${formatFrequency(schedule)}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Time</div>
              <div class="schedule-info-value">${schedule.time_of_day}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Next Run</div>
              <div class="schedule-info-value">
                <span class="next-run-badge">⏰ ${nextRun}</span>
              </div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Last Run</div>
              <div class="schedule-info-value">${lastRun}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Operations</div>
              <div class="schedule-info-value">${(schedule as any).operations?.length ?? (schedule as any).operation_ids?.length ?? 0} selected</div>
            </div>
          </div>
          ${schedule.message ? `
            <div class="conflict-warning">
              <div class="conflict-warning-text">⚠️ ${escapeHtml(schedule.message)}</div>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error('Failed to load schedules:', error);
    showToast('Failed to load schedules', 'error');
  }
}

/**
 * Save a schedule (create or update)
 */
export async function saveSchedule(): Promise<void> {
  const scheduleIdEl = document.getElementById('schedule-id') as HTMLInputElement | null;
  const scheduleId = scheduleIdEl?.value || '';
  const nameEl = document.getElementById('schedule-name') as HTMLInputElement | null;
  const name = nameEl?.value || '';
  const descEl = document.getElementById('schedule-description') as HTMLTextAreaElement | null;
  const description = descEl?.value || '';
  const freqEl = document.getElementById('schedule-frequency') as HTMLSelectElement | null;
  const frequency = freqEl?.value || '';
  const timeEl = document.getElementById('schedule-time') as HTMLInputElement | null;
  const time = timeEl?.value || '';
  const enabledEl = document.getElementById('schedule-enabled') as HTMLInputElement | null;
  const enabled = enabledEl?.checked || false;

  // Get selected operations
  const operations = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="operations"]:checked'))
    .map(cb => cb.value);

  if (!name || operations.length === 0 || !time) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  const scheduleData: any = {
    name,
    description,
    operations,
    frequency,
    time_of_day: time + ':00', // Add seconds
    enabled
  };

  // Add frequency-specific fields
  if (frequency === 'weekly') {
    const days = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="days"]:checked'))
      .map(cb => cb.value);
    if (days.length === 0) {
      showToast('Please select at least one day of the week', 'error');
      return;
    }
    scheduleData.days_of_week = days;
  } else if (frequency === 'monthly') {
    const dayEl = document.getElementById('schedule-day') as HTMLInputElement | null;
    const day = parseInt(dayEl?.value || '0');
    if (!day || day < 1 || day > 28) {
      showToast('Please enter a day between 1 and 28', 'error');
      return;
    }
    scheduleData.day_of_month = day;
  }

  try {
    const url = scheduleId ? `/api/schedules/${scheduleId}` : '/api/schedules';
    const method = scheduleId ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scheduleData)
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to save schedule');
    }

    showToast(scheduleId ? 'Schedule updated!' : 'Schedule created!', 'success');
    closeScheduleModal();
    loadSchedules();
  } catch (error) {
    console.error('Failed to save schedule:', error);
    showToast((error as Error).message, 'error');
  }
}

/**
 * Delete a schedule
 */
export async function deleteSchedule(scheduleId: string): Promise<void> {
  if (!confirm('Delete this schedule? This will unregister it from launchd.')) {
    return;
  }

  try {
    const response = await fetch(`/api/schedules/${scheduleId}`, {
      method: 'DELETE'
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete schedule');
    }

    showToast('Schedule deleted', 'success');
    loadSchedules();
  } catch (error) {
    console.error('Failed to delete schedule:', error);
    showToast((error as Error).message, 'error');
  }
}

/**
 * Toggle schedule enabled state
 */
export async function toggleScheduleEnabled(scheduleId: string, enabled: boolean): Promise<void> {
  try {
    const response = await fetch(`/api/schedules/${scheduleId}/enabled`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to toggle schedule');
    }

    showToast(enabled ? 'Schedule enabled' : 'Schedule disabled', 'success');
    loadSchedules();
  } catch (error) {
    console.error('Failed to toggle schedule:', error);
    showToast((error as Error).message, 'error');
  }
}

/**
 * Run schedule immediately
 */
export async function runScheduleNow(scheduleId: string): Promise<void> {
  if (!confirm('Run this schedule now? This will execute all operations immediately.')) {
    return;
  }

  try {
    const response = await fetch(`/api/schedules/${scheduleId}/run-now`, {
      method: 'POST'
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || 'Failed to run schedule');
    }

    showToast('Schedule running...', 'success');
    // Reload to show updated last_run
    setTimeout(() => loadSchedules(), 2000);
  } catch (error) {
    console.error('Failed to run schedule:', error);
    showToast((error as Error).message, 'error');
  }
}

// ============================================================================
// Schedule Modal
// ============================================================================

/**
 * Open schedule modal for create/edit
 */
export function openScheduleModal(scheduleId: string | null = null): Promise<void> {
  const modal = document.getElementById('schedule-modal');
  const title = document.getElementById('schedule-modal-title');
  const form = document.getElementById('schedule-form') as HTMLFormElement | null;

  if (!modal || !title) return Promise.resolve();

  if (form) form.reset();
  const scheduleIdEl = document.getElementById('schedule-id') as HTMLInputElement | null;
  if (scheduleIdEl) scheduleIdEl.value = scheduleId || '';
  title.textContent = scheduleId ? 'Edit Schedule' : 'Create Schedule';

  // Load operations into selector
  loadOperationsForSchedule();

  if (scheduleId) {
    return loadScheduleForEdit(scheduleId);
  }

  modal.classList.add('active');
  return Promise.resolve();
}

/**
 * Close schedule modal
 */
export function closeScheduleModal(): void {
  const modal = document.getElementById('schedule-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

/**
 * Load operations for schedule selector
 */
async function loadOperationsForSchedule(): Promise<void> {
  try {
    const response = await fetch('/api/maintenance/operations');
    const data = await response.json();

    const container = document.getElementById('schedule-operations');
    if (!container) return;

    container.innerHTML = data.operations.map((op: any) => `
      <label class="operation-checkbox">
        <input type="checkbox" name="operations" value="${op.id}">
        <div class="operation-checkbox-label">
          <div class="operation-checkbox-name">${escapeHtml(op.name)}</div>
          <div class="operation-checkbox-desc">${escapeHtml(op.description || '')}</div>
        </div>
      </label>
    `).join('');
  } catch (error) {
    console.error('Failed to load operations:', error);
  }
}

/**
 * Load schedule data for editing
 */
async function loadScheduleForEdit(scheduleId: string): Promise<void> {
  try {
    const response = await fetch(`/api/schedules/${scheduleId}`);
    const data = await response.json();

    if (!data.success) {
      showToast('Schedule not found', 'error');
      closeScheduleModal();
      return;
    }

    const schedule: Schedule = data.schedule;

    const nameEl = document.getElementById('schedule-name') as HTMLInputElement | null;
    const descEl = document.getElementById('schedule-description') as HTMLTextAreaElement | null;
    const freqEl = document.getElementById('schedule-frequency') as HTMLSelectElement | null;
    const timeEl = document.getElementById('schedule-time') as HTMLInputElement | null;
    const enabledEl = document.getElementById('schedule-enabled') as HTMLInputElement | null;

    if (nameEl) nameEl.value = schedule.name || '';
    if (descEl) descEl.value = schedule.description || '';
    if (freqEl && schedule.frequency) freqEl.value = schedule.frequency;
    if (timeEl && schedule.time_of_day) timeEl.value = schedule.time_of_day.substring(0, 5); // HH:MM
    if (enabledEl) enabledEl.checked = schedule.enabled;

    // Check selected operations
    schedule.operation_ids.forEach(opId => {
      const checkbox = document.querySelector<HTMLInputElement>(`input[name="operations"][value="${opId}"]`);
      if (checkbox) checkbox.checked = true;
    });

    // Set frequency-specific fields
    updateFrequencyOptions();

    if (schedule.frequency === 'weekly' && schedule.days_of_week) {
      schedule.days_of_week.forEach(day => {
        const checkbox = document.querySelector<HTMLInputElement>(`input[name="days"][value="${day}"]`);
        if (checkbox) checkbox.checked = true;
      });
    }

    if (schedule.frequency === 'monthly' && schedule.day_of_month) {
      const dayEl = document.getElementById('schedule-day') as HTMLInputElement | null;
      if (dayEl) dayEl.value = String(schedule.day_of_month);
    }

    const modal = document.getElementById('schedule-modal');
    if (modal) modal.classList.add('active');
  } catch (error) {
    console.error('Failed to load schedule:', error);
    showToast('Failed to load schedule', 'error');
  }
}

/**
 * Update frequency-specific form options
 */
export function updateFrequencyOptions(): void {
  const freqEl = document.getElementById('schedule-frequency') as HTMLSelectElement | null;
  const frequency = freqEl?.value || '';
  const daysSelector = document.getElementById('days-selector');
  const daySelector = document.getElementById('day-selector');

  if (daysSelector) {
    daysSelector.style.display = frequency === 'weekly' ? 'block' : 'none';
  }
  if (daySelector) {
    daySelector.style.display = frequency === 'monthly' ? 'block' : 'none';
  }
}

/**
 * Apply template to schedule modal
 */
export function applyScheduleTemplate(template: any): void {
  openScheduleModal();

  // Wait for modal to open and operations to load
  setTimeout(() => {
    const nameEl = document.getElementById('schedule-name') as HTMLInputElement | null;
    const descEl = document.getElementById('schedule-description') as HTMLTextAreaElement | null;
    const freqEl = document.getElementById('schedule-frequency') as HTMLSelectElement | null;
    const timeEl = document.getElementById('schedule-time') as HTMLInputElement | null;

    if (nameEl) nameEl.value = template.name;
    if (descEl) descEl.value = template.description;
    if (freqEl) freqEl.value = template.frequency;
    if (timeEl) timeEl.value = template.time_of_day.substring(0, 5);

    // Check operations
    template.operations.forEach((opId: string) => {
      const checkbox = document.querySelector<HTMLInputElement>(`input[name="operations"][value="${opId}"]`);
      if (checkbox) checkbox.checked = true;
    });

    // Set frequency options
    updateFrequencyOptions();

    if (template.days_of_week) {
      template.days_of_week.forEach((day: string) => {
        const checkbox = document.querySelector<HTMLInputElement>(`input[name="days"][value="${day}"]`);
        if (checkbox) checkbox.checked = true;
      });
    }

    if (template.day_of_month) {
      const dayEl = document.getElementById('schedule-day') as HTMLInputElement | null;
      if (dayEl) dayEl.value = template.day_of_month;
    }
  }, 100);
}

/**
 * Called when Schedule tab is shown
 */
export function onScheduleTabShow(): void {
  loadScheduleTemplates();
  loadSchedules();
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format schedule frequency
 */
function formatFrequency(schedule: Schedule): string {
  if (schedule.frequency === 'daily') {
    return 'Daily';
  } else if (schedule.frequency === 'weekly') {
    const days = schedule.days_of_week?.map(d => d.substring(0, 3).toUpperCase()).join(', ');
    return `Weekly (${days || 'No days'})`;
  } else if (schedule.frequency === 'monthly') {
    return `Monthly (Day ${schedule.day_of_month})`;
  }
  return schedule.frequency || 'Unknown';
}

/**
 * Format date/time for display
 */
function formatDateTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffMs < 0) {
      return date.toLocaleString();
    } else if (diffDays === 0 && diffHours < 24) {
      return `in ${diffHours}h`;
    } else if (diffDays < 7) {
      return `in ${diffDays}d`;
    } else {
      return date.toLocaleDateString();
    }
  } catch (e) {
    return isoString;
  }
}
