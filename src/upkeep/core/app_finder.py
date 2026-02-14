"""
Core logic for finding applications and their associated artifacts.
"""

import os
import plistlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppArtifact:
    """Represents a file or directory associated with an application."""

    path: Path
    kind: str  # "app", "cache", "config", "data", "log", "container", "preferences"
    size_bytes: int
    reason: str  # "Bundle ID match", "Name match"


@dataclass
class AppScanResult:
    """Result of scanning an application for artifacts."""

    app_info: dict[str, Any]  # name, version, bundle_id, icon_path
    artifacts: list[AppArtifact] = field(default_factory=list)
    total_size_bytes: int = 0

    @property
    def name(self) -> str:
        return self.app_info.get("name", "Unknown")

    @property
    def path(self) -> str:
        return self.app_info.get("path", "")

    @property
    def bundle_id(self) -> str:
        return self.app_info.get("bundle_id", "")

    @property
    def version(self) -> str:
        return self.app_info.get("version", "")

    @property
    def icon_path(self) -> str:
        return self.app_info.get("icon_path", "")

    @property
    def size_bytes(self) -> int:
        return self.total_size_bytes

    @property
    def size_display(self) -> str:
        # Simple helper for display
        s = self.total_size_bytes
        if s < 1024:
            return f"{s} B"
        elif s < 1024**2:
            return f"{s / 1024:.1f} KB"
        elif s < 1024**3:
            return f"{s / 1024**2:.1f} MB"
        else:
            return f"{s / 1024**3:.1f} GB"


