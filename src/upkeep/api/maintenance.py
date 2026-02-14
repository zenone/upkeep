"""
Secure Maintenance API - Job Queue Pattern

API-First Design: Clean interface for maintenance operations.
Used by Web GUI, CLI, and Web.
"""

import asyncio
import json
import re
import time
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

from upkeep.core.exceptions import (
    DaemonNotAvailableError,
    OperationNotFoundError,
)

from .base import BaseAPI


def clean_output_line(text: str) -> str:
    """Clean control characters from output text.

    Removes all terminal control characters that can cause text truncation
    or corruption when displayed in web UI.

    Business logic:
    - Terminal output often contains ANSI codes for colors, cursor movement,
      carriage returns for progress updates, backspaces, etc.
    - These control characters corrupt text when displayed in HTML
    - Example: "Installing...\rInstalled" becomes "Installed..." (carriage return overwrites)
    - Example: "\x1b[32mSuccess\x1b[0m" becomes "Success" (removes color codes)
    - Example: "abc\b\bxy" becomes "abxy" (removes backspaces that delete chars)
    - Example: "\x1b[2K" (clear line command) is removed

    Root cause investigation (Task #140):
    - Truncation like "Logmaintenance" (missing "file: /var/root/Library/Logs/mac-")
      was caused by terminal control codes (backspace, cursor positioning)
      that work in terminals but corrupt HTML text display

    Args:
        text: Raw output text that may contain control characters

    Returns:
        Cleaned text safe for display in web UI
    """
    if not text:
        return text

    # Remove carriage returns (they cause text to overwrite itself)
    text = text.replace('\r', '')

    # Remove backspaces (they delete previous characters in terminals)
    text = text.replace('\b', '')

    # Remove ALL ANSI escape sequences (not just colors)
    # This includes: colors, cursor movement, clear screen/line, etc.
    # Pattern 1: CSI sequences (Control Sequence Introducer)
    #   \x1b\[ - ESC[ sequence start
    #   [0-9;?]* - zero or more digits, semicolons, or question marks (parameters)
    #   [a-zA-Z] - command letter (m=SGR/color, K=EL/erase line, H=CUP/cursor pos, etc.)
    ansi_escape = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')
    text = ansi_escape.sub('', text)

    # Pattern 2: OSC sequences (Operating System Command)
    #   \x1b\] - ESC] sequence start (used for window title, etc.)
    #   [^\x07\x1b]* - any chars except BEL or ESC
    #   (\x07|\x1b\\) - terminated by BEL or ESC\
    osc_escape = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)')
    text = osc_escape.sub('', text)

    # Remove other control characters (except newline \n and tab \t which we want to keep)
    # \x00-\x08: NULL through backspace
    # \x0B-\x0C: vertical tab, form feed
    # \x0E-\x1F: shift out through unit separator
    # \x7F: DEL
    control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    text = control_chars.sub('', text)

    return text


