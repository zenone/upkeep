# App Uninstaller Design

## Goal
Provide a "Michelin-star" quality application uninstaller for macOS that safely and completely removes applications and their associated artifacts (caches, preferences, containers, support files), similar to tools like AppCleaner or Hazel, but with a transparent, developer-first approach.

## User Stories
1.  **Discovery**: User views a list of installed applications with metadata (size, last used, version).
2.  **Search**: User searches for an app by name.
3.  **Analysis**: User selects an app and sees a detailed breakdown of all associated files and their sizes.
4.  **Safety**: User is warned if they attempt to delete a system app or a critical tool.
5.  **Removal**: User confirms deletion, and files are moved to Trash (safe delete) or permanently removed (if configured).

## Architecture

### 1. `AppFinder` Service
Responsible for locating applications and their related files.

**Core Logic:**
-   **Input**: Application path (e.g., `/Applications/Slack.app`) or Bundle ID.
-   **Heuristics**:
    -   **Bundle ID Matching**: The primary method. Parse `Info.plist` to get `CFBundleIdentifier` (e.g., `com.tinyspeck.slackmacgap`).
    -   **Name Matching**: Fallback for files that don't use the bundle ID (e.g., `~/Library/Application Support/Slack`).
-   **Search Locations**:
    -   `~/Library/Application Support/`
    -   `~/Library/Caches/`
    -   `~/Library/Containers/` (Sandboxed apps)
    -   `~/Library/Group Containers/`
    -   `~/Library/Preferences/`
    -   `~/Library/Logs/`
    -   `~/Library/Saved Application State/`
    -   `~/Library/WebKit/`
    -   `/Library/` (System-wide support/preferences - requires elevated output context, maybe read-only for v1)
    -   `/var/db/receipts/` (BOM files - useful for finding installed files)

**API Contract:**

```python
@dataclass
class AppArtifact:
    path: Path
    kind: str  # "app", "cache", "config", "data", "log", "container"
    size_bytes: int
    reason: str  # "Bundle ID match", "Name match"

@dataclass
class AppScanResult:
    app_info: Dict[str, Any]  # name, version, bundle_id, icon_path
    artifacts: List[AppArtifact]
    total_size_bytes: int

class AppFinder:
    def scan(self, app_path: str) -> AppScanResult:
        ...
    
    def find_all_apps(self) -> List[Dict[str, Any]]:
        """Returns list of all apps in standard locations."""
        ...
```

### 2. `AppUninstaller` Service
Responsible for the actual removal process.

**Core Logic:**
-   **Dry Run**: Always available and default.
-   **Safety Checks**:
    -   **System App Protection**: Prevent deletion of `/System/Applications/*` and protected apps (Safari, Mail).
    -   **Running App Check**: Warn if the app is currently running.
-   **Deletion Method**:
    -   Prefer `send2trash` (move to Trash) for safety.
    -   Optional: Secure delete / `rm` (not recommended for v1).

**API Contract:**

```python
class AppUninstaller:
    def uninstall(self, artifacts: List[AppArtifact], dry_run: bool = True) -> Dict[str, Any]:
        """
        Executes uninstallation.
        Returns report of deleted files and any errors.
        """
        ...
```

### 3. Safety & Whitelisting
We must prevent users from accidentally deleting critical system components or the Upkeep tool itself.

**Protected Paths:**
-   `/System/*`
-   `/usr/*`
-   `/bin/*`, `/sbin/*`

**Protected Bundle IDs:**
-   `com.apple.*` (Need nuance here, some Apple apps are user-removable, but core system ones aren't)
-   `com.upkeep.*` (Self-protection)

## CLI Interface
Integration with the existing `upkeep` CLI.

```bash
upkeep uninstall "Slack" --dry-run
upkeep uninstall /Applications/Slack.app
```

## Web UI
-   **List View**: Searchable table of apps.
-   **Detail View**: Tree view of artifacts with checkboxes (allow user to uncheck specific files they want to keep).
-   **Action**: "Uninstall" button with confirmation modal showing total size to be reclaimed.

## Implementation Plan (TDD)

1.  **Phase 1: Discovery (The `AppFinder`)**
    -   Implement `find_all_apps` to list applications.
    -   Implement `Info.plist` parsing to extract Bundle IDs.
    -   Test against common apps (VS Code, Slack, Chrome).

2.  **Phase 2: The Scanner (Artifact Discovery)**
    -   Implement heuristics for finding related files.
    -   Write tests with mocked file system structures.
    -   Verify "Zap-like" accuracy (compare against manual findings).

3.  **Phase 3: The Uninstaller (Action)**
    -   Implement `AppUninstaller` with `dry_run`.
    -   Implement `trash` integration.
    -   Add safety checks for system apps.

4.  **Phase 4: Interface**
    -   Add CLI command.
    -   Build Web UI components.

## Zap-like Features (Michelin Star Touch)
-   **Leftover Watcher**: (Future P2) Daemon that detects when an app is moved to Trash and offers to cleanup leftovers.
-   **Quick Look**: Integration in UI to preview files before deleting.
