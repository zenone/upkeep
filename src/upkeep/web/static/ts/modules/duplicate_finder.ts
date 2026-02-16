/**
 * Duplicate Finder UI Module
 * 
 * Provides UI for scanning, viewing, and managing duplicate files.
 */

import { showToast } from "./ui.js";

interface FileInfo {
    path: string;
    mtime: string | null;
}

interface DuplicateGroup {
    hash: string;
    full_hash: string;
    size_bytes: number;
    size_formatted: string;
    file_count: number;
    potential_savings_bytes: number;
    potential_savings_formatted: string;
    files: FileInfo[];
}

interface ScanSummary {
    total_files_scanned: number;
    total_duplicates: number;
    total_wasted_bytes: number;
    total_wasted_formatted: string;
    duplicate_groups_count: number;
    scan_duration_seconds: number;
    errors_count: number;
}

interface ScanResult {
    scan_summary: ScanSummary;
    duplicate_groups: DuplicateGroup[];
    errors: string[];
}

interface ScanStatus {
    scan_id: string;
    status: "pending" | "running" | "complete" | "error";
    progress: {
        stage: string;
        current: number;
        total: number;
    };
    error: string | null;
}

export class DuplicateFinder {
    private container: HTMLElement;
    private pathInput!: HTMLInputElement;
    private minSizeSelect!: HTMLSelectElement;
    private includeHiddenCheckbox!: HTMLInputElement;
    private scanButton!: HTMLButtonElement;
    private progressContainer!: HTMLElement;
    private resultsContainer!: HTMLElement;
    
    private currentScanId: string | null = null;
    private scanResult: ScanResult | null = null;
    private selectedFiles: Set<string> = new Set();

    constructor(containerId: string) {
        const el = document.getElementById(containerId);
        if (!el) throw new Error(`Container ${containerId} not found`);
        this.container = el;
        
        this.buildUI();
        this.bindEvents();
    }

    private buildUI(): void {
        this.container.innerHTML = `
            <div class="duplicate-finder">
                <div class="scan-controls">
                    <div class="control-row">
                        <label for="dup-path">Path:</label>
                        <input type="text" id="dup-path" value="~" placeholder="Directory to scan" />
                        <button id="dup-home-btn" class="quick-path-btn">🏠 Home</button>
                        <button id="dup-downloads-btn" class="quick-path-btn">📥 Downloads</button>
                        <button id="dup-documents-btn" class="quick-path-btn">📄 Documents</button>
                    </div>
                    <div class="control-row">
                        <label for="dup-min-size">Min size:</label>
                        <select id="dup-min-size">
                            <option value="0.001">1 KB+</option>
                            <option value="0.1">100 KB+</option>
                            <option value="1" selected>1 MB+</option>
                            <option value="10">10 MB+</option>
                            <option value="100">100 MB+</option>
                        </select>
                        <label for="dup-hidden">
                            <input type="checkbox" id="dup-hidden" /> Include hidden files
                        </label>
                        <button id="dup-scan-btn" class="primary">🔍 Scan for Duplicates</button>
                    </div>
                </div>
                
                <div id="dup-progress" class="scan-progress" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">Preparing scan...</div>
                </div>
                
                <div id="dup-results" class="scan-results" style="display: none;">
                    <div class="results-summary">
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-files-scanned">0</span>
                            <span class="stat-label">Files Scanned</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-groups-found">0</span>
                            <span class="stat-label">Duplicate Groups</span>
                        </div>
                        <div class="summary-stat highlight">
                            <span class="stat-value" id="dup-wasted-space">0 B</span>
                            <span class="stat-label">Potential Savings</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-scan-time">0s</span>
                            <span class="stat-label">Scan Time</span>
                        </div>
                    </div>
                    
                    <div class="results-actions">
                        <button id="dup-export-csv" class="action-btn">📊 Export CSV</button>
                        <button id="dup-export-text" class="action-btn">📝 Export Text</button>
                        <button id="dup-delete-selected" class="action-btn danger" disabled>🗑️ Delete Selected (0)</button>
                    </div>
                    
                    <div id="dup-groups-container" class="groups-container">
                        <!-- Duplicate groups will be rendered here -->
                    </div>
                </div>
                
                <div id="dup-empty" class="empty-state" style="display: none;">
                    <div class="empty-icon">🎉</div>
                    <div class="empty-title">No Duplicates Found</div>
                    <div class="empty-text">Your files are unique! No duplicate files were detected.</div>
                </div>
            </div>
        `;

        // Get references to UI elements
        this.pathInput = this.container.querySelector("#dup-path") as HTMLInputElement;
        this.minSizeSelect = this.container.querySelector("#dup-min-size") as HTMLSelectElement;
        this.includeHiddenCheckbox = this.container.querySelector("#dup-hidden") as HTMLInputElement;
        this.scanButton = this.container.querySelector("#dup-scan-btn") as HTMLButtonElement;
        this.progressContainer = this.container.querySelector("#dup-progress") as HTMLElement;
        this.resultsContainer = this.container.querySelector("#dup-results") as HTMLElement;
    }

