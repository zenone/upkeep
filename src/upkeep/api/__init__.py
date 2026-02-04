"""API layer for upkeep toolkit.

This package provides a clean, testable API for all maintenance operations.
All CLI and TUI interfaces should use these APIs rather than direct subprocess calls.

Usage:
    from upkeep.api import StorageAPI, SystemAPI, MaintenanceAPI

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

from upkeep.api.storage import StorageAPI
from upkeep.api.maintenance import MaintenanceAPI
from upkeep.api.schedule import ScheduleAPI

__all__ = [
    "StorageAPI",
    "MaintenanceAPI",
    "ScheduleAPI",
]