class MaintenanceAPI(BaseAPI):
    """API for system maintenance operations using secure job queue.

    Provides:
    - List available maintenance operations
    - Run operations via secure job queue (daemon)
    - Stream operation progress in real-time
    - Cancel/skip operations
    """

    # Job queue directory (shared with root daemon)
    QUEUE_DIR = Path("/var/local/upkeep-jobs")

    # Define all operations with metadata
    OPERATIONS = {
        # System Updates
        "macos-check": {
            "id": "macos-check",
            "name": "Check macOS Updates",
            "description": "Check for available macOS system updates",
            "guidance": "Why: Apple releases security patches, bug fixes, and feature updates regularly. Staying informed helps plan maintenance. When: Run weekly to check for critical security updates, before planning major projects, or when Apple announces important fixes. After: Shows list of available updates instantly. No changes made (read-only check). You can then decide whether to install.",
            "category": "Update Operations",
            "safe": True,
            "recommended": True,
        },
        "macos-install": {
            "id": "macos-install",
            "name": "Install macOS Updates",
            "description": "Install available macOS system updates",
            "guidance": "Why: macOS updates fix critical security vulnerabilities, patch bugs, and improve stability. Delayed updates leave your Mac vulnerable. When: Run when Check Updates shows critical security patches, during planned maintenance (not before important work), or when experiencing bugs that updates might fix. After: Mac will update (15-60 min) and may require restart. Backup first. Some apps may need updating if compatibility changes.",
            "category": "Update Operations",
            "safe": False,
            "recommended": False,
        },
        "brew-update": {
            "id": "brew-update",
            "name": "Update Homebrew",
            "description": "Update Homebrew packages",
            "guidance": "Why: Homebrew packages receive security fixes, bug fixes, and new features regularly. Outdated packages have known vulnerabilities. When: Run weekly for security, before installing new packages (to avoid conflicts), or when brew commands fail. After: All Homebrew packages updated to latest versions. Takes 5-15 minutes depending on number of packages. Some apps may look slightly different with new versions.",
            "category": "Update Operations",
            "safe": True,
            "recommended": True,
        },
        "brew-cleanup": {
            "id": "brew-cleanup",
            "name": "Cleanup Homebrew",
            "description": "Remove old versions and link packages",
            "guidance": "Why: Homebrew keeps old versions of packages which waste disk space. Unlinked packages aren't accessible via PATH. When: Run monthly to free disk space, when 'brew doctor' shows warnings about unlinked kegs, or when commands aren't found after installing via brew. After: Old package versions removed, unused dependencies deleted, all packages linked. Frees 1-5GB typically. Takes 2-5 minutes.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "mas-update": {
            "id": "mas-update",
            "name": "Update App Store Apps",
            "description": "Update Mac App Store applications",
            "guidance": "Why: App Store apps receive bug fixes, security patches, and new features through updates. Outdated apps may crash or have vulnerabilities. When: Run weekly, when you see update notifications, or before important work (to ensure apps are stable). After: All App Store apps updated to latest versions. Takes 5-20 minutes depending on update sizes. Some apps may require reopening to see changes.",
            "category": "Update Operations",
            "safe": True,
            "recommended": True,
        },

        # Disk Operations
        "disk-verify": {
            "id": "disk-verify",
            "name": "Verify Disk",
            "description": "Verify disk health and integrity",
            "guidance": "Why: Disks can develop file system errors from crashes, power loss, or hardware issues. Early detection prevents data loss. When: Run monthly for prevention, before major system updates, when Mac crashes frequently, files won't open, or system feels slow. After: Shows if disk is healthy or has errors. Takes 5-10 minutes. If errors found, run Repair Disk. No changes made to disk (read-only check).",
            "category": "Disk / Filesystem",
            "safe": True,
            "recommended": True,
        },
        "disk-repair": {
            "id": "disk-repair",
            "name": "Repair Disk",
            "description": "Repair disk errors if found",
            "guidance": "Why: Disk errors corrupt files and cause crashes if left unfixed. First Aid repairs file system issues. When: Run ONLY after Verify Disk shows errors, when Mac crashes frequently, apps won't open, or files become corrupted. Don't run preventively. After: Attempts to fix file system errors (15-30 min). May require Recovery Mode for boot disk. Backup critical files first. If repair fails repeatedly, disk may be failing physically.",
            "category": "Disk / Filesystem",
            "safe": False,
            "recommended": False,
        },
        "smart-check": {
            "id": "smart-check",
            "name": "Check SMART Status",
            "description": "Check disk SMART health status",
            "guidance": "Why: SMART (Self-Monitoring, Analysis and Reporting Technology) monitors disk health and predicts failures before they happen. When: Run monthly for early warning, when disk makes unusual noises, feels slow, or shows strange behavior. After: Shows disk health status instantly. If \"Verified\" = healthy. If \"Failing\" = backup immediately and replace disk soon. No changes made (read-only check).",
            "category": "Disk / Filesystem",
            "safe": True,
            "recommended": False,
        },

        # Cleanup Operations
        "trim-logs": {
            "id": "trim-logs",
            "name": "Trim User Logs",
            "description": "Remove user logs older than 30 days",
            "guidance": "Why: Apps write diagnostic logs to track errors and activity. Old logs (>30 days) waste space and are rarely needed. When: Run monthly for routine cleanup, when low on disk space, or after resolving app issues (old diagnostic logs no longer useful). After: Frees 500MB-2GB typically. Old log files deleted permanently. Recent logs (<30 days) kept for troubleshooting. No impact on app functionality.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "trim-caches": {
            "id": "trim-caches",
            "name": "Trim User Caches",
            "description": "Remove user caches older than 30 days",
            "guidance": "Why: Apps store temporary data (thumbnails, previews, downloads) in caches. Old caches waste disk space and can become corrupted. When: Run monthly for maintenance, when running low on disk space, or when apps crash or display wrong content. After: Frees 2-10GB typically. Apps automatically rebuild caches as needed (thumbnails regenerate when viewing files, etc.). May see brief slowdown first time opening apps.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "browser-cache": {
            "id": "browser-cache",
            "name": "Clear Browser Caches",
            "description": "Clear Safari and Chrome browser caches",
            "guidance": "Why: Browsers cache images, videos, and scripts to speed up page loading. Over time (months), caches grow large (5-20GB) and can become corrupted. When: Run monthly if you browse heavily, when browsers feel sluggish, pages display incorrectly, or you're low on disk space. After: Frees 5-20GB, first visit to websites will redownload resources (slightly slower initially), cache rebuilds automatically. You may need to log back into some sites.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "dev-cache": {
            "id": "dev-cache",
            "name": "Clear Developer Caches",
            "description": "Clear Xcode DerivedData and build caches",
            "guidance": "Why: Xcode stores compiled code, indexes, and build artifacts in DerivedData. This grows to 20-50GB and can cause build failures. When: Run monthly for active developers, when Xcode builds fail mysteriously, autocomplete stops working, or you're low on disk space. After: Frees 20-50GB. Next Xcode build will be slower (full rebuild), but subsequent builds are normal speed. Autocomplete and indexing will rebuild in background.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "dev-tools-cache": {
            "id": "dev-tools-cache",
            "name": "Clear Dev Tools Caches",
            "description": "Clear npm, pip, Go, Cargo, and Composer package caches",
            "guidance": "Why: Package managers (npm, pip, Go, Cargo, Composer) cache downloaded packages to speed up installs. Over time, these caches grow to several GB with old/unused packages. When: Run monthly to reclaim disk space, when you notice npm/pip/go taking excessive disk space, or when package installs fail with cache corruption. After: Frees 500MB-5GB typically. Next package install will re-download needed packages (slight delay on first install only). No impact on installed packages or projects.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "thin-tm": {
            "id": "thin-tm",
            "name": "Thin Time Machine Snapshots",
            "description": "Remove old Time Machine local snapshots",
            "guidance": "Why: Time Machine stores local snapshots on your disk for quick restores. macOS usually manages these automatically. When: Run ONLY when disk is >88% full and you urgently need space. macOS normally deletes old snapshots when space is low. After: Deletes local Time Machine snapshots immediately, freeing 5-50GB. You'll lose ability to restore to deleted snapshots. External Time Machine backups (if any) are unaffected. Use only as last resort.",
            "category": "Cleanup Operations",
            "safe": False,
            "recommended": False,
        },
        "messages-cache": {
            "id": "messages-cache",
            "name": "Clear Messages Caches",
            "description": "Remove Messages preview/cache files (not chat history)",
            "guidance": "Why: Messages builds large preview caches and attachment preview thumbnails over time. These can grow to many GB and waste space. When: Run when low on disk space, or when Messages caches are unusually large. After: Frees disk space immediately. Messages may rebuild previews over time. Your actual chat database and message content are not deleted.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "wallpaper-aerials": {
            "id": "wallpaper-aerials",
            "name": "Remove Aerial Wallpaper Videos",
            "description": "Delete downloaded macOS Aerial (wallpaper) videos",
            "guidance": "Why: macOS can download high-resolution Aerial videos for wallpapers/screensavers, which can consume tens of GB. When: Run when disk space is low and Aerial videos are taking significant space. After: Frees disk space immediately. macOS may re-download videos later if Aerial wallpapers are enabled.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },

        # System Operations
        "spotlight-status": {
            "id": "spotlight-status",
            "name": "Check Spotlight Status",
            "description": "Check Spotlight indexing status",
            "guidance": "Why: Spotlight indexes all files for instant search. Checking status helps diagnose search problems. When: Run when Spotlight search returns no results, can't find files you know exist, or after adding large amounts of data. After: Shows whether Spotlight is indexing, idle, or disabled. Takes 1 second. No changes made. If problems found, may need to Rebuild Index.",
            "category": "System Operations",
            "safe": True,
            "recommended": False,
        },
        "spotlight-reindex": {
            "id": "spotlight-reindex",
            "name": "Rebuild Spotlight Index",
            "description": "Rebuild Spotlight search index",
            "guidance": "Why: Spotlight index can become corrupted, causing wrong search results or missing files. Rebuilding fixes the index. When: Run ONLY when searches consistently return wrong results, files don't appear in search but exist, or Spotlight Status shows errors. After: Deletes and rebuilds entire search index (1-3 hours). Mac will be slower during reindexing. Searches won't work until rebuild completes. CPU and battery usage will be high. Avoid during important work.",
            "category": "System Operations",
            "safe": False,
            "recommended": False,
        },
        "dns-flush": {
            "id": "dns-flush",
            "name": "Flush DNS Cache",
            "description": "Clear DNS resolver cache",
            "guidance": "Why: macOS caches DNS lookups (website names to IP addresses) to speed up connections. Stale cache causes connection failures. When: Run when websites won't load but internet works, getting \"server not found\" errors, after changing DNS settings/VPN, or after network changes. After: DNS cache is cleared immediately. Next website visit will query DNS servers (adds ~50ms delay first time), then cache rebuilds automatically.",
            "category": "System Operations",
            "safe": True,
            "recommended": False,
        },
        "periodic": {
            "id": "periodic",
            "name": "Run Periodic Maintenance",
            "description": "Run macOS periodic maintenance scripts (daily/weekly/monthly)",
            "guidance": "Why: macOS ships periodic housekeeping scripts (log rotation, temp cleanup, etc.). On laptops/sleeping Macs they may not run regularly. When: Run monthly, or if the Mac is often asleep at night (scripts may be skipped). After: Runs periodic tasks; usually takes seconds to a few minutes. Mostly safe; output is informational. No reboot required.",
            "category": "System Operations",
            "safe": True,
            "recommended": False,
        },
        "mail-optimize": {
            "id": "mail-optimize",
            "name": "Optimize Mail Database",
            "description": "Rebuild Mail.app envelope index",
            "guidance": "Why: Mail.app indexes emails for fast searching. Over time, the index can become fragmented or corrupted. When: Run quarterly, or when Mail feels slow, searches return wrong results, messages appear incomplete, or mailboxes won't open. After: Mail will rebuild the envelope index (takes 5-30 minutes depending on mailbox size). Searches will be faster and more accurate. Close Mail before running.",
            "category": "System Operations",
            "safe": True,
            "recommended": False,
        },

        # Reports
        "space-report": {
            "id": "space-report",
            "name": "Disk Space Report",
            "description": "Generate detailed disk space usage report",
            "guidance": "Why: Shows exactly where disk space is being used by scanning all files and folders. Helps identify space hogs. When: Run when running low on disk space and need to find what's using it, before cleanup operations to prioritize targets, or investigating unexpected space usage. After: Generates detailed report showing largest folders/files (takes 2-5 minutes). No changes made. Use report to decide what to delete. Check for large Downloads, old iOS backups, or forgotten files.",
            "category": "Reports & Analysis",
            "safe": True,
            "recommended": False,
        },
        "disk-triage": {
            "id": "disk-triage",
            "name": "Disk Triage",
            "description": "Quick overview of disk usage across key directories",
            "guidance": "Why: 'What's using my disk?' is the first question when space is low. This provides a quick answer. When: Before any cleanup, during weekly health checks, or after 'disk full' alerts. After: Shows ranked 'top offenders' in Home, Library, Caches, and other key locations. Takes 30-60 seconds. No changes made (read-only).",
            "category": "Reports & Analysis",
            "safe": True,
            "recommended": False,
        },
        "downloads-report": {
            "id": "downloads-report",
            "name": "Downloads Report",
            "description": "Report size and age of files in Downloads folder",
            "guidance": "Why: Downloads accumulate installers, archives, and forgotten files over time. When: Monthly, after big software installs, or when disk is tight. After: Shows files sorted by size with age information. No changes made (read-only). Use to decide what to clean.",
            "category": "Reports & Analysis",
            "safe": True,
            "recommended": False,
        },
        "downloads-cleanup": {
            "id": "downloads-cleanup",
            "name": "Clean Downloads",
            "description": "Remove old installers and archives from Downloads",
            "guidance": "Why: Old DMGs, ZIPs, and PKGs in Downloads waste space and are rarely needed. When: Monthly or when disk is tight. After: Removes .dmg, .zip, .pkg, and .iso files older than 30 days. Frees 1-20GB typically. Other files are left untouched.",
            "category": "Cleanup Operations",
            "safe": False,
            "recommended": False,
        },
        "xcode-cleanup": {
            "id": "xcode-cleanup",
            "name": "Xcode Cleanup",
            "description": "Remove Xcode DerivedData build cache",
            "guidance": "Why: Xcode stores compiled code and indexes in DerivedData. Can grow to 50GB+ for active developers. When: Monthly, when disk is tight, or when Xcode builds fail mysteriously. After: Removes all build caches. Next build will be slower (full rebuild), then normal. Frees 5-50GB.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "caches-cleanup": {
            "id": "caches-cleanup",
            "name": "Clear User Caches",
            "description": "Remove all user cache files",
            "guidance": "Why: ~/Library/Caches is designed to be purgeable. Contains temporary data apps can rebuild. When: Monthly or when disk is tight. After: Clears all user caches. Apps rebuild as needed. First app launch may be slightly slower. Frees 2-10GB typically.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "logs-cleanup": {
            "id": "logs-cleanup",
            "name": "Clean Old Logs",
            "description": "Remove log files older than 30 days",
            "guidance": "Why: Log files accumulate indefinitely and are rarely needed after a few weeks. When: Monthly maintenance. After: Removes logs older than 30 days from ~/Library/Logs. Frees 0.5-5GB. Recent logs preserved for troubleshooting.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "trash-empty": {
            "id": "trash-empty",
            "name": "Empty Trash",
            "description": "Permanently delete items in Trash",
            "guidance": "Why: Trash can hold GBs of 'deleted' files that still use disk space. When: Weekly or when disk is tight. After: Permanently deletes all Trash contents. Cannot be undone. Frees space immediately.",
            "category": "Cleanup Operations",
            "safe": False,
            "recommended": False,
        },
        "docker-prune": {
            "id": "docker-prune",
            "name": "Docker Cleanup",
            "description": "Clean up Docker (stopped containers, dangling images, build cache)",
            "guidance": "Why: Docker accumulates stopped containers, old images, and build cache that consume significant disk space (often 10-50GB for active developers). When: Monthly for active Docker users, when disk is tight, after completing a project. After: Removes stopped containers, unused networks, dangling images, and build cache. Running containers and tagged images are preserved. Frees 5-50GB typically.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
        "xcode-device-support": {
            "id": "xcode-device-support",
            "name": "Xcode Device Support Cleanup",
            "description": "Remove old iOS/watchOS/tvOS device support files",
            "guidance": "Why: Xcode caches device symbols for every iOS version you've connected to. Can grow to 20-40GB over time, especially with frequent iOS updates. When: After upgrading your devices to new iOS versions, annually, or when disk is tight. After: Removes device support caches. Will re-download when you connect a device (takes 2-5 minutes). Frees 10-40GB typically.",
            "category": "Cleanup Operations",
            "safe": True,
            "recommended": False,
        },
    }

    def __init__(self):
        """Initialize the Maintenance API."""
        super().__init__()
        self._cancel_requested = False
        self._skip_requested = False

    def get_operations(self) -> list[dict[str, Any]]:
        """Get list of all available maintenance operations.

        Returns:
            List of operation dictionaries with metadata including WHY/WHAT details

        Example:
            operations = api.get_operations()
            for op in operations:
                print(f"{op['name']}: {op['description']}")
        """
        self._log_call("get_operations")

        # Load operation details (WHY/WHAT) from JSON
        try:
            operation_details = self._load_operation_details()
        except Exception as e:
            # Defensive: never fail listing operations due to metadata issues
            self.logger.error(f"Failed to load operation details: {e}")
            operation_details = {}

        # Merge operation details into operations list
        operations = []
        merged_count = 0
        guidance_fallback_count = 0
        for op in self.OPERATIONS.values():
            op_dict = dict(op)  # Create a copy

            # Add WHY/WHAT details if available
            if op['id'] in operation_details:
                details = operation_details[op['id']]
                op_dict['why'] = details.get('why', {})
                op_dict['what'] = details.get('what', {})
                op_dict['when_to_run'] = details.get('when_to_run', [])
                op_dict['safety'] = details.get('safety', 'unknown')
                merged_count += 1
                self.logger.info(f"Merged WHY/WHAT for operation: {op['id']}")
            else:
                # Fallback: derive a consistent WHY/WHAT/WHEN structure from the legacy guidance string.
                # This keeps the UI consistent even when operation_details.json is incomplete.
                details = self._guidance_to_details(op.get("guidance"))
                if details is not None:
                    op_dict["why"] = details.get("why", {})
                    op_dict["what"] = details.get("what", {})
                    op_dict["when_to_run"] = details.get("when_to_run", [])
                    op_dict["safety"] = details.get("safety")
                    guidance_fallback_count += 1
                else:
                    # Always provide keys so downstream consumers don't branch on missing fields
                    op_dict['why'] = {}
                    op_dict['what'] = {}
                    op_dict['when_to_run'] = []
                    op_dict['safety'] = None

            operations.append(op_dict)

        self.logger.info(
            f"Merged operation details: file={merged_count} guidance_fallback={guidance_fallback_count} total={len(operations)}"
        )
        return operations

    def _guidance_to_details(self, guidance: str | None) -> dict[str, Any] | None:
        """Convert legacy one-line guidance into the structured WHY/WHAT/WHEN format.

        Guidance strings follow the pattern:
          "Why: ... When: ... After: ..."

        This fallback ensures *all* operations can render the same accordion layout
        even if operation_details.json is incomplete.
        """
        if not guidance or not isinstance(guidance, str):
            return None

        text = " ".join(guidance.strip().split())

        def _slice(label: str, next_labels: list[str]) -> str | None:
            i = text.find(label)
            if i < 0:
                return None
            start = i + len(label)
            end = None
            for nl in next_labels:
                j = text.find(nl, start)
                if j >= 0:
                    end = j if end is None else min(end, j)
            chunk = text[start:end].strip() if end is not None else text[start:].strip()
            return chunk or None

        why = _slice("Why:", ["When:", "After:"])
        when = _slice("When:", ["After:"])
        after = _slice("After:", [])

        # If nothing matched, don't fabricate structure.
        if not (why or when or after):
            return None

        details: dict[str, Any] = {
            "why": {"context": why} if why else {},
            "when_to_run": [when] if when else [],
            "what": {},
            "safety": None,
        }

        if after:
            details["what"] = {
                "outcomes": [
                    {
                        "type": "positive",
                        "description": after,
                    }
                ]
            }

        return details

    def _load_operation_details(self) -> dict[str, Any]:
        """Load operation details from operation_details.json.

        Returns:
            Dict mapping operation IDs to their WHY/WHAT details
        """
        try:
            # Find operation_details.json in project root
            # Start from this file and go up to find the project root
            current_file = Path(__file__)
            # Path: src/upkeep/api/maintenance.py
            # Up 1: src/upkeep/api
            # Up 2: src/upkeep
            # Up 3: src
            # Up 4: project root
            project_root = current_file.parent.parent.parent.parent

            details_file = project_root / "operation_details.json"

            if not details_file.exists():
                # Fallback: try relative to working directory
                details_file = Path("operation_details.json")
                if not details_file.exists():
                    self._log_error(f"operation_details.json not found. Tried: {project_root / 'operation_details.json'} and {Path('operation_details.json').absolute()}")
                    return {}

            self.logger.info(f"Loading operation details from: {details_file}")
            raw = details_file.read_text(encoding="utf-8").strip()
            if not raw:
                return {}

            data = json.loads(raw)

            # Support both formats:
            # 1) {"operations": { ... }}
            # 2) { ... } (direct mapping)
            operations = data.get('operations', data) if isinstance(data, dict) else {}
            self.logger.info(f"Loaded WHY/WHAT data for {len(operations)} operations")
            return operations

        except json.JSONDecodeError as e:
            self._log_error(f"Invalid JSON in operation_details.json: {e}")
            return {}
        except Exception as e:
            self._log_error(f"Failed to load operation details: {type(e).__name__}: {e}")
            return {}

    def get_operation(self, operation_id: str) -> dict[str, Any]:
        """Get a specific operation by ID.

        Args:
            operation_id: ID of the operation

        Returns:
            Operation dictionary with metadata

        Raises:
            OperationNotFoundError: If operation ID is not found
        """
        self._log_call("get_operation", operation_id=operation_id)

        operation = self.OPERATIONS.get(operation_id)
        if not operation:
            raise OperationNotFoundError(f"Operation not found: {operation_id}")

        return operation

    def _ensure_queue_dir(self) -> None:
        """Ensure the daemon queue directory exists and is writable.

        This prevents common 500s when the web UI/API is used before the daemon
        has had a chance to create/chmod the queue directory.

        Safety:
        - Creates the directory if missing
        - Best-effort chmod to 0777 to match daemon expectations (local machine queue)
        """
        try:
            self.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
            try:
                # World-writable is intentional here: the root daemon reads/validates jobs,
                # while the unprivileged web process needs to write job/flag files.
                self.QUEUE_DIR.chmod(0o777)
            except Exception:
                pass
        except Exception:
            # If we can't ensure it, downstream will raise a DaemonNotAvailableError
            pass

    def _enqueue_job(self, operation_id: str) -> str:
        """Enqueue a job for the daemon to process.

        Args:
            operation_id: ID of operation to run

        Returns:
            Job ID (UUID)

        Raises:
            DaemonNotAvailableError: If job queue is not accessible
        """
        # Ensure queue exists before writing
        self._ensure_queue_dir()

        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat(),
        }

        job_file = self.QUEUE_DIR / f"{job_id}.job.json"

        try:
            with open(job_file, "w") as f:
                json.dump(job, f, indent=2)
        except (PermissionError, OSError) as e:
            raise DaemonNotAvailableError(
                f"Cannot access job queue (is daemon running?): {e}"
            )
        except Exception as e:
            raise DaemonNotAvailableError(f"Failed to enqueue job: {e}")

        return job_id

    async def _wait_for_result(self, job_id: str, timeout: int = 1800) -> dict[str, Any]:
        """Wait for job result file to appear.

        Args:
            job_id: Job ID to wait for
            timeout: Maximum wait time in seconds

        Returns:
            Result dictionary

        Raises:
            TimeoutError: If result doesn't appear within timeout
        """
        result_file = self.QUEUE_DIR / f"{job_id}.result.json"
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check for cancellation
            if self._cancel_requested:
                return {
                    "job_id": job_id,
                    "status": "cancelled",
                    "error": "Operation cancelled by user",
                }

            # Check for skip
            if self._skip_requested:
                self._skip_requested = False
                return {
                    "job_id": job_id,
                    "status": "skipped",
                    "error": "Operation skipped by user",
                }

            # Check if result exists
            if result_file.exists():
                try:
                    with open(result_file, encoding='utf-8') as f:
                        result = json.load(f)

                    # Clean up result file
                    try:
                        result_file.unlink()
                    except Exception:
                        pass

                    return result
                except json.JSONDecodeError:
                    # File might still be writing, wait a bit
                    await asyncio.sleep(0.1)
                    continue

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

            # Wait before checking again
            await asyncio.sleep(0.5)

    def execute_operation(self, operation_id: str, timeout: int = 1800) -> dict[str, Any]:
        """Execute a single operation via the daemon queue and wait for the result.

        This is the synchronous entry point used by scheduled tasks.

        Args:
            operation_id: Operation ID to run
            timeout: Maximum wait time in seconds

        Returns:
            Result dict from the daemon (status, stdout/stderr, exit_code, etc.)

        Raises:
            OperationNotFoundError: If operation_id is unknown
            DaemonNotAvailableError: If the queue can't be accessed
            TimeoutError: If the daemon doesn't return a result in time
        """
        self._log_call("execute_operation", operation_id=operation_id, timeout=timeout)

        if operation_id not in self.OPERATIONS:
            raise OperationNotFoundError(f"Operation not found: {operation_id}")

        job_id = self._enqueue_job(operation_id)

        # Wait for the daemon result synchronously
        try:
            return asyncio.run(self._wait_for_result(job_id, timeout=timeout))
        except RuntimeError:
            # If we're already inside an event loop (rare but possible),
            # use a dedicated loop.
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._wait_for_result(job_id, timeout=timeout))
            finally:
                loop.close()

    async def run_operations(
        self,
        operation_ids: list[str],
    ) -> AsyncIterator[dict[str, Any]]:
        """Run multiple maintenance operations sequentially and stream progress.

        Args:
            operation_ids: List of operation IDs to run

        Yields:
            Progress events as dictionaries

        Example:
            async for event in api.run_operations(["brew-update", "disk-verify"]):
                if event['type'] == 'output':
                    print(event['line'])
                elif event['type'] == 'operation_complete':
                    print(f"Success: {event['success']}")
        """
        self._log_call("run_operations", operation_ids=operation_ids)

        self._cancel_requested = False
        total = len(operation_ids)
        results = []

        yield {
            "type": "start",
            "message": f"Starting {total} maintenance operation(s)...",
            "total": total,
            "timestamp": datetime.now().isoformat(),
        }

        for idx, op_id in enumerate(operation_ids, 1):
            if self._cancel_requested:
                yield {
                    "type": "cancelled",
                    "message": "Batch cancelled by user",
                    "timestamp": datetime.now().isoformat(),
                }
                break

            operation = self.OPERATIONS.get(op_id)
            if not operation:
                yield {
                    "type": "error",
                    "operation_id": op_id,
                    "message": f"Unknown operation: {op_id}",
                    "timestamp": datetime.now().isoformat(),
                }
                continue

            yield {
                "type": "operation_start",
                "operation_id": op_id,
                "operation_name": operation["name"],
                "progress": f"{idx}/{total}",
                "timestamp": datetime.now().isoformat(),
            }

            op_started_ts = time.time()

            try:
                # Enqueue job for daemon
                job_id = self._enqueue_job(op_id)

                yield {
                    "type": "output",
                    "operation_id": op_id,
                    "stream": "stdout",
                    "line": f"Job enqueued: {job_id}",
                    "timestamp": datetime.now().isoformat(),
                }

                yield {
                    "type": "output",
                    "operation_id": op_id,
                    "stream": "stdout",
                    "line": "Waiting for daemon to process...",
                    "timestamp": datetime.now().isoformat(),
                }

                # Wait for result
                result = await self._wait_for_result(job_id)

                # Check for skip/cancel
                if result.get("status") in ["cancelled", "skipped"]:
                    yield {
                        "type": "operation_skipped",
                        "operation_id": op_id,
                        "message": result.get("error", "Operation skipped"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    results.append({
                        "operation_id": op_id,
                        "success": False,
                        "returncode": -2,
                        "skipped": True,
                    })
                    continue

                # Stream stdout if available
                stdout = result.get("stdout", "")
                if stdout:
                    for line in stdout.split("\n"):
                        if line.strip():
                            # Clean control characters to prevent text truncation/corruption
                            cleaned_line = clean_output_line(line)
                            yield {
                                "type": "output",
                                "operation_id": op_id,
                                "stream": "stdout",
                                "line": cleaned_line,
                                "timestamp": datetime.now().isoformat(),
                            }

                # Stream stderr if available
                stderr = result.get("stderr", "")
                if stderr:
                    for line in stderr.split("\n"):
                        if line.strip():
                            # Clean control characters to prevent text truncation/corruption
                            cleaned_line = clean_output_line(line)
                            yield {
                                "type": "output",
                                "operation_id": op_id,
                                "stream": "stderr",
                                "line": cleaned_line,
                                "timestamp": datetime.now().isoformat(),
                            }

                # Send completion event
                success = result.get("status") == "success"
                exit_code = result.get("exit_code", -1)
                duration_seconds = max(0.0, time.time() - op_started_ts)

                yield {
                    "type": "operation_complete",
                    "operation_id": op_id,
                    "success": success,
                    "returncode": exit_code,
                    "timestamp": datetime.now().isoformat(),
                }

                # Write per-operation history (last run + rolling durations)
                try:
                    log_dir = Path.home() / "Library" / "Logs" / "upkeep"
                    log_dir.mkdir(parents=True, exist_ok=True)
                    history_file = log_dir / "operation_history.json"

                    # Load existing history
                    history: dict = {}
                    if history_file.exists():
                        try:
                            history = json.loads(history_file.read_text())
                        except json.JSONDecodeError:
                            history = {}

                    op_hist = history.get(op_id, {}) if isinstance(history.get(op_id, {}), dict) else {}
                    op_hist["last_run"] = datetime.now().isoformat()
                    op_hist["success"] = success
                    op_hist["last_duration_seconds"] = round(duration_seconds, 3)

                    # Maintain rolling windows of runtimes
                    # - durations_seconds: successful runs only (preferred for median)
                    # - durations_all_seconds: all runs (fallback when no successful baseline exists yet)

                    durations_all = op_hist.get("durations_all_seconds", [])
                    if not isinstance(durations_all, list):
                        durations_all = []
                    durations_all.append(round(duration_seconds, 3))
                    durations_all = durations_all[-5:]
                    op_hist["durations_all_seconds"] = durations_all

                    if success:
                        durations = op_hist.get("durations_seconds", [])
                        if not isinstance(durations, list):
                            durations = []
                        durations.append(round(duration_seconds, 3))
                        durations = durations[-5:]
                        op_hist["durations_seconds"] = durations

                    history[op_id] = op_hist

                    # Write back to file
                    history_file.write_text(json.dumps(history, indent=2))
                except Exception as e:
                    self.logger.warning(f"Failed to write operation history: {e}")

                results.append({
                    "operation_id": op_id,
                    "success": success,
                    "returncode": exit_code,
                })

            except TimeoutError as e:
                yield {
                    "type": "operation_error",
                    "operation_id": op_id,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                yield {
                    "type": "operation_complete",
                    "operation_id": op_id,
                    "success": False,
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat(),
                }
                results.append({
                    "operation_id": op_id,
                    "success": False,
                    "returncode": -1,
                })

        # Send summary
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        yield {
            "type": "summary",
            "total": total,
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

        # Write completion timestamp to file for last_run tracking
        try:
            log_dir = Path.home() / "Library" / "Logs" / "upkeep"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp_file = log_dir / "last_run_timestamp.txt"
            timestamp_file.write_text(datetime.now().isoformat())
        except Exception as e:
            self.logger.warning(f"Failed to write timestamp file: {e}")

        yield {
            "type": "complete",
            "message": f"Completed {total} operation(s): {successful} successful, {failed} failed",
            "timestamp": datetime.now().isoformat(),
        }

    def skip_current_operation(self) -> bool:
        """Skip the current operation and move to the next (Task #133 fix).

        Business Logic:
        - Writes skip.flag file in queue directory
        - Daemon watches for this file and kills subprocess when found
        - Daemon marks operation as "skipped" and moves to next job

        Returns:
            True if skip was initiated
        """
        self._skip_requested = True

        # Task #133: Write skip flag file so daemon can kill subprocess
        try:
            self._ensure_queue_dir()
            skip_flag = self.QUEUE_DIR / "skip.flag"
            skip_flag.write_text("skip")
            self.logger.info("Skip flag written, daemon will kill current subprocess")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write skip flag: {e}")
            return False

    def cancel_operations(self) -> bool:
        """Cancel running operations.

        Returns:
            True if cancellation was initiated
        """
        self._log_call("cancel_operations")
        self._cancel_requested = True
        return True

    def get_queue_status(self) -> dict[str, Any]:
        """Get current queue status and running operation info (Task #129).

        Business Logic:
        - Shows what operation is currently running
        - Shows how long current operation has been running
        - Shows how many operations are waiting in queue
        - Provides transparency so user knows system isn't hung

        Returns:
            Dictionary with queue status:
            - current_operation: dict with operation info (or None)
            - queued_count: number of operations waiting
            - daemon_running: whether daemon is active
        """
        self._log_call("get_queue_status")

        try:
            # Check if daemon is running (simple check - just assume it is)
            # Could enhance this later with PID file check
            daemon_running = True

            # Read current operation status from daemon's status file
            status_file = self.QUEUE_DIR / "daemon-status.json"
            current_operation = None

            if status_file.exists():
                try:
                    with open(status_file) as f:
                        status_data = json.load(f)

                    # Calculate elapsed time
                    start_time = status_data.get("start_time", 0)
                    elapsed_seconds = int(datetime.now().timestamp() - start_time)

                    current_operation = {
                        "operation_id": status_data.get("operation_id", ""),
                        "name": self._get_operation_name(status_data.get("operation_id", "")),
                        "elapsed_seconds": elapsed_seconds,
                        "elapsed_formatted": self._format_duration(elapsed_seconds),
                        "timeout_seconds": status_data.get("timeout_seconds", 0),
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to read status file: {e}")

            # Count queued jobs
            job_files = list(self.QUEUE_DIR.glob("*.job.json"))
            queued_count = len(job_files)

            return {
                "daemon_running": daemon_running,
                "current_operation": current_operation,
                "queued_count": queued_count,
            }

        except Exception as e:
            self.logger.error(f"Error getting queue status: {e}")
            return {
                "daemon_running": False,
                "current_operation": None,
                "queued_count": 0,
                "error": str(e),
            }

    def _get_operation_name(self, operation_id: str) -> str:
        """Get human-readable name for operation ID."""
        return self.OPERATIONS.get(operation_id, {}).get("name", operation_id)

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
