/**
 * Dashboard module - System monitoring and health display
 */

import type { SystemInfoData, SparklineData, PreviousMetrics, ProcessInfo } from '../types';
import { showToast } from './ui';
import { animateValue } from './ui';

// ============================================================================
// Global State
// ============================================================================

export const sparklineData: SparklineData = {
  cpu: [],
  memory: [],
  disk: [],
  timestamps: []
};

export const previousMetrics: PreviousMetrics = {
  cpu: null,
  memory: null,
  disk: null
};

export let currentUsername: string | null = null;

// ============================================================================
// System Metrics & Health
// ============================================================================

/**
 * Load and display system information
 */
export async function loadSystemInfo(): Promise<void> {
  try {
    const response = await fetch('/api/system/info');
    const data: SystemInfoData = await response.json();

    // Store username globally for use in path buttons
    if (data.system && data.system.username) {
      currentUsername = data.system.username;
      // Also store on window for access from other modules
      (window as any)._currentUsername = data.system.username;
    }

    // Calculate trends
    const cpuTrend = calculateTrend(data.cpu.history);
    const memoryTrend = calculateTrend(data.memory.history);
    const diskTrend = calculateTrend(data.disk.history);

    // System metrics with animations
    const metricsDiv = document.getElementById('system-metrics');
    if (!metricsDiv) return;

    const isFirstLoad = previousMetrics.cpu === null;

    if (isFirstLoad) {
      // First load: build HTML structure
      metricsDiv.innerHTML = `
        <div class="metric-card">
          <h3>CPU Usage</h3>
          <div class="value" id="cpu-value">${data.cpu.percent.toFixed(1)}%</div>
          ${getTrendHTML(cpuTrend, data.cpu.history)}
          <div class="sparkline-container">
            <canvas id="cpu-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${data.cpu.count} cores</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${getStatusClass(data.cpu.percent)}" id="cpu-bar"
                 style="width: ${data.cpu.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Memory</h3>
          <div class="value" id="memory-value">${data.memory.percent.toFixed(1)}%</div>
          ${getTrendHTML(memoryTrend, data.memory.history)}
          <div class="sparkline-container">
            <canvas id="memory-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${data.memory.available_gb.toFixed(1)} GB available</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${getStatusClass(data.memory.percent)}" id="memory-bar"
                 style="width: ${data.memory.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Disk Space</h3>
          <div class="value" id="disk-value">${data.disk.percent.toFixed(1)}%</div>
          ${getTrendHTML(diskTrend, data.disk.history)}
          <div class="sparkline-container">
            <canvas id="disk-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${data.disk.free_gb.toFixed(1)} GB free of ${data.disk.total_gb.toFixed(1)} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${getStatusClass(data.disk.percent)}" id="disk-bar"
                 style="width: ${data.disk.percent}%"></div>
          </div>
        </div>
        ${data.network ? `
        <div class="metric-card">
          <h3>Network</h3>
          <div class="value" id="network-value">
            ↓ ${data.network.download_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="margin-top: 0.25rem;">
            ↑ ${data.network.upload_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="font-size: 0.75rem; margin-top: 0.5rem;">
            Total: ↓${data.network.total_recv_gb} GB / ↑${data.network.total_sent_gb} GB
          </div>
        </div>
        ` : ''}
        ${data.swap && data.swap.total_gb > 0 ? `
        <div class="metric-card">
          <h3>Swap</h3>
          <div class="value" id="swap-value">${data.swap.percent.toFixed(1)}%</div>
          <div class="subvalue">${data.swap.used_gb} GB used of ${data.swap.total_gb} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${getStatusClass(data.swap.percent)}" id="swap-bar"
                 style="width: ${data.swap.percent}%"></div>
          </div>
          ${data.swap.percent > 50 ? '<div class="warning">⚠️ High swap usage indicates memory pressure</div>' : ''}
        </div>
        ` : ''}
      `;

      console.log('First load - Memory bar HTML rendered');
      setTimeout(() => {
        const memBar = document.getElementById('memory-bar');
        if (memBar) {
          console.log('Memory bar found after first load:', {
            width: memBar.style.width,
            className: memBar.className,
            computedWidth: window.getComputedStyle(memBar).width,
            parent: memBar.parentElement
          });
        } else {
          console.error('Memory bar NOT found after first load!');
        }
      }, 100);
    } else {
      // Subsequent loads: animate values
      const cpuValueEl = document.getElementById('cpu-value');
      const memoryValueEl = document.getElementById('memory-value');
      const diskValueEl = document.getElementById('disk-value');

      if (cpuValueEl && previousMetrics.cpu !== null) {
        animateValue(cpuValueEl, previousMetrics.cpu, data.cpu.percent, 300, 1, '%');
      }
      if (memoryValueEl && previousMetrics.memory !== null) {
        animateValue(memoryValueEl, previousMetrics.memory, data.memory.percent, 300, 1, '%');
      }
      if (diskValueEl && previousMetrics.disk !== null) {
        animateValue(diskValueEl, previousMetrics.disk, data.disk.percent, 300, 1, '%');
      }

      // Update progress bars smoothly
      const cpuBar = document.getElementById('cpu-bar');
      const memoryBar = document.getElementById('memory-bar');
      const diskBar = document.getElementById('disk-bar');

      if (!memoryBar) {
        console.error('Memory bar element not found!');
      } else {
        console.log(`Memory bar found: width=${data.memory.percent}%, element:`, memoryBar);
      }

      if (cpuBar) {
        cpuBar.style.width = data.cpu.percent + '%';
        cpuBar.className = `progress-bar-fill ${getStatusClass(data.cpu.percent)}`;
      }
      if (memoryBar) {
        memoryBar.style.width = data.memory.percent + '%';
        memoryBar.className = `progress-bar-fill ${getStatusClass(data.memory.percent)}`;
      }
      if (diskBar) {
        diskBar.style.width = data.disk.percent + '%';
        diskBar.className = `progress-bar-fill ${getStatusClass(data.disk.percent)}`;
      }

      // Update trend indicators (recreate HTML for simplicity)
      const cpuCard = document.querySelector('.metric-card:nth-child(1)');
      const memoryCard = document.querySelector('.metric-card:nth-child(2)');
      const diskCard = document.querySelector('.metric-card:nth-child(3)');

      if (cpuCard) {
        const existingTrend = cpuCard.querySelector('.trend');
        if (existingTrend) existingTrend.remove();
        const valueDiv = cpuCard.querySelector('.value');
        if (valueDiv) {
          valueDiv.insertAdjacentHTML('afterend', getTrendHTML(cpuTrend, data.cpu.history));
        }
      }
      if (memoryCard) {
        const existingTrend = memoryCard.querySelector('.trend');
        if (existingTrend) existingTrend.remove();
        const valueDiv = memoryCard.querySelector('.value');
        if (valueDiv) {
          valueDiv.insertAdjacentHTML('afterend', getTrendHTML(memoryTrend, data.memory.history));
        }
      }
      if (diskCard) {
        const existingTrend = diskCard.querySelector('.trend');
        if (existingTrend) existingTrend.remove();
        const valueDiv = diskCard.querySelector('.value');
        if (valueDiv) {
          valueDiv.insertAdjacentHTML('afterend', getTrendHTML(diskTrend, data.disk.history));
        }
      }
    }

    // Store current metrics for next animation
    previousMetrics.cpu = data.cpu.percent;
    previousMetrics.memory = data.memory.percent;
    previousMetrics.disk = data.disk.percent;

    // Fetch full sparkline data and draw
    fetch('/api/system/sparkline')
      .then(res => res.json())
      .then(sparkData => {
        console.log('Sparkline data received:', sparkData);
        if (sparkData && sparkData.cpu && sparkData.cpu.length >= 2) {
          drawSparkline('cpu-sparkline', sparkData.cpu, '#ff6961');
          drawSparkline('memory-sparkline', sparkData.memory, '#0a84ff');
          drawSparkline('disk-sparkline', sparkData.disk, '#ff9500');
        } else {
          console.warn('Sparkline data insufficient:', sparkData);
        }
      })
      .catch(err => console.error('Error loading sparkline data:', err));

    // System info
    const systemInfoDiv = document.getElementById('system-info');
    if (systemInfoDiv) {
      systemInfoDiv.innerHTML = `
        <dl class="info-item">
          <dt>Total Memory</dt>
          <dd>${data.memory.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Memory</dt>
          <dd>${data.memory.used_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Total Disk</dt>
          <dd>${data.disk.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Disk</dt>
          <dd>${data.disk.used_gb.toFixed(1)} GB</dd>
        </dl>
      `;
    }

    // Maintenance status - Load last run time from API
    const diskWarning = data.disk.percent > 80
      ? `<div class="warning">⚠️ Disk usage is high (${data.disk.percent.toFixed(1)}%). Consider running cleanup operations.</div>`
      : '';
    const memoryWarning = data.memory.percent > 80
      ? `<div class="warning">⚠️ Memory usage is high (${data.memory.percent.toFixed(1)}%).</div>`
      : '';

    // Fetch last maintenance run time
    await loadLastMaintenanceRun(diskWarning, memoryWarning);

  } catch (error) {
    const metricsDiv = document.getElementById('system-metrics');
    if (metricsDiv) {
      metricsDiv.innerHTML = `<div class="error">Error loading system info: ${(error as Error).message}</div>`;
    }
  }
}

/**
 * Get color for health score
 */
function getHealthColor(score: number, overall: string): string {
  // Use overall status for consistent coloring
  switch (overall) {
    case 'excellent': return '#32d74b';  // Green
    case 'good': return '#0a84ff';       // Blue
    case 'fair': return '#ff9500';       // Orange
    case 'poor': return '#ff3b30';       // Red
    default:
      // Fallback to score-based coloring
      if (score >= 90) return '#32d74b';
      if (score >= 70) return '#0a84ff';
      if (score >= 50) return '#ff9500';
      return '#ff3b30';
  }
}

/**
 * Generate SVG health gauge
 */
function generateHealthGaugeSVG(score: number, overall: string): string {
  const size = 180;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;

  // Arc spans 240 degrees (from 150° to 390°, or -30° to 210° from top)
  const startAngle = 150;  // degrees
  const endAngle = 390;    // degrees
  const totalArc = endAngle - startAngle;  // 240 degrees

  // Calculate the arc length based on score (0-100)
  const scoreAngle = startAngle + (totalArc * score / 100);

  // Convert to radians and calculate path
  const toRadians = (deg: number) => (deg - 90) * Math.PI / 180;

  const startX = center + radius * Math.cos(toRadians(startAngle));
  const startY = center + radius * Math.sin(toRadians(startAngle));
  const endX = center + radius * Math.cos(toRadians(endAngle));
  const endY = center + radius * Math.sin(toRadians(endAngle));
  const scoreX = center + radius * Math.cos(toRadians(scoreAngle));
  const scoreY = center + radius * Math.sin(toRadians(scoreAngle));

  // Large arc flag (1 if arc > 180 degrees)
  const bgLargeArc = totalArc > 180 ? 1 : 0;
  const scoreLargeArc = (scoreAngle - startAngle) > 180 ? 1 : 0;

  const color = getHealthColor(score, overall);

  // Background track path
  const bgPath = `M ${startX} ${startY} A ${radius} ${radius} 0 ${bgLargeArc} 1 ${endX} ${endY}`;

  // Score arc path
  const scorePath = score > 0
    ? `M ${startX} ${startY} A ${radius} ${radius} 0 ${scoreLargeArc} 1 ${scoreX} ${scoreY}`
    : '';

  // Status emoji
  const emoji = overall === 'excellent' ? '✨' :
                overall === 'good' ? '👍' :
                overall === 'fair' ? '⚠️' : '🔴';

  return `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" class="health-gauge-svg">
      <!-- Background track -->
      <path
        d="${bgPath}"
        fill="none"
        stroke="var(--border-light)"
        stroke-width="${strokeWidth}"
        stroke-linecap="round"
      />
      <!-- Score arc with gradient -->
      <defs>
        <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:${color};stop-opacity:0.7" />
          <stop offset="100%" style="stop-color:${color};stop-opacity:1" />
        </linearGradient>
      </defs>
      ${score > 0 ? `
      <path
        d="${scorePath}"
        fill="none"
        stroke="url(#healthGradient)"
        stroke-width="${strokeWidth}"
        stroke-linecap="round"
        class="health-gauge-arc"
      />
      ` : ''}
      <!-- Center score text -->
      <text x="${center}" y="${center - 10}" text-anchor="middle" class="health-gauge-score" fill="${color}">
        ${score}
      </text>
      <text x="${center}" y="${center + 20}" text-anchor="middle" class="health-gauge-label">
        ${overall.toUpperCase()}
      </text>
      <text x="${center}" y="${center + 45}" text-anchor="middle" class="health-gauge-emoji">
        ${emoji}
      </text>
    </svg>
  `;
}

/**
 * Load and display system health score with visual gauge
 */
export async function loadHealthScore(): Promise<void> {
  const healthDiv = document.getElementById('health-score');
  if (!healthDiv) return;

  try {
    const response = await fetch('/api/system/health');
    const data = await response.json();

    // Generate SVG gauge
    const gaugeSVG = generateHealthGaugeSVG(data.score, data.overall);

    // Build issues list
    let issuesHTML = '';
    if (data.issues && data.issues.length > 0) {
      issuesHTML = `
        <div class="health-issues">
          <h4>Issues Detected:</h4>
          <ul class="health-issues-list">
            ${data.issues.map((issue: string) => `
              <li class="${issue.includes('Critical') ? 'critical' : 'warning'}">
                ${issue.includes('Critical') ? '🔴' : '⚠️'} ${issue}
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    } else {
      issuesHTML = `
        <div class="health-all-clear">
          <span class="health-check-icon">✓</span>
          All systems healthy
        </div>
      `;
    }

    healthDiv.innerHTML = `
      <div class="health-gauge-container">
        ${gaugeSVG}
      </div>
      ${issuesHTML}
    `;
  } catch (error) {
    healthDiv.innerHTML = `<div class="error">Error loading health score: ${(error as Error).message}</div>`;
  }
}

/**
 * Load and display top resource consumers
 */
export async function loadTopProcesses(): Promise<void> {
  const processesDiv = document.getElementById('top-processes');
  if (!processesDiv) return;

  try {
    const response = await fetch('/api/system/processes?limit=3');
    const data = await response.json();

    let html = '<div class="process-section">';
    html += '<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top CPU Consumers</h3>';
    html += '<div class="process-list">';
    data.top_cpu.forEach((proc: ProcessInfo, idx: number) => {
      html += `
        <div class="process-item">
          <div class="process-rank">${idx + 1}</div>
          <div class="process-name">${proc.name}</div>
          <div class="process-value">${proc.cpu_percent}%</div>
        </div>
      `;
    });
    html += '</div></div>';

    html += '<div class="process-section" style="margin-top: 1.5rem;">';
    html += '<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top Memory Consumers</h3>';
    html += '<div class="process-list">';
    data.top_memory.forEach((proc: ProcessInfo, idx: number) => {
      html += `
        <div class="process-item">
          <div class="process-rank">${idx + 1}</div>
          <div class="process-name">${proc.name}</div>
          <div class="process-value">${proc.memory_mb.toFixed(0)} MB</div>
        </div>
      `;
    });
    html += '</div></div>';

    processesDiv.innerHTML = html;
  } catch (error) {
    processesDiv.innerHTML = `<div class="error">Error loading processes: ${(error as Error).message}</div>`;
  }
}

/**
 * Load and display last maintenance run time
 */
export async function loadLastMaintenanceRun(diskWarning: string = '', memoryWarning: string = ''): Promise<void> {
  const statusDiv = document.getElementById('maintenance-status');
  if (!statusDiv) return;

  try {
    const response = await fetch('/api/maintenance/last-run');
    const data = await response.json();

    let lastRunText: string;
    if (data.status === 'never') {
      lastRunText = '<strong>Never</strong>';
    } else {
      const lastRun = data.global_last_run || 'Unknown';
      const relative = data.global_last_run_relative || '';
      lastRunText = `<strong>${lastRun}</strong> <span style="color: var(--text-secondary);">(${relative})</span>`;
    }

    statusDiv.innerHTML = `
      <p>Last maintenance run: ${lastRunText}</p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${diskWarning}
      ${memoryWarning}
      ${!diskWarning && !memoryWarning ? '<div class="success">✓ System is running smoothly</div>' : ''}
    `;
  } catch (error) {
    // Fallback to "Never" if API fails
    statusDiv.innerHTML = `
      <p>Last maintenance run: <strong>Never</strong> <span style="color: var(--text-secondary);">(check logs)</span></p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${diskWarning}
      ${memoryWarning}
      ${!diskWarning && !memoryWarning ? '<div class="success">✓ System is running smoothly</div>' : ''}
    `;
  }
}

// ============================================================================
// Sparkline & Trend Visualization
// ============================================================================

/**
 * Draw sparkline chart on canvas
 */
export function drawSparkline(canvasId: string, data: number[], color: string = '#0a84ff'): void {
  const canvas = document.getElementById(canvasId) as HTMLCanvasElement | null;
  if (!canvas) {
    console.warn(`Canvas not found: ${canvasId}`);
    return;
  }
  if (!data || data.length < 2) {
    console.warn(`Insufficient data for ${canvasId}: ${data ? data.length : 0} points`);
    return;
  }

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const width = canvas.width;
  const height = canvas.height;

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  // Find min/max for scaling
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1; // Avoid division by zero

  // Draw line
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineJoin = 'round';

  data.forEach((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;

    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.stroke();
}

/**
 * Calculate trend from history array
 */
export function calculateTrend(history: number[]): 'up' | 'down' | 'neutral' {
  if (!history || history.length < 2) return 'neutral';

  const recent = history[history.length - 1]!;
  const previous = history[history.length - 2]!;
  const delta = recent - previous;

  if (Math.abs(delta) < 0.5) return 'neutral'; // Threshold for neutral
  return delta > 0 ? 'up' : 'down';
}

/**
 * Get trend display HTML
 */
export function getTrendHTML(trend: 'up' | 'down' | 'neutral', history: number[]): string {
  if (!history || history.length < 2) return '';

  const recent = history[history.length - 1]!;
  const previous = history[history.length - 2]!;
  const delta = Math.abs(recent - previous).toFixed(1);

  const arrows: Record<string, string> = {
    up: '↑',
    down: '↓',
    neutral: '•'
  };

  return `<span class="trend ${trend}">${arrows[trend]} ${delta}%</span>`;
}

/**
 * Get status class based on percentage
 */
export function getStatusClass(percent: number): string {
  if (percent > 90) return 'danger';
  if (percent > 75) return 'warning';
  return '';
}

/**
 * Run a quick health check - comprehensive system scan with recommendations
 * This is the "one-click" feature that makes Upkeep competitive with CleanMyMac X
 */
export async function runQuickHealthCheck(): Promise<void> {
  const btn = document.querySelector('.hero-card button') as HTMLButtonElement;
  const originalText = btn?.innerHTML;
  
  try {
    // Update button to show loading state
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '🔄 Scanning...';
    }
    
    // Show toast
    showToast('Starting health check...', 'info');
    
    // Run the preflight/doctor check which scans the system
    const response = await fetch('/api/maintenance/doctor', {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    
    const result = await response.json();
    
    // Reload all dashboard data
    await Promise.all([
      loadSystemInfo(),
      loadHealthScore(),
      loadTopProcesses()
    ]);
    
    // Show results
    const issueCount = result.issues?.length ?? 0;
    if (issueCount === 0) {
      showToast('✅ Your Mac is healthy! No issues found.', 'success');
    } else {
      showToast(`Found ${issueCount} item${issueCount > 1 ? 's' : ''} to review. Check the Maintenance tab.`, 'warning');
      // Switch to maintenance tab to show issues
      const switchTab = (window as any).showTab;
      if (switchTab) {
        setTimeout(() => switchTab('maintenance'), 1500);
      }
    }
    
  } catch (error) {
    console.error('Health check error:', error);
    showToast('Health check encountered an error. Please try again.', 'error');
  } finally {
    // Restore button
    if (btn && originalText) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}
