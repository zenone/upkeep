import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from upkeep.core.app_finder import AppFinder, AppScanResult


@dataclass
class UninstallResult:
    """Result of an uninstall operation."""
    success: bool
    deleted_paths: list[Path]
    bytes_recovered: int
    errors: list[str]

class AppUninstaller:
    """
    Handles finding and removing application files.
    Defaults to dry_run=True for safety.
    """
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.finder = AppFinder()

    def generate_report(self, app: AppScanResult) -> Any:
        """
        Generate a detailed report of what would be removed.
        Returns an object that can be serialized to JSON (via to_dict or vars).
        """
        # Simply wrapping the AppScanResult artifacts for now
        # Could grouping by kind here
        artifacts_by_kind = {}
        for a in app.artifacts:
            k = a.kind
            if k not in artifacts_by_kind:
                artifacts_by_kind[k] = []
            artifacts_by_kind[k].append({
                "path": str(a.path),
                "size_bytes": a.size_bytes,
                "reason": a.reason
            })

        return type("Report", (), {
            "to_dict": lambda: {
                "app_info": app.app_info,
                "total_size": app.total_size_bytes,
                "artifacts": artifacts_by_kind
            }
        })()

    def uninstall(self, app: AppScanResult) -> UninstallResult:
        """
        Executes the uninstallation based on the scan result.
        """
        deleted = []
        recovered = 0
        errors = []

        # Sort artifacts to delete deepest paths first (though for files it doesn't matter much)
        # But for directories, we should be careful.
        # Actually AppFinder returns paths.

        # We need to delete all artifacts + the app bundle itself.
        # Note: artifacts list includes the app bundle (kind="app").

        to_delete = sorted(app.artifacts, key=lambda x: len(str(x.path)), reverse=True)

        for artifact in to_delete:
            p = artifact.path
            if not p.exists():
                continue

            try:
                if self.dry_run:
                    # Just simulate
                    deleted.append(p)
                    recovered += artifact.size_bytes
                else:
                    if p.is_dir() and not p.is_symlink():
                        # Use send2trash or shutil.rmtree?
                        # Requirements say "Safety: Moves to Trash"
                        # But send2trash is external dependency.
                        # server.py has delete_path using storage_api.
                        # For now, let's use shutil.rmtree or os.remove if dry_run=False
                        # BUT BETTER: Use the existing StorageAPI if possible, or just Move to Trash logic.
                        # Since I don't want to add deps, I'll use a simple move to ~/.Trash
                        trash_dir = Path.home() / ".Trash"
                        dest = trash_dir / p.name
                        if dest.exists():
                            # timestamp it
                            import time
                            dest = trash_dir / f"{p.name}.{int(time.time())}"

                        shutil.move(str(p), str(dest))
                        deleted.append(p)
                        recovered += artifact.size_bytes
                    else:
                        # File
                        trash_dir = Path.home() / ".Trash"
                        dest = trash_dir / p.name
                        if dest.exists():
                            import time
                            dest = trash_dir / f"{p.name}.{int(time.time())}"
                        shutil.move(str(p), str(dest))
                        deleted.append(p)
                        recovered += artifact.size_bytes

            except Exception as e:
                errors.append(f"Failed to delete {p}: {e}")

        return UninstallResult(
            success=len(errors) == 0,
            deleted_paths=deleted,
            bytes_recovered=recovered,
            errors=errors
        )

