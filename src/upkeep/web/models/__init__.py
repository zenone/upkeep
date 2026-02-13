"""
Pydantic models for API request/response validation.

This package contains all Data Transfer Objects (DTOs) used in the API.
Following API-First principles, these models define the contract between
frontend and backend.
"""

from .common import (
    ErrorResponse,
    SuccessResponse,
)
from .maintenance import (
    LastRunResponse,
    MaintenanceOperation,
    OperationEvent,
    OperationsListResponse,
    RunOperationsRequest,
)
from .schedule import (
    Schedule,
    ScheduleCreate,
    ScheduleDeleteResponse,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleToggleResponse,
    ScheduleUpdate,
)
from .storage import (
    DeleteRequest,
    DeleteResponse,
    StorageAnalyzeRequest,
    StorageAnalyzeResponse,
    StorageEntry,
)
from .system import (
    ProcessesResponse,
    ProcessInfo,
    SparklineResponse,
    SystemHealthResponse,
    SystemInfoResponse,
)

__all__ = [
    # System
    "SystemInfoResponse",
    "SystemHealthResponse",
    "SparklineResponse",
    "ProcessInfo",
    "ProcessesResponse",
    # Storage
    "StorageAnalyzeRequest",
    "StorageAnalyzeResponse",
    "StorageEntry",
    "DeleteRequest",
    "DeleteResponse",
    # Maintenance
    "MaintenanceOperation",
    "OperationsListResponse",
    "LastRunResponse",
    "RunOperationsRequest",
    "OperationEvent",
    # Schedule
    "Schedule",
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleListResponse",
    "ScheduleResponse",
    # Common
    "ErrorResponse",
    "SuccessResponse",
]
