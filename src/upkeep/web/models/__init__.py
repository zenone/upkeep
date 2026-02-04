"""
Pydantic models for API request/response validation.

This package contains all Data Transfer Objects (DTOs) used in the API.
Following API-First principles, these models define the contract between
frontend and backend.
"""

from .system import (
    SystemInfoResponse,
    SystemHealthResponse,
    SparklineResponse,
    ProcessInfo,
    ProcessesResponse,
)
from .storage import (
    StorageAnalyzeRequest,
    StorageAnalyzeResponse,
    StorageEntry,
    DeleteRequest,
    DeleteResponse,
)
from .maintenance import (
    MaintenanceOperation,
    OperationsListResponse,
    LastRunResponse,
    RunOperationsRequest,
    OperationEvent,
)
from .schedule import (
    Schedule,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleDeleteResponse,
    ScheduleToggleResponse,
)
from .common import (
    ErrorResponse,
    SuccessResponse,
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
