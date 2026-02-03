"""Maintenance operations models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceOperation(BaseModel):
    """A maintenance operation that can be executed."""

    id: str = Field(..., description="Operation identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Operation description")
    category: str = Field(..., description="Operation category")
    recommended: bool = Field(default=False, description="Whether this operation is recommended")
    requires_sudo: bool = Field(default=True, description="Whether this operation requires sudo privileges")

    # WHY/WHAT information for user guidance
    why: Optional[Dict[str, Any]] = Field(default=None, description="Why to run this operation (problems it solves)")
    what: Optional[Dict[str, Any]] = Field(default=None, description="What to expect (outcomes and timeline)")
    when_to_run: Optional[List[str]] = Field(default=None, description="When to run this operation")
    safety: Optional[str] = Field(default=None, description="Safety level: low-risk, medium-risk, high-risk")
    guidance: Optional[str] = Field(default=None, description="Legacy guidance field (deprecated, use why/what instead)")


class OperationsListResponse(BaseModel):
    """List of available maintenance operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operations": [
                    {
                        "id": "clear_user_caches",
                        "name": "Clear User Caches",
                        "description": "Clear user-level caches",
                        "category": "cleanup",
                        "recommended": True,
                        "requires_sudo": False,
                    },
                    {
                        "id": "repair_permissions",
                        "name": "Repair Disk Permissions",
                        "description": "Verify and repair disk permissions",
                        "category": "system",
                        "recommended": True,
                        "requires_sudo": True,
                    },
                ]
            }
        }
    )

    operations: List[MaintenanceOperation] = Field(..., description="Available operations")


class OperationHistory(BaseModel):
    """History of a single operation."""

    last_run: Optional[str] = Field(None, description="ISO 8601 timestamp of last run")
    last_run_relative: str = Field(..., description="Human-readable relative time (e.g., '2 hours ago')")
    status: Optional[str] = Field(None, description="Last run status: completed, failed, or skipped")
    duration_seconds: Optional[float] = Field(None, description="Duration of last run in seconds", ge=0)


class LastRunResponse(BaseModel):
    """Last run information for maintenance operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "global_last_run": "2026-01-28T17:30:25Z",
                "global_last_run_relative": "2 hours ago",
                "status": "completed",
                "operations": {
                    "clear_user_caches": {
                        "last_run": "2026-01-28T17:30:25Z",
                        "last_run_relative": "2 hours ago",
                        "status": "completed",
                        "duration_seconds": 2.3,
                    },
                    "repair_permissions": {
                        "last_run": None,
                        "last_run_relative": "Never",
                        "status": None,
                        "duration_seconds": None,
                    },
                },
            }
        }
    )

    success: bool = Field(True, description="Request succeeded")
    global_last_run: Optional[str] = Field(None, description="ISO 8601 timestamp of most recent operation")
    global_last_run_relative: str = Field(..., description="Relative time of most recent operation")
    status: str = Field(..., description="Status: completed, never, or error")
    operations: Dict[str, OperationHistory] = Field(
        default_factory=dict, description="Per-operation history keyed by operation ID"
    )


class RunOperationsRequest(BaseModel):
    """Request to run maintenance operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"operation_ids": ["clear_user_caches", "clear_system_caches", "repair_permissions"]}
        }
    )

    operation_ids: List[str] = Field(..., description="List of operation IDs to run", min_length=1)


class OperationEvent(BaseModel):
    """Server-sent event for operation progress."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "progress",
                "operation_id": "clear_user_caches",
                "message": "Clearing DNS cache...",
                "current": 1,
                "total": 3,
            }
        }
    )

    type: str = Field(..., description="Event type: start, progress, complete, skip, error, done")
    operation_id: Optional[str] = Field(None, description="Operation identifier")
    message: str = Field(..., description="Event message")
    current: Optional[int] = Field(None, description="Current operation number", ge=1)
    total: Optional[int] = Field(None, description="Total operations", ge=1)
