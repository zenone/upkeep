"""API layer for mac-maintenance toolkit.

This package provides a clean, testable API for all maintenance operations.
All CLI and TUI interfaces should use these APIs rather than direct subprocess calls.

Usage:
    from mac_maintenance.api import StorageAPI, SystemAPI, MaintenanceAPI

    # Storage analysis
    storage = StorageAPI()
    result = storage.analyze_path("/Users/user/Downloads")

    # System information
    system = SystemAPI()
    info = system.get_memory_info()

    # Maintenance operations
    maintenance = MaintenanceAPI()
    result = await maintenance.update_homebrew()
"""

from mac_maintenance.api.storage import StorageAPI
from mac_maintenance.api.maintenance import MaintenanceAPI
from mac_maintenance.api.schedule import ScheduleAPI

__all__ = [
    "StorageAPI",
    "MaintenanceAPI",
    "ScheduleAPI",
]
