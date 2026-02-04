"""
Common type definitions and enums for Upkeep.

Following API-First principles, all data structures are strongly typed.
"""

from enum import Enum


class OperationStatus(str, Enum):
    """Status of a maintenance operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class DeletionMode(str, Enum):
    """Mode for deleting files/directories."""

    TRASH = "trash"  # Move to Trash (recoverable)
    PERMANENT = "permanent"  # Permanently delete (cannot be undone)


class HealthStatus(str, Enum):
    """System health assessment categories."""

    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"  # 60-79
    FAIR = "fair"  # 40-59
    POOR = "poor"  # 0-39


class ProcessSortBy(str, Enum):
    """Sorting options for process lists."""

    CPU = "cpu"
    MEMORY = "memory"


class OperationCategory(str, Enum):
    """Categories of maintenance operations."""

    SYSTEM_UPDATE = "system_update"
    DISK = "disk"
    CLEANUP = "cleanup"
    MAINTENANCE = "maintenance"
