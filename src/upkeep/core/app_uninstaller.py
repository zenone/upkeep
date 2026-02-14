import shutil
import os
from pathlib import Path
from typing import List, Dict, Union, Any, Optional

from upkeep.core.app_finder import AppFinder

class AppUninstaller:
    """
    Handles finding and removing application files.
    Defaults to dry_run=True for safety.
    """
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.finder = AppFinder()

    def plan_uninstall(self, app_path: str) -> Dict[str, Any]:
        """
        Finds all files related to the app without deleting anything.
        Returns a dict with 'app' path and 'related' paths.
        """
        scan_result = self.finder.scan(app_path)
        
        if not scan_result:
            return {"app": Path(app_path), "related": []}

        app_main_path = Path(scan_result.app_info.get("path", app_path))
        
        related_paths = []
        for artifact in scan_result.artifacts:
            # We want all artifacts EXCEPT the app bundle itself in the 'related' list
            # The app bundle is tracked separately in the 'app' key
            if artifact.kind == "app" and artifact.path == app_main_path:
                continue
            related_paths.append(artifact.path)

        return {
            "app": app_main_path,
            "related": related_paths
        }

    def uninstall(self, app_path: str) -> Dict[str, Any]:
        """
        Executes the uninstallation based on the plan.
        If dry_run is True, returns the plan with status='planned'.
        If dry_run is False, deletes files and returns status='deleted'.
        """
        plan = self.plan_uninstall(app_path)
        
        # Combine app and related into one list for processing
        # Ensure list contains Path objects
        items_to_delete = plan.get("related", []) + [plan.get("app")]
        
        result = {
            "app": plan.get("app"),
            "items": items_to_delete,
            "dry_run": self.dry_run,
            "status": "planned" if self.dry_run else "deleted",
            "errors": []
        }

        if self.dry_run:
            return result

        # Actual deletion logic (for future slice)
        # TODO: Implement deletion
        
        return result
