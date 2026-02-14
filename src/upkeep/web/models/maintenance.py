"""Maintenance operations models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceOperation(BaseModel):
    """A maintenance operation that can be executed."""

    id: str = Field(..., description="Operation identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Operation description")
    category: str = Field(..., description="Operation category")
    recommended: bool = Field(default=False, description="Whether this operation is recommended")
    requires_sudo: bool = Field(
        default=True, description="Whether this operation requires sudo privileges"
    )

    # WHY/WHAT information for user guidance
    why: dict[str, Any] | None = Field(
        default=None, description="Why to run this operation (problems it solves)"
    )
    what: dict[str, Any] | None = Field(
        default=None, description="What to expect (outcomes and timeline)"
    )
    when_to_run: list[str] | None = Field(default=None, description="When to run this operation")
    safety: str | None = Field(
        default=None, description="Safety level: low-risk, medium-risk, high-risk"
    )
    guidance: str | None = Field(
        default=None, description="Legacy guidance field (deprecated, use why/what instead)"
    )


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

    operations: list[MaintenanceOperation] = Field(..., description="Available operations")


class OperationHistory(BaseModel):
    """History of a single operation."""

    last_run: str | None = Field(None, description="ISO 8601 timestamp of last run")
    last_run_relative: str = Field(
        ..., description="Human-readable relative time (e.g., '2 hours ago')"
    )
    success: bool | None = Field(None, description="Whether last run was successful")
    last_duration_seconds: float | None = Field(
        None, description="Duration of last run in seconds", ge=0
    )
    typical_seconds: float | None = Field(None, description="Median duration in seconds (for ETA)")
    typical_display: str | None = Field(
        None, description="Human-readable typical duration (e.g., '12s')"
    )
    typical_runs: int | None = Field(
        None, description="Number of successful runs used for typical calculation"
    )
    typical_runs_all: int | None = Field(None, description="Number of all runs recorded")
    typical_basis: str | None = Field(None, description="Which data was used: 'success' or 'all'")


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
                        "success": True,
                        "last_duration_seconds": 2.3,
                        "typical_seconds": 2.5,
                        "typical_display": "3s",
                        "typical_runs": 5,
                        "typical_runs_all": 5,
                        "typical_basis": "success",
                    },
                    "repair_permissions": {
                        "last_run": None,
                        "last_run_relative": "Never",
                        "success": None,
                        "last_duration_seconds": None,
                        "typical_seconds": None,
                        "typical_display": None,
                        "typical_runs": 0,
                        "typical_runs_all": 0,
                        "typical_basis": None,
                    },
                },
            }
        }
    )

    success: bool = Field(True, description="Request succeeded")
    global_last_run: str | None = Field(
        None, description="ISO 8601 timestamp of most recent operation"
    )
    global_last_run_relative: str = Field(..., description="Relative time of most recent operation")
    status: str = Field(..., description="Status: completed, never, or error")
    operations: dict[str, OperationHistory] = Field(
        default_factory=dict, description="Per-operation history keyed by operation ID"
    )


class RunOperationsRequest(BaseModel):
    """Request to run maintenance operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operation_ids": ["clear_user_caches", "clear_system_caches", "repair_permissions"]
            }
        }
    )

    operation_ids: list[str] = Field(..., description="List of operation IDs to run", min_length=1)


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
    operation_id: str | None = Field(None, description="Operation identifier")
    message: str = Field(..., description="Event message")
    current: int | None = Field(None, description="Current operation number", ge=1)
    total: int | None = Field(None, description="Total operations", ge=1)
