import { showToast } from "./ui.js";

interface AppInfo {
    name: string;
    path: string;
    bundle_id: string;
    version: string;
    size_bytes: number;
    size_display: string;
    icon: string;
}

interface UninstallResult {
    success: boolean;
    app: string;
    dry_run: boolean;
    deleted_paths: string[];
    bytes_recovered: number;
}

export class AppUninstaller {
    private container: HTMLElement;
    private searchInput: HTMLInputElement;
    private appList: HTMLElement;
    private apps: AppInfo[] = [];

    constructor(containerId: string) {
        const el = document.getElementById(containerId);
        if (!el) throw new Error(`Container ${containerId} not found`);
        this.container = el;
        
        // Build UI structure
        this.container.innerHTML = `
            <div class="app-uninstaller">
                <div class="search-bar">
                    <input type="text" id="app-search" placeholder="Search installed applications..." />
                    <button id="refresh-apps" class="secondary">Refresh</button>
                </div>
                <div class="app-list-header">
                    <span>Name</span>
                    <span>Size</span>
                    <span>Action</span>
                </div>
                <div id="app-list-content" class="app-list-content">
                    <div class="loading">Loading apps...</div>
                </div>
            </div>
        `;
        
        this.searchInput = this.container.querySelector("#app-search") as HTMLInputElement;
        this.appList = this.container.querySelector("#app-list-content") as HTMLElement;
        
        this.searchInput.addEventListener("input", () => this.filterApps());
        this.container.querySelector("#refresh-apps")?.addEventListener("click", () => this.loadApps());
        
        this.loadApps();
    }

    async loadApps() {
        this.appList.innerHTML = '<div class="loading">Scanning applications...</div>';
        try {
            const response = await fetch("/api/apps");
            if (!response.ok) throw new Error("Failed to load apps");
            
            const data = await response.json();
            if (data.success) {
                this.apps = data.apps;
                this.renderApps(this.apps);
            } else {
                this.appList.innerHTML = `<div class="error">${data.error || "Unknown error"}</div>`;
            }
        } catch (e) {
            this.appList.innerHTML = `<div class="error">Error loading apps: ${e}</div>`;
        }
    }

    filterApps() {
        const query = this.searchInput.value.toLowerCase();
        const filtered = this.apps.filter(app => 
            app.name.toLowerCase().includes(query) || 
            app.bundle_id.toLowerCase().includes(query)
        );
        this.renderApps(filtered);
    }

    renderApps(apps: AppInfo[]) {
        if (apps.length === 0) {
            this.appList.innerHTML = '<div class="empty">No applications found</div>';
            return;
        }

        this.appList.innerHTML = "";
        
        apps.forEach(app => {
            const row = document.createElement("div");
            row.className = "app-row";
            row.innerHTML = `
                <div class="app-name">
                    <div class="name">${app.name}</div>
                    <div class="sub">${app.version} • ${app.path}</div>
                </div>
                <div class="app-size">${app.size_display}</div>
                <div class="app-actions">
                    <button class="danger" data-app="${app.name}">Uninstall</button>
                </div>
            `;
            
            row.querySelector("button")?.addEventListener("click", () => this.confirmUninstall(app));
            this.appList.appendChild(row);
        });
    }

    async confirmUninstall(app: AppInfo) {
        if (!confirm(`Are you sure you want to uninstall ${app.name}? This will move the app and its data to Trash.`)) {
            return;
        }
        
        try {
            const btn = this.appList.querySelector(`button[data-app="${app.name}"]`) as HTMLButtonElement;
            if (btn) {
                btn.disabled = true;
                btn.textContent = "Uninstalling...";
            }

            const response = await fetch(`/api/apps/${encodeURIComponent(app.name)}/uninstall?dry_run=false`, {
                method: "POST"
            });
            
            if (!response.ok) throw new Error("Uninstall failed");
            
            const result: UninstallResult = await response.json();
            if (result.success) {
                showToast(`Uninstalled ${app.name}. recovered ${this.formatBytes(result.bytes_recovered)}`, "success");
                // Remove from list
                this.apps = this.apps.filter(a => a.name !== app.name);
                this.renderApps(this.apps);
            } else {
                showToast(`Failed to uninstall ${app.name}`, "error");
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = "Uninstall";
                }
            }
        } catch (e) {
            showToast(`Error: ${e}`, "error");
            // Reload to reset state
            this.loadApps();
        }
    }

    formatBytes(bytes: number): string {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB", "TB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }
}