    private bindEvents(): void {
        // Quick path buttons
        this.container.querySelector("#dup-home-btn")?.addEventListener("click", () => {
            this.pathInput.value = "~";
        });
        this.container.querySelector("#dup-downloads-btn")?.addEventListener("click", () => {
            this.pathInput.value = "~/Downloads";
        });
        this.container.querySelector("#dup-documents-btn")?.addEventListener("click", () => {
            this.pathInput.value = "~/Documents";
        });

        // Scan button
        this.scanButton.addEventListener("click", () => this.startScan());

        // Export buttons
        this.container.querySelector("#dup-export-csv")?.addEventListener("click", () => this.exportResults("csv"));
        this.container.querySelector("#dup-export-text")?.addEventListener("click", () => this.exportResults("text"));

        // Delete button
        this.container.querySelector("#dup-delete-selected")?.addEventListener("click", () => this.deleteSelected());
    }

    private expandPath(path: string): string {
        // Expand ~ to user home (this happens on server side, but we can clean it up)
        if (path === "~" || path.startsWith("~/")) {
            // Let the server handle it
            return path;
        }
        return path;
    }

    async startScan(): Promise<void> {
        const path = this.expandPath(this.pathInput.value.trim() || "~");
        const minSizeMb = parseFloat(this.minSizeSelect.value);
        const includeHidden = this.includeHiddenCheckbox.checked;

        // Reset UI
        this.selectedFiles.clear();
        this.scanResult = null;
        this.showProgress();

        try {
            // Start the scan
            const startResponse = await fetch(
                `/api/duplicates/scan?paths=${encodeURIComponent(path)}&min_size_mb=${minSizeMb}&include_hidden=${includeHidden}`,
                { method: "POST" }
            );

            if (!startResponse.ok) {
                const error = await startResponse.json();
                throw new Error(error.detail || "Failed to start scan");
            }

            const { scan_id } = await startResponse.json();
            this.currentScanId = scan_id;

            // Poll for status
            await this.pollScanStatus(scan_id);
        } catch (e) {
            showToast(`Scan error: ${e}`, "error");
            this.hideProgress();
        }
    }

