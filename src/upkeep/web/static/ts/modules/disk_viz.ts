/**
 * Disk Visualization Module
 * Interactive treemap visualization of disk usage using D3.js
 */

import * as d3 from 'd3';
import { showToast } from './ui.js';

interface DiskNode {
    name: string;
    path: string;
    value: number;
    sizeFormatted: string;  // from backend
    percentage: number;      // from backend
    totalSizeFormatted?: string;
    children?: DiskNode[];
}

interface DiskUsageResponse {
    success: boolean;
    data?: DiskNode;
    error?: string;
    warnings?: string[];
    scan_time_seconds?: number;
}

export class DiskVisualizer {
    private container: HTMLElement;
    private width: number;
    private height: number;
    private currentPath: string = '/';
    private pathHistory: string[] = [];
    private isLoading: boolean = false;
    private abortController: AbortController | null = null;
    private scanStartTime: number = 0;
    private elapsedTimerInterval: number | null = null;

    constructor(containerId: string) {
        const el = document.getElementById(containerId);
        if (!el) throw new Error(`Container ${containerId} not found`);
        this.container = el;
        this.width = 800;
        this.height = 500;
        
        this.buildUI();
    }

    private buildUI() {
        this.container.innerHTML = `
            <div class="disk-viz-wrapper">
                <div class="disk-viz-controls">
                    <div class="disk-viz-path-group">
                        <label for="disk-viz-path">Path:</label>
                        <input type="text" id="disk-viz-path" value="/" placeholder="/" />
                        <button id="disk-viz-scan" class="primary">Scan</button>
                        <button id="disk-viz-back" class="secondary" disabled>← Back</button>
                        <button id="disk-viz-home" class="secondary">🏠 Home</button>
                    </div>
                    <div class="disk-viz-options">
                        <label>
                            Depth: 
                            <select id="disk-viz-depth">
                                <option value="2">2 levels</option>
                                <option value="3" selected>3 levels</option>
                                <option value="4">4 levels</option>
                                <option value="5">5 levels</option>
                            </select>
                        </label>
                        <label>
                            Min size: 
                            <select id="disk-viz-min-size">
                                <option value="0">Show all</option>
                                <option value="1" selected>1 MB+</option>
                                <option value="10">10 MB+</option>
                                <option value="100">100 MB+</option>
                                <option value="1000">1 GB+</option>
                            </select>
                        </label>
                    </div>
                </div>
                
                <div class="disk-viz-quick-paths">
                    <span>Quick:</span>
                    <button class="quick-path-btn" data-path="/">/ (root)</button>
                    <button class="quick-path-btn" data-path="/Users">Users</button>
                    <button class="quick-path-btn" data-path="/Applications">Applications</button>
                    <button class="quick-path-btn" data-path="/Library">Library</button>
                </div>
                
                <div class="disk-viz-breadcrumbs" id="disk-viz-breadcrumbs"></div>
                
                <div class="disk-viz-chart" id="disk-viz-chart">
                    <div class="disk-viz-placeholder">
                        <div class="placeholder-icon">📊</div>
                        <h3>Disk Usage Visualization</h3>
                        <p>Click "Scan" to analyze disk usage and see an interactive treemap.</p>
                        <p class="hint">Click on folders in the treemap to drill down.</p>
                    </div>
                </div>
                
                <div class="disk-viz-legend" id="disk-viz-legend"></div>
                
                <div class="disk-viz-details" id="disk-viz-details" style="display: none;">
                    <h4>Selected:</h4>
                    <div id="disk-viz-selected-info"></div>
                </div>
            </div>
            
            <style>
                .disk-viz-wrapper {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .disk-viz-controls {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    align-items: center;
                    margin-bottom: 1rem;
                    justify-content: space-between;
                }
                
                .disk-viz-path-group {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .disk-viz-path-group input {
                    width: 250px;
                    padding: 0.5rem 0.75rem;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                }
                
                .disk-viz-options {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }
                
                .disk-viz-options select {
                    padding: 0.4rem 0.6rem;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                }
                
                .disk-viz-quick-paths {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    margin-bottom: 1rem;
                    flex-wrap: wrap;
                }
                
                .disk-viz-quick-paths span {
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                }
                
                .disk-viz-quick-paths .quick-path-btn {
                    padding: 0.35rem 0.75rem;
                    font-size: 0.8rem;
                    border-radius: 4px;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .disk-viz-quick-paths .quick-path-btn:hover {
                    background: var(--accent-color);
                    color: white;
                    border-color: var(--accent-color);
                }
                
                .disk-viz-breadcrumbs {
                    display: flex;
                    gap: 0.25rem;
                    align-items: center;
                    margin-bottom: 0.75rem;
                    font-size: 0.875rem;
                    flex-wrap: wrap;
                }
                
                .disk-viz-breadcrumbs .breadcrumb {
                    cursor: pointer;
                    color: var(--accent-color);
                    transition: color 0.2s;
                }
                
                .disk-viz-breadcrumbs .breadcrumb:hover {
                    text-decoration: underline;
                }
                
                .disk-viz-breadcrumbs .separator {
                    color: var(--text-secondary);
                }
                
                .disk-viz-chart {
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    min-height: 500px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    position: relative;
                }
                
                .disk-viz-placeholder {
                    text-align: center;
                    color: var(--text-secondary);
                    padding: 2rem;
                }
                
                .disk-viz-placeholder .placeholder-icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                    opacity: 0.5;
                }
                
                .disk-viz-placeholder h3 {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-primary);
                }
                
                .disk-viz-placeholder .hint {
                    font-size: 0.85rem;
                    margin-top: 1rem;
                    opacity: 0.7;
                }
                
                .disk-viz-loading {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1rem;
                }
                
                .disk-viz-loading .spinner {
                    width: 48px;
                    height: 48px;
                    border: 4px solid var(--border-color);
                    border-top-color: var(--accent-color);
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }
                
                .disk-viz-loading .spinner-pulse {
                    width: 60px;
                    height: 60px;
                    border: 4px solid var(--border-color);
                    border-top-color: var(--accent-color);
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite, pulse 2s ease-in-out infinite;
                    box-shadow: 0 0 0 0 rgba(var(--accent-color-rgb, 0, 122, 255), 0.4);
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                @keyframes pulse {
                    0%, 100% { 
                        box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
                        transform: rotate(0deg) scale(1);
                    }
                    50% { 
                        box-shadow: 0 0 0 15px rgba(59, 130, 246, 0);
                        transform: rotate(180deg) scale(1.05);
                    }
                }
                
                .cancel-scan-btn {
                    margin-top: 1rem;
                    padding: 0.5rem 1.25rem;
                    background: var(--bg-secondary);
                    color: var(--text-secondary);
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.875rem;
                    transition: all 0.2s;
                }
                
                .cancel-scan-btn:hover {
                    background: #fee2e2;
                    color: #dc2626;
                    border-color: #fca5a5;
                }
                
                .scan-elapsed {
                    font-variant-numeric: tabular-nums;
                }
                
                .disk-viz-legend {
                    display: flex;
                    gap: 1rem;
                    margin-top: 1rem;
                    flex-wrap: wrap;
                    justify-content: center;
                }
                
                .disk-viz-legend-item {
                    display: flex;
                    align-items: center;
                    gap: 0.35rem;
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                }
                
                .disk-viz-legend-color {
                    width: 12px;
                    height: 12px;
                    border-radius: 2px;
                }
                
                .disk-viz-details {
                    margin-top: 1rem;
                    padding: 1rem;
                    background: var(--bg-tertiary);
                    border-radius: 8px;
                }
                
                .disk-viz-details h4 {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }
                
                #disk-viz-selected-info {
                    font-family: monospace;
                    font-size: 0.875rem;
                }
                
                /* Treemap styles */
                .treemap-cell {
                    cursor: pointer;
                    transition: opacity 0.2s;
                }
                
                .treemap-cell:hover {
                    opacity: 0.85;
                }
                
                .treemap-label {
                    pointer-events: none;
                    font-size: 11px;
                    fill: white;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
                }
                
                .treemap-size {
                    pointer-events: none;
                    font-size: 9px;
                    fill: rgba(255,255,255,0.8);
                }
            </style>
        `;
        
        // Bind events
        this.container.querySelector('#disk-viz-scan')?.addEventListener('click', () => this.scan());
        this.container.querySelector('#disk-viz-back')?.addEventListener('click', () => this.goBack());
        this.container.querySelector('#disk-viz-home')?.addEventListener('click', () => this.goHome());
        
        const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
        pathInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.scan();
        });
        
        // Quick path buttons
        this.container.querySelectorAll('.disk-viz-quick-paths .quick-path-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const path = (btn as HTMLElement).dataset.path || '/';
                pathInput.value = path;
                this.currentPath = path;
                this.scan();
            });
        });
    }

    async scan() {
        if (this.isLoading) return;
        
        const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
        const depthSelect = this.container.querySelector('#disk-viz-depth') as HTMLSelectElement;
        const minSizeSelect = this.container.querySelector('#disk-viz-min-size') as HTMLSelectElement;
        
        const path = pathInput.value || '/';
        const depth = parseInt(depthSelect.value) || 3;
        const minSizeMb = parseInt(minSizeSelect.value) || 1;
        
        this.currentPath = path;
        this.isLoading = true;
        
        this.showLoading();
        
        // Use Server-Sent Events for streaming progress
        const url = `/api/disk/usage/stream?path=${encodeURIComponent(path)}&depth=${depth}&min_size_mb=${minSizeMb}`;
        
        try {
            const eventSource = new EventSource(url);
            this.abortController = new AbortController();
            
            // Store reference for cancellation
            const cleanup = () => {
                eventSource.close();
                this.isLoading = false;
                this.abortController = null;
                this.stopElapsedTimer();
            };
            
            // Handle abort
            this.abortController.signal.addEventListener('abort', () => {
                cleanup();
            });
            
            eventSource.addEventListener('progress', (event) => {
                const data = JSON.parse(event.data);
                this.updateProgress(data.currentDir, data.itemCount);
            });
            
            eventSource.addEventListener('complete', (event) => {
                const result = JSON.parse(event.data);
                const elapsedSecs = ((Date.now() - this.scanStartTime) / 1000).toFixed(1);
                const itemCount = result.itemCount || this.countNodes(result);
                
                this.renderTreemap(result as DiskNode);
                this.updateBreadcrumbs();
                
                if (result.warnings && result.warnings.length > 0) {
                    showToast(`Scan complete: ${itemCount} items in ${elapsedSecs}s (${result.warnings.length} warnings)`, 'warning');
                } else {
                    showToast(`Scan complete: ${itemCount} items, ${result.totalSizeFormatted || result.sizeFormatted} in ${elapsedSecs}s`, 'success');
                }
                
                cleanup();
            });
            
            eventSource.addEventListener('error', (event) => {
                // Check if it's a real error or just stream end
                if (eventSource.readyState === EventSource.CLOSED) {
                    return; // Normal close
                }
                
                // Try to parse error data
                try {
                    const data = JSON.parse((event as MessageEvent).data);
                    this.showError(data.error || 'Scan failed');
                } catch {
                    this.showError('Connection lost during scan');
                }
                cleanup();
            });
            
            eventSource.addEventListener('cancelled', () => {
                this.showCancelled();
                cleanup();
            });
            
            // Handle connection error
            eventSource.onerror = () => {
                if (this.isLoading) {
                    // Fallback to non-streaming endpoint
                    eventSource.close();
                    this.scanFallback(path, depth, minSizeMb);
                }
            };
            
        } catch (error) {
            // Fallback to non-streaming endpoint
            this.scanFallback(path, depth, minSizeMb);
        }
    }
    
    private updateProgress(currentDir: string, itemCount: number) {
        const pathEl = this.container.querySelector('.scan-path');
        const statusEl = this.container.querySelector('.scan-status');
        
        if (pathEl) {
            // Truncate long paths
            const maxLen = 50;
            const displayPath = currentDir.length > maxLen 
                ? '...' + currentDir.slice(-maxLen + 3) 
                : currentDir;
            pathEl.textContent = displayPath;
            pathEl.setAttribute('title', currentDir);
        }
        
        if (statusEl) {
            statusEl.textContent = `Scanning... ${itemCount.toLocaleString()} items found`;
        }
    }
    
    private showCancelled() {
        const chartEl = this.container.querySelector('#disk-viz-chart') as HTMLElement;
        chartEl.innerHTML = `
            <div class="disk-viz-placeholder">
                <div class="placeholder-icon">🚫</div>
                <h3>Scan Cancelled</h3>
                <p>The disk scan was cancelled.</p>
                <p class="hint">Click "Scan" to try again.</p>
            </div>
        `;
    }
    
    private async scanFallback(path: string, depth: number, minSizeMb: number) {
        // Fallback to non-streaming endpoint
        this.abortController = new AbortController();
        
        try {
            const response = await fetch(
                `/api/disk/usage?path=${encodeURIComponent(path)}&depth=${depth}&min_size_mb=${minSizeMb}`,
                { signal: this.abortController.signal }
            );
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
                this.showError(errorData.detail || `HTTP ${response.status}`);
                return;
            }
            
            const result = await response.json();
            const elapsedSecs = ((Date.now() - this.scanStartTime) / 1000).toFixed(1);
            
            if (result.error && !result.name) {
                this.showError(result.error);
            } else if (result.name) {
                const itemCount = this.countNodes(result);
                this.renderTreemap(result as DiskNode);
                this.updateBreadcrumbs();
                showToast(`Scan complete: ${itemCount} items, ${result.totalSizeFormatted || result.sizeFormatted} in ${elapsedSecs}s`, 'success');
            } else {
                this.showError('Invalid response from server');
            }
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }
            this.showError(`Failed to scan: ${error}`);
        } finally {
            this.isLoading = false;
            this.abortController = null;
            this.stopElapsedTimer();
        }
    }
    
    private countNodes(node: DiskNode): number {
        let count = 1;
        if (node.children) {
            for (const child of node.children) {
                count += this.countNodes(child);
            }
        }
        return count;
    }

    private showLoading() {
        const chartEl = this.container.querySelector('#disk-viz-chart') as HTMLElement;
        this.scanStartTime = Date.now();
        
        chartEl.innerHTML = `
            <div class="disk-viz-loading">
                <div class="spinner-pulse"></div>
                <div class="scan-status">Scanning disk structure...</div>
                <div class="scan-path" style="font-size: 0.85rem; color: var(--accent-color); font-family: monospace; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${this.currentPath}</div>
                <div class="scan-elapsed" style="font-size: 0.9rem; color: var(--text-primary); margin-top: 0.5rem;">
                    <span class="elapsed-icon">⏱️</span> <span id="elapsed-time">0s</span>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">This may take a moment for large directories</div>
                <button id="cancel-scan-btn" class="cancel-scan-btn">✕ Cancel</button>
            </div>
        `;
        
        // Start elapsed timer
        this.startElapsedTimer();
        
        // Bind cancel button
        const cancelBtn = chartEl.querySelector('#cancel-scan-btn');
        cancelBtn?.addEventListener('click', () => this.cancelScan());
    }
    
    private startElapsedTimer() {
        // Clear any existing timer
        if (this.elapsedTimerInterval) {
            clearInterval(this.elapsedTimerInterval);
        }
        
        const updateElapsed = () => {
            const elapsedEl = this.container.querySelector('#elapsed-time');
            if (elapsedEl && this.isLoading) {
                const elapsed = Math.floor((Date.now() - this.scanStartTime) / 1000);
                if (elapsed < 60) {
                    elapsedEl.textContent = `${elapsed}s`;
                } else {
                    const mins = Math.floor(elapsed / 60);
                    const secs = elapsed % 60;
                    elapsedEl.textContent = `${mins}m ${secs}s`;
                }
            }
        };
        
        updateElapsed();
        this.elapsedTimerInterval = window.setInterval(updateElapsed, 1000);
    }
    
    private stopElapsedTimer() {
        if (this.elapsedTimerInterval) {
            clearInterval(this.elapsedTimerInterval);
            this.elapsedTimerInterval = null;
        }
    }
    
    private cancelScan() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.isLoading = false;
        this.stopElapsedTimer();
        this.showCancelled();
        showToast('Scan cancelled', 'info');
    }

    private showError(message: string) {
        const chartEl = this.container.querySelector('#disk-viz-chart') as HTMLElement;
        chartEl.innerHTML = `
            <div class="disk-viz-placeholder">
                <div class="placeholder-icon">⚠️</div>
                <h3>Scan Error</h3>
                <p>${message}</p>
            </div>
        `;
        showToast(message, 'error');
    }

    private renderTreemap(data: DiskNode) {
        const chartEl = this.container.querySelector('#disk-viz-chart') as HTMLElement;
        chartEl.innerHTML = '';
        
        // Get actual dimensions
        const rect = chartEl.getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = Math.max(500, rect.height);
        
        // Create SVG
        const svg = d3.select(chartEl)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .style('font-family', '-apple-system, BlinkMacSystemFont, sans-serif');
        
        // Create hierarchy
        const root = d3.hierarchy(data)
            .sum(d => d.children ? 0 : d.value)
            .sort((a, b) => (b.value || 0) - (a.value || 0));
        
        // Create treemap layout
        const treemap = d3.treemap<DiskNode>()
            .size([this.width, this.height])
            .paddingOuter(3)
            .paddingInner(2)
            .paddingTop(20)
            .round(true);
        
        // Apply treemap layout - returns nodes with x0, y0, x1, y1
        const treemapRoot = treemap(root);
        
        // After treemap(), nodes have rectangular coordinates
        type TreemapNode = d3.HierarchyRectangularNode<DiskNode>;
        
        // Color scale
        const colorScale = d3.scaleOrdinal<string>()
            .domain(['Applications', 'Users', 'Library', 'System', 'private', 'opt', 'usr', 'var', 'other'])
            .range([
                '#FF6B6B', // Red - Applications
                '#4ECDC4', // Teal - Users
                '#45B7D1', // Blue - Library
                '#96CEB4', // Green - System
                '#FFEAA7', // Yellow - private
                '#DDA0DD', // Plum - opt
                '#98D8C8', // Mint - usr
                '#F7DC6F', // Gold - var
                '#B8B8B8'  // Gray - other
            ]);
        
        const getColor = (d: TreemapNode): string => {
            // Get top-level category
            let node: TreemapNode | null = d;
            while (node && node.depth > 1) {
                node = node.parent as TreemapNode | null;
            }
            const category = node?.data.name || 'other';
            return colorScale(category);
        };
        
        // Get descendants with proper typing
        const nodes = treemapRoot.descendants() as TreemapNode[];
        
        // Render cells
        const cell = svg.selectAll('g')
            .data(nodes.filter(d => d.depth > 0))
            .join('g')
            .attr('transform', d => `translate(${d.x0},${d.y0})`);
        
        // Rectangles
        cell.append('rect')
            .attr('class', 'treemap-cell')
            .attr('width', d => Math.max(0, d.x1 - d.x0))
            .attr('height', d => Math.max(0, d.y1 - d.y0))
            .attr('fill', d => getColor(d))
            .attr('stroke', 'var(--bg-secondary)')
            .attr('stroke-width', 1)
            .on('click', (event, d) => this.handleCellClick(d))
            .on('mouseover', (event, d) => this.showDetails(d))
            .on('mouseout', () => this.hideDetails())
            .append('title')
            .text(d => `${d.data.path}\n${d.data.sizeFormatted || 'N/A'}\n${(d.data.percentage || 0).toFixed(1)}%`);
        
        // Labels (only for cells large enough)
        cell.filter(d => (d.x1 - d.x0) > 60 && (d.y1 - d.y0) > 30)
            .append('text')
            .attr('class', 'treemap-label')
            .attr('x', 4)
            .attr('y', 14)
            .text(d => this.truncateLabel(d.data.name, d.x1 - d.x0 - 8));
        
        // Size labels (for larger cells)
        cell.filter(d => (d.x1 - d.x0) > 50 && (d.y1 - d.y0) > 45)
            .append('text')
            .attr('class', 'treemap-size')
            .attr('x', 4)
            .attr('y', 26)
            .text(d => d.data.sizeFormatted || '');
        
        // Update legend
        this.renderLegend(colorScale);
    }

    private truncateLabel(text: string, maxWidth: number): string {
        const charWidth = 7; // approximate
        const maxChars = Math.floor(maxWidth / charWidth);
        if (text.length <= maxChars) return text;
        return text.slice(0, maxChars - 2) + '…';
    }

    private handleCellClick(d: { data: DiskNode; children?: unknown; parent: unknown }) {
        if (d.children && d.data.path) {
            // Save current path for back navigation
            this.pathHistory.push(this.currentPath);
            this.currentPath = d.data.path;
            
            const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
            pathInput.value = d.data.path;
            
            // Enable back button
            const backBtn = this.container.querySelector('#disk-viz-back') as HTMLButtonElement;
            backBtn.disabled = false;
            
            this.scan();
        }
    }

    private showDetails(d: { data: DiskNode }) {
        const detailsEl = this.container.querySelector('#disk-viz-details') as HTMLElement;
        const infoEl = this.container.querySelector('#disk-viz-selected-info') as HTMLElement;
        
        detailsEl.style.display = 'block';
        infoEl.innerHTML = `
            <strong>${d.data.name}</strong><br>
            Path: ${d.data.path}<br>
            Size: ${d.data.sizeFormatted || 'N/A'}<br>
            Percent: ${(d.data.percentage || 0).toFixed(2)}% of parent
        `;
    }

    private hideDetails() {
        const detailsEl = this.container.querySelector('#disk-viz-details') as HTMLElement;
        detailsEl.style.display = 'none';
    }

    private renderLegend(colorScale: d3.ScaleOrdinal<string, string>) {
        const legendEl = this.container.querySelector('#disk-viz-legend') as HTMLElement;
        const categories = colorScale.domain();
        
        legendEl.innerHTML = categories.map(cat => `
            <div class="disk-viz-legend-item">
                <div class="disk-viz-legend-color" style="background: ${colorScale(cat)}"></div>
                <span>${cat}</span>
            </div>
        `).join('');
    }

    private updateBreadcrumbs() {
        const breadcrumbsEl = this.container.querySelector('#disk-viz-breadcrumbs') as HTMLElement;
        const parts = this.currentPath.split('/').filter(p => p);
        
        let html = `<span class="breadcrumb" data-path="/">/</span>`;
        let currentPath = '';
        
        parts.forEach((part, i) => {
            currentPath += '/' + part;
            html += `<span class="separator">/</span>`;
            html += `<span class="breadcrumb" data-path="${currentPath}">${part}</span>`;
        });
        
        breadcrumbsEl.innerHTML = html;
        
        // Bind click events
        breadcrumbsEl.querySelectorAll('.breadcrumb').forEach(el => {
            el.addEventListener('click', () => {
                const path = (el as HTMLElement).dataset.path || '/';
                const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
                pathInput.value = path;
                this.currentPath = path;
                this.scan();
            });
        });
    }

    private goBack() {
        if (this.pathHistory.length > 0) {
            const prevPath = this.pathHistory.pop()!;
            this.currentPath = prevPath;
            
            const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
            pathInput.value = prevPath;
            
            // Disable back button if no more history
            if (this.pathHistory.length === 0) {
                const backBtn = this.container.querySelector('#disk-viz-back') as HTMLButtonElement;
                backBtn.disabled = true;
            }
            
            this.scan();
        }
    }

    private goHome() {
        this.pathHistory = [];
        this.currentPath = '/';
        
        const pathInput = this.container.querySelector('#disk-viz-path') as HTMLInputElement;
        pathInput.value = '/';
        
        const backBtn = this.container.querySelector('#disk-viz-back') as HTMLButtonElement;
        backBtn.disabled = true;
        
        this.scan();
    }
}

// Export initialization function
export function initDiskViz(containerId: string): DiskVisualizer {
    return new DiskVisualizer(containerId);
}
