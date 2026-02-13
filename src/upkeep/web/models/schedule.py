"""Scheduled maintenance task models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Schedule(BaseModel):
    """A scheduled maintenance task."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sched_001",
                "name": "Daily Cache Cleanup",
                "enabled": True,
                "cron": "0 2 * * *",
                "cron_human": "Every day at 2:00 AM",
                "operations": ["clear_user_caches", "clear_system_caches"],
                "created_at": "2026-01-28T10:00:00Z",
                "last_run": "2026-01-28T02:00:00Z",
                "next_run": "2026-01-29T02:00:00Z",
            }
        }
    )

    id: str = Field(..., description="Unique schedule identifier")
    name: str = Field(..., description="Schedule name", min_length=1, max_length=100)
    enabled: bool = Field(True, description="Whether schedule is active")
    cron: str = Field(..., description="Cron expression (minute hour day month weekday)")
    cron_human: str = Field(..., description="Human-readable cron description")
    operations: list[str] = Field(..., description="Operation IDs to run", min_length=1)
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    last_run: str | None = Field(None, description="ISO 8601 timestamp of last execution")
    next_run: str = Field(..., description="ISO 8601 timestamp of next scheduled execution")

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate cron expression format."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have exactly 5 fields")
        return v


class ScheduleCreate(BaseModel):
    """Request to create a new schedule."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Daily Cache Cleanup",
                "cron": "0 2 * * *",
                "operations": ["clear_user_caches", "clear_system_caches"],
                "enabled": True,
            }
        }
    )

    name: str = Field(..., description="Schedule name", min_length=1, max_length=100)
    cron: str = Field(..., description="Cron expression", min_length=9)
    operations: list[str] = Field(
        ..., description="Operation IDs to run", min_length=1, max_length=20
    )
    enabled: bool = Field(True, description="Start enabled or disabled")

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate cron expression format."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have exactly 5 fields (minute hour day month weekday)"
            )
        return v


class ScheduleUpdate(BaseModel):
    """Request to update an existing schedule."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "Weekly Cache Cleanup", "cron": "0 2 * * 0", "enabled": False}
        }
    )

    name: str | None = Field(None, description="New schedule name", min_length=1, max_length=100)
    cron: str | None = Field(None, description="New cron expression")
    operations: list[str] | None = Field(
        None, description="New operation IDs", min_length=1, max_length=20
    )
    enabled: bool | None = Field(None, description="Enable or disable schedule")

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        """Validate cron expression format if provided."""
        if v is not None:
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have exactly 5 fields")
        return v


class ScheduleListResponse(BaseModel):
    """List of all schedules."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "schedules": [
                    {
                        "id": "sched_001",
                        "name": "Daily Cleanup",
                        "enabled": True,
                        "cron": "0 2 * * *",
                        "cron_human": "Every day at 2:00 AM",
                        "operations": ["clear_user_caches"],
                        "created_at": "2026-01-28T10:00:00Z",
                        "last_run": "2026-01-28T02:00:00Z",
                        "next_run": "2026-01-29T02:00:00Z",
                    }
                ],
                "active_count": 1,
            }
        }
    )

    success: bool = Field(True, description="Request succeeded")
    schedules: list[Schedule] = Field(..., description="All schedules")
    active_count: int = Field(..., description="Number of enabled schedules", ge=0)


class ScheduleResponse(BaseModel):
    """Single schedule response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "schedule": {
                    "id": "sched_001",
                    "name": "Daily Cleanup",
                    "enabled": True,
                    "cron": "0 2 * * *",
                    "cron_human": "Every day at 2:00 AM",
                    "operations": ["clear_user_caches"],
                    "created_at": "2026-01-28T10:00:00Z",
                    "last_run": "2026-01-28T02:00:00Z",
                    "next_run": "2026-01-29T02:00:00Z",
                },
            }
        }
    )

    success: bool = Field(True, description="Request succeeded")
    schedule: Schedule = Field(..., description="The schedule")


class ScheduleDeleteResponse(BaseModel):
    """Response after deleting a schedule."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "message": "Schedule 'Daily Cleanup' deleted successfully"}
        }
    )

    success: bool = Field(True, description="Delete succeeded")
    message: str = Field(..., description="Confirmation message")


class ScheduleToggleResponse(BaseModel):
    """Response after toggling a schedule."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "enabled": False,
                "message": "Schedule 'Daily Cleanup' disabled",
            }
        }
    )

    success: bool = Field(True, description="Toggle succeeded")
    enabled: bool = Field(..., description="New enabled state")
    message: str = Field(..., description="Confirmation message")