    private async pollScanStatus(scanId: string): Promise<void> {
        const pollInterval = 500; // ms
        const maxAttempts = 600; // 5 minutes max
        let attempts = 0;

        const poll = async (): Promise<void> => {
            try {
                const response = await fetch(`/api/duplicates/status/${scanId}`);
                if (!response.ok) {
                    throw new Error("Failed to get scan status");
                }

                const status: ScanStatus = await response.json();
                this.updateProgress(status);

                if (status.status === "complete") {
                    await this.loadResults(scanId);
                    return;
                }

                if (status.status === "error") {
                    throw new Error(status.error || "Scan failed");
                }

                // Continue polling
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, pollInterval);
                } else {
                    throw new Error("Scan timeout - taking too long");
                }
            } catch (e) {
                showToast(`${e}`, "error");
                this.hideProgress();
            }
        };

        await poll();
    }

    private updateProgress(status: ScanStatus): void {
        const progressFill = this.progressContainer.querySelector(".progress-fill") as HTMLElement;
        const progressText = this.progressContainer.querySelector(".progress-text") as HTMLElement;

        const stageNames: Record<string, string> = {
            scanning: "Scanning files...",
            size_grouping: "Grouping by size...",
            partial_hashing: "Computing partial hashes...",
            full_hashing: "Verifying duplicates...",
        };

        const stageName = stageNames[status.progress.stage] || status.progress.stage;
        
        if (status.progress.total > 0) {
            const percent = Math.round((status.progress.current / status.progress.total) * 100);
            progressFill.style.width = `${percent}%`;
            progressText.textContent = `${stageName} (${percent}%)`;
        } else {
            progressText.textContent = stageName;
        }
    }

    private async loadResults(scanId: string): Promise<void> {
        try {
            const response = await fetch(`/api/duplicates/results/${scanId}`);
            if (!response.ok) {
                throw new Error("Failed to load results");
            }

            const results: ScanResult = await response.json();
            this.scanResult = results;
            this.renderResults(results);
        } catch (e) {
            showToast(`Failed to load results: ${e}`, "error");
            this.hideProgress();
        }
    }

    private renderResults(results: ScanResult): void {
        this.hideProgress();

        if (results.duplicate_groups.length === 0) {
            // Show empty state
            (this.container.querySelector("#dup-empty") as HTMLElement).style.display = "block";
            this.resultsContainer.style.display = "none";
            return;
        }

        (this.container.querySelector("#dup-empty") as HTMLElement).style.display = "none";
        this.resultsContainer.style.display = "block";

        // Update summary stats
        const { scan_summary } = results;
        (this.container.querySelector("#dup-files-scanned") as HTMLElement).textContent = 
            scan_summary.total_files_scanned.toLocaleString();
        (this.container.querySelector("#dup-groups-found") as HTMLElement).textContent = 
            scan_summary.duplicate_groups_count.toString();
        (this.container.querySelector("#dup-wasted-space") as HTMLElement).textContent = 
            scan_summary.total_wasted_formatted;
        (this.container.querySelector("#dup-scan-time") as HTMLElement).textContent = 
            `${scan_summary.scan_duration_seconds.toFixed(1)}s`;

        // Render duplicate groups
        const groupsContainer = this.container.querySelector("#dup-groups-container") as HTMLElement;
        groupsContainer.innerHTML = "";

        results.duplicate_groups.forEach((group, index) => {
            const groupEl = this.createGroupElement(group, index);
            groupsContainer.appendChild(groupEl);
        });
    }

    private createGroupElement(group: DuplicateGroup, index: number): HTMLElement {
        const el = document.createElement("div");
        el.className = "duplicate-group";
        el.innerHTML = `
            <div class="group-header" data-index="${index}">
                <span class="group-toggle">▶</span>
                <span class="group-title">Group ${index + 1}: ${group.file_count} files</span>
                <span class="group-size">${group.size_formatted} each</span>
                <span class="group-savings">Save ${group.potential_savings_formatted}</span>
            </div>
            <div class="group-files" style="display: none;">
                ${group.files.map((file, fileIndex) => `
                    <div class="file-row">
                        <label>
                            <input type="checkbox" 
                                   class="file-checkbox" 
                                   data-path="${this.escapeHtml(file.path)}"
                                   data-group="${index}"
                                   ${fileIndex === 0 ? 'disabled title="Keep at least one copy"' : ''}>
                            <span class="file-path">${this.escapeHtml(file.path)}</span>
                        </label>
                        <span class="file-mtime">${file.mtime ? new Date(file.mtime).toLocaleDateString() : ""}</span>
                    </div>
                `).join("")}
                <div class="group-actions">
                    <button class="group-btn keep-newest" data-group="${index}">Keep Newest</button>
                    <button class="group-btn keep-oldest" data-group="${index}">Keep Oldest</button>
                    <button class="group-btn select-all" data-group="${index}">Select All (except first)</button>
                </div>
            </div>
        `;

        // Toggle expand/collapse
        const header = el.querySelector(".group-header") as HTMLElement;
        const files = el.querySelector(".group-files") as HTMLElement;
        const toggle = el.querySelector(".group-toggle") as HTMLElement;
        
        header.addEventListener("click", () => {
            const isExpanded = files.style.display !== "none";
            files.style.display = isExpanded ? "none" : "block";
            toggle.textContent = isExpanded ? "▶" : "▼";
        });

        // Checkbox events
        el.querySelectorAll(".file-checkbox").forEach(checkbox => {
            checkbox.addEventListener("change", (e) => {
                const input = e.target as HTMLInputElement;
                const path = input.dataset.path!;
                if (input.checked) {
                    this.selectedFiles.add(path);
                } else {
                    this.selectedFiles.delete(path);
                }
                this.updateDeleteButton();
            });
        });

        // Quick select buttons
        el.querySelector(".keep-newest")?.addEventListener("click", () => this.keepNewest(group, index, el));
        el.querySelector(".keep-oldest")?.addEventListener("click", () => this.keepOldest(group, index, el));
        el.querySelector(".select-all")?.addEventListener("click", () => this.selectAllExceptFirst(group, index, el));

        return el;
    }

    private keepNewest(group: DuplicateGroup, groupIndex: number, el: HTMLElement): void {
        // Find the newest file (most recent mtime)
        const filesWithMtime = group.files
            .map((f, i) => ({ file: f, index: i }))
            .filter(f => f.file.mtime)
            .sort((a, b) => new Date(b.file.mtime!).getTime() - new Date(a.file.mtime!).getTime());

        const newestIndex = filesWithMtime.length > 0 ? filesWithMtime[0]!.index : 0;
        
        el.querySelectorAll(".file-checkbox").forEach((checkbox, i) => {
            const input = checkbox as HTMLInputElement;
            if (!input.disabled) {
                input.checked = i !== newestIndex;
                const path = input.dataset.path!;
                if (input.checked) {
                    this.selectedFiles.add(path);
                } else {
                    this.selectedFiles.delete(path);
                }
            }
        });
        this.updateDeleteButton();
    }

    private keepOldest(group: DuplicateGroup, groupIndex: number, el: HTMLElement): void {
        // Find the oldest file
        const filesWithMtime = group.files
            .map((f, i) => ({ file: f, index: i }))
            .filter(f => f.file.mtime)
            .sort((a, b) => new Date(a.file.mtime!).getTime() - new Date(b.file.mtime!).getTime());

        const oldestIndex = filesWithMtime.length > 0 ? filesWithMtime[0]!.index : 0;
        
        el.querySelectorAll(".file-checkbox").forEach((checkbox, i) => {
            const input = checkbox as HTMLInputElement;
            if (!input.disabled) {
                input.checked = i !== oldestIndex;
                const path = input.dataset.path!;
                if (input.checked) {
                    this.selectedFiles.add(path);
                } else {
                    this.selectedFiles.delete(path);
                }
            }
        });
        this.updateDeleteButton();
    }

    private selectAllExceptFirst(group: DuplicateGroup, groupIndex: number, el: HTMLElement): void {
        el.querySelectorAll(".file-checkbox").forEach((checkbox) => {
            const input = checkbox as HTMLInputElement;
            if (!input.disabled) {
                input.checked = true;
                this.selectedFiles.add(input.dataset.path!);
            }
        });
        this.updateDeleteButton();
    }

    private updateDeleteButton(): void {
        const btn = this.container.querySelector("#dup-delete-selected") as HTMLButtonElement;
        btn.disabled = this.selectedFiles.size === 0;
        btn.textContent = `🗑️ Delete Selected (${this.selectedFiles.size})`;
    }

    private async deleteSelected(): Promise<void> {
        if (this.selectedFiles.size === 0 || !this.currentScanId) return;

        const count = this.selectedFiles.size;
        if (!confirm(`Move ${count} file(s) to Trash? This can be undone from Trash.`)) {
            return;
        }

        const btn = this.container.querySelector("#dup-delete-selected") as HTMLButtonElement;
        btn.disabled = true;
        btn.textContent = "Deleting...";

        try {
            const response = await fetch(
                `/api/duplicates/delete?scan_id=${this.currentScanId}`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ paths: Array.from(this.selectedFiles) }),
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Delete failed");
            }

            const result = await response.json();
            
            if (result.deleted_count > 0) {
                showToast(`Moved ${result.deleted_count} file(s) to Trash`, "success");
            }
            if (result.error_count > 0) {
                showToast(`Failed to delete ${result.error_count} file(s)`, "error");
            }

            // Re-scan to update results
            await this.startScan();
        } catch (e) {
            showToast(`Delete error: ${e}`, "error");
            this.updateDeleteButton();
        }
    }

    private async exportResults(format: "csv" | "text"): Promise<void> {
        if (!this.currentScanId) return;

        try {
            const response = await fetch(`/api/duplicates/results/${this.currentScanId}?format=${format}`);
            if (!response.ok) throw new Error("Export failed");

            const content = await response.text();
            const blob = new Blob([content], { type: format === "csv" ? "text/csv" : "text/plain" });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement("a");
            a.href = url;
            a.download = `duplicates-${this.currentScanId}.${format === "csv" ? "csv" : "txt"}`;
            a.click();
            
            URL.revokeObjectURL(url);
            showToast(`Exported as ${format.toUpperCase()}`, "success");
        } catch (e) {
            showToast(`Export error: ${e}`, "error");
        }
    }

    private showProgress(): void {
        this.progressContainer.style.display = "block";
        this.resultsContainer.style.display = "none";
        (this.container.querySelector("#dup-empty") as HTMLElement).style.display = "none";
        this.scanButton.disabled = true;
        this.scanButton.textContent = "Scanning...";
        
        // Reset progress bar
        const progressFill = this.progressContainer.querySelector(".progress-fill") as HTMLElement;
        progressFill.style.width = "0%";
    }

    private hideProgress(): void {
        this.progressContainer.style.display = "none";
        this.scanButton.disabled = false;
        this.scanButton.textContent = "🔍 Scan for Duplicates";
    }

    private escapeHtml(str: string): string {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
}
