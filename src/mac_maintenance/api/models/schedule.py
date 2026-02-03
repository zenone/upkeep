"""Schedule data models for recurring maintenance tasks.

Pydantic models for schedule configuration, validation, and API responses.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime, time
from enum import Enum
import uuid


class ScheduleFrequency(str, Enum):
    """Schedule frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Advanced: custom intervals (future enhancement)


class DayOfWeek(str, Enum):
    """Days of the week for weekly schedules."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ScheduleConfig(BaseModel):
    """Configuration for a scheduled maintenance task.

    Represents a recurring maintenance schedule with timing, operations,
    and metadata. Used by ScheduleAPI and persisted to schedules.json.

    Validation Rules:
    - Weekly schedules MUST provide days_of_week
    - Monthly schedules MUST provide day_of_month (1-28)
    - operations list must not be empty
    """

    # Identification
    id: Optional[str] = Field(
        default=None,
        description="Unique schedule ID (auto-generated UUID)"
    )
    name: str = Field(
        ...,
        description="Human-readable schedule name",
        min_length=1,
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of what this schedule does"
    )

    # Operations to execute
    operations: List[str] = Field(
        ...,
        description="List of maintenance operation IDs to run",
        min_length=1
    )

    # Schedule timing
    frequency: ScheduleFrequency = Field(
        ...,
        description="How often to run (daily, weekly, monthly)"
    )
    time_of_day: time = Field(
        ...,
        description="Time of day to run (HH:MM:SS)"
    )

    # Frequency-specific fields
    days_of_week: Optional[List[DayOfWeek]] = Field(
        None,
        description="Days for weekly schedules (required for weekly)"
    )
    day_of_month: Optional[int] = Field(
        None,
        description="Day of month (1-28) for monthly schedules",
        ge=1,
        le=28  # Avoid month-end issues (Feb has 28 days)
    )

    # State
    enabled: bool = Field(
        True,
        description="Whether schedule is currently active"
    )

    # Scheduling behavior
    wake_mac: bool = Field(
        False,
        description="Attempt to wake the Mac for this schedule (best-effort; may require admin)"
    )
    notify: bool = Field(
        True,
        description="Show a macOS notification after the schedule runs (success/fail summary)"
    )

    # Metadata
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp (auto-set)"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp (auto-set)"
    )
    last_run: Optional[datetime] = Field(
        None,
        description="Last execution timestamp"
    )
    next_run: Optional[datetime] = Field(
        None,
        description="Next scheduled execution (calculated)"
    )

    @model_validator(mode='after')
    def validate_schedule_requirements(self):
        """Validate frequency-specific requirements."""
        # Weekly schedules MUST have days_of_week
        if self.frequency == ScheduleFrequency.WEEKLY:
            if not self.days_of_week or len(self.days_of_week) == 0:
                raise ValueError("days_of_week required for weekly schedules")

        # Monthly schedules MUST have day_of_month
        if self.frequency == ScheduleFrequency.MONTHLY:
            if self.day_of_month is None:
                raise ValueError("day_of_month required for monthly schedules")

        return self

    def generate_id(self) -> str:
        """Generate a unique ID for this schedule if not already set."""
        if not self.id:
            self.id = f"schedule-{uuid.uuid4()}"
        return self.id

    def set_timestamps(self, is_new: bool = False):
        """Set created_at and updated_at timestamps."""
        now = datetime.now()
        if is_new or not self.created_at:
            self.created_at = now
        self.updated_at = now


class ScheduleResponse(BaseModel):
    """API response for single schedule operations."""
    success: bool = Field(..., description="Whether operation succeeded")
    schedule: Optional[ScheduleConfig] = Field(
        None,
        description="Schedule data (if successful)"
    )
    error: Optional[str] = Field(
        None,
        description="Error message (if failed)"
    )
    message: Optional[str] = Field(
        None,
        description="Additional information"
    )


class ScheduleListResponse(BaseModel):
    """API response for listing schedules."""
    success: bool = Field(..., description="Whether operation succeeded")
    schedules: List[ScheduleConfig] = Field(
        default_factory=list,
        description="List of schedules"
    )
    count: int = Field(..., description="Total number of schedules")
    error: Optional[str] = Field(
        None,
        description="Error message (if failed)"
    )