class AppFinder:
    """Service to locate applications and their related files."""

    def __init__(self, root_path: Path | None = None):
        """
        Initialize AppFinder.

        Args:
            root_path: Optional root path for testing (default: /)
        """
        self.root_path = root_path or Path("/")
        self.user_home = Path.home()

        # Paths to scan for artifacts relative to user home
        self.artifact_locations = [
            ("Library/Application Support", "support"),
            ("Library/Caches", "cache"),
            ("Library/Containers", "container"),
            ("Library/Group Containers", "container"),
            ("Library/Preferences", "preferences"),
            ("Library/Logs", "log"),
            ("Library/Saved Application State", "state"),
            ("Library/WebKit", "cache"),
        ]

    def scan_applications(self) -> list[AppScanResult]:
        """
        Find all installed applications in standard locations.

        Returns:
            List of AppScanResult objects for found apps.
        """
        app_paths = []
        search_dirs = [
            Path("/Applications"),
            Path("/System/Applications"),
            self.user_home / "Applications",
        ]

        for d in search_dirs:
            if d.exists():
                # Find all .app bundles
                app_paths.extend(d.glob("*.app"))

        results = []
        for p in app_paths:
            try:
                # Scan each app (this might be slow for ALL apps, optimization needed later)
                # For now, just basic info from Info.plist to be fast, deep scan only on demand?
                # Actually, the requirement is to list apps with sizes.
                # Let's do a lightweight scan first.

                # Use scan() but maybe optimized?
                # scan() does a full artifact search.
                # For the list view, we might just want the app bundle info + size.
                # But the user expects "total footprint".
                # Let's use scan() for now and limit if too slow.
                res = self.scan(str(p))
                if res:
                    results.append(res)
            except Exception:
                continue

        return results

    def find_app(self, name_or_path: str) -> AppScanResult | None:
        """
        Find an app by name (e.g. 'Slack') or path.
        """
        # If full path given
        if "/" in name_or_path and Path(name_or_path).exists():
            return self.scan(name_or_path)

        # Search standard locations
        search_dirs = [
            Path("/Applications"),
            Path("/System/Applications"),
            self.user_home / "Applications",
        ]

        # Try exact name match with .app extension
        for d in search_dirs:
            if d.exists():
                p = d / f"{name_or_path}.app"
                if p.exists():
                    return self.scan(str(p))

        # Try case-insensitive scan
        lower_name = name_or_path.lower()
        for d in search_dirs:
            if d.exists():
                for p in d.glob("*.app"):
                    if p.stem.lower() == lower_name:
                        return self.scan(str(p))

        return None

    def scan(self, app_path_str: str) -> AppScanResult | None:
        """
        Scan an application path and find all associated artifacts.

        Args:
            app_path_str: Path to the .app bundle

        Returns:
            AppScanResult or None if app not found/invalid
        """
        app_path = Path(app_path_str)
        if not app_path.exists():
            return None

        # 1. Parse Info.plist to get Bundle ID and metadata
        info_plist = app_path / "Contents" / "Info.plist"
        if not info_plist.exists():
            return None

        try:
            with open(info_plist, "rb") as f:
                try:
                    plist_data = plistlib.load(f)
                except (plistlib.InvalidFileException, Exception):
                    # Try reading as text XML if binary fails
                    f.seek(0)
                    try:
                        plist_data = plistlib.load(f, fmt=plistlib.FMT_XML)
                    except Exception:
                        return None
        except Exception:
            return None

        bundle_id = plist_data.get("CFBundleIdentifier")
        app_name = plist_data.get("CFBundleName", app_path.stem)
        version = plist_data.get("CFBundleShortVersionString", "Unknown")

        if not bundle_id:
            return None

        # 2. Start building result
        result = AppScanResult(
            app_info={
                "name": app_name,
                "bundle_id": bundle_id,
                "version": version,
                "path": str(app_path),
            },
            artifacts=[],
            total_size_bytes=0,
        )

        # Add the app itself as an artifact
        app_size = self._get_size(app_path)
        result.artifacts.append(
            AppArtifact(path=app_path, kind="app", size_bytes=app_size, reason="Application bundle")
        )
        result.total_size_bytes += app_size

        # 3. Scan for associated artifacts using Bundle ID and Name
        self._find_artifacts(result, bundle_id, app_name)

        return result

    def _find_artifacts(self, result: AppScanResult, bundle_id: str, app_name: str):
        """Find artifacts in standard locations matching Bundle ID or Name."""

        for rel_path, kind in self.artifact_locations:
            base_dir = self.user_home / rel_path

            # Debugging aid: print checking path
            # print(f"Checking base_dir: {base_dir} (Exists: {base_dir.exists()})")

            if not base_dir.exists():
                continue

            # Strategy 1: Exact match on Bundle ID (e.g., ~/Library/Preferences/com.slack.Slack.plist)
            # Check for directory match
            bundle_dir = base_dir / bundle_id
            if bundle_dir.exists():
                self._add_artifact(result, bundle_dir, kind, "Bundle ID match")

            # Check for file match (e.g. preferences plist)
            bundle_file = base_dir / f"{bundle_id}.plist"
            if bundle_file.exists():
                self._add_artifact(result, bundle_file, kind, "Bundle ID match")

            # Strategy 2: Exact match on App Name (e.g., ~/Library/Application Support/Slack)
            # Only if name is distinctive enough (len > 3) to avoid false positives like "Log" or "Mac"
            if len(app_name) > 3:
                name_dir = base_dir / app_name
                if name_dir.exists():
                    self._add_artifact(result, name_dir, kind, "Name match")

    def _add_artifact(self, result: AppScanResult, path: Path, kind: str, reason: str):
        """Add an artifact to the result if not already present."""
        # Check if already added to avoid duplicates
        if any(a.path == path for a in result.artifacts):
            return

        size = self._get_size(path)
        result.artifacts.append(AppArtifact(path=path, kind=kind, size_bytes=size, reason=reason))
        result.total_size_bytes += size

    def _get_size(self, path: Path) -> int:
        """Calculate size of file or directory in bytes."""
        total = 0
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = Path(dirpath) / f
                        if not fp.is_symlink():
                            total += fp.stat().st_size
        except Exception:
            pass  # Ignore permission errors/stat failures
        return total
