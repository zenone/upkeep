"""Tests for ScheduleAPI.

TDD approach: These tests define the expected behavior of ScheduleAPI
before implementation. Tests will initially fail (red), then we implement
the API to make them pass (green), then refactor.

Test Coverage:
- Schedule model validation (Pydantic models)
- CRUD operations (create, read, update, delete)
- Business logic (ID generation, timestamps, next run calculation)
- Conflict detection and warnings
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, time
from typing import List

from mac_maintenance.api.models.schedule import (
    ScheduleConfig,
    ScheduleFrequency,
    DayOfWeek,
    ScheduleResponse,
    ScheduleListResponse,
)
from mac_maintenance.core.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
)


class TestScheduleModels:
    """Test Pydantic schedule models and validation."""

    def test_create_daily_schedule(self):
        """Should create a valid daily schedule."""
        schedule = ScheduleConfig(
            name="Daily Cleanup",
            description="Clean caches and logs",
            operations=["trim_logs", "flush_dns"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time(3, 0, 0),
            enabled=True
        )

        assert schedule.name == "Daily Cleanup"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.time_of_day == time(3, 0, 0)
        assert len(schedule.operations) == 2
        assert schedule.enabled is True

    def test_create_weekly_schedule(self):
        """Should create a valid weekly schedule with days."""
        schedule = ScheduleConfig(
            name="Weekly Maintenance",
            operations=["verify_disk", "update_homebrew"],
            frequency=ScheduleFrequency.WEEKLY,
            time_of_day=time(3, 0, 0),
            days_of_week=[DayOfWeek.SUNDAY, DayOfWeek.WEDNESDAY]
        )

        assert schedule.frequency == ScheduleFrequency.WEEKLY
        assert len(schedule.days_of_week) == 2
        assert DayOfWeek.SUNDAY in schedule.days_of_week

    def test_weekly_schedule_requires_days(self):
        """Weekly schedules MUST have days_of_week."""
        with pytest.raises(ValueError, match="days_of_week required"):
            ScheduleConfig(
                name="Invalid Weekly",
                operations=["verify_disk"],
                frequency=ScheduleFrequency.WEEKLY,
                time_of_day=time(3, 0, 0),
                # Missing days_of_week - should raise error
            )

    def test_create_monthly_schedule(self):
        """Should create a valid monthly schedule with day_of_month."""
        schedule = ScheduleConfig(
            name="Monthly Maintenance",
            operations=["verify_disk", "repair_disk"],
            frequency=ScheduleFrequency.MONTHLY,
            time_of_day=time(4, 0, 0),
            day_of_month=15
        )

        assert schedule.frequency == ScheduleFrequency.MONTHLY
        assert schedule.day_of_month == 15

    def test_monthly_schedule_requires_day(self):
        """Monthly schedules MUST have day_of_month."""
        with pytest.raises(ValueError, match="day_of_month required"):
            ScheduleConfig(
                name="Invalid Monthly",
                operations=["verify_disk"],
                frequency=ScheduleFrequency.MONTHLY,
                time_of_day=time(3, 0, 0),
                # Missing day_of_month - should raise error
            )

    def test_day_of_month_range_validation(self):
        """day_of_month must be 1-28 (avoid month-end issues)."""
        # Valid: day 1
        schedule1 = ScheduleConfig(
            name="First of Month",
            operations=["verify_disk"],
            frequency=ScheduleFrequency.MONTHLY,
            time_of_day=time(3, 0, 0),
            day_of_month=1
        )
        assert schedule1.day_of_month == 1

        # Valid: day 28
        schedule2 = ScheduleConfig(
            name="28th of Month",
            operations=["verify_disk"],
            frequency=ScheduleFrequency.MONTHLY,
            time_of_day=time(3, 0, 0),
            day_of_month=28
        )
        assert schedule2.day_of_month == 28

        # Invalid: day 0
        with pytest.raises(ValueError):
            ScheduleConfig(
                name="Invalid Day 0",
                operations=["verify_disk"],
                frequency=ScheduleFrequency.MONTHLY,
                time_of_day=time(3, 0, 0),
                day_of_month=0
            )

        # Invalid: day 29 (February might not have it)
        with pytest.raises(ValueError):
            ScheduleConfig(
                name="Invalid Day 29",
                operations=["verify_disk"],
                frequency=ScheduleFrequency.MONTHLY,
                time_of_day=time(3, 0, 0),
                day_of_month=29
            )

    def test_operations_not_empty(self):
        """operations list must contain at least one operation."""
        with pytest.raises(ValueError):
            ScheduleConfig(
                name="No Operations",
                operations=[],  # Empty - should raise error
                frequency=ScheduleFrequency.DAILY,
                time_of_day=time(3, 0, 0)
            )

    def test_name_length_validation(self):
        """name must be 1-100 characters."""
        # Too short (empty)
        with pytest.raises(ValueError):
            ScheduleConfig(
                name="",  # Empty - should raise error
                operations=["verify_disk"],
                frequency=ScheduleFrequency.DAILY,
                time_of_day=time(3, 0, 0)
            )

        # Too long (>100 chars)
        with pytest.raises(ValueError):
            ScheduleConfig(
                name="A" * 101,  # 101 chars - should raise error
                operations=["verify_disk"],
                frequency=ScheduleFrequency.DAILY,
                time_of_day=time(3, 0, 0)
            )

        # Valid: exactly 100 chars
        schedule = ScheduleConfig(
            name="A" * 100,
            operations=["verify_disk"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time(3, 0, 0)
        )
        assert len(schedule.name) == 100

    def test_schedule_id_generation(self):
        """Should auto-generate UUID if id not provided."""
        schedule = ScheduleConfig(
            name="Test Schedule",
            operations=["verify_disk"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time(3, 0, 0)
        )

        # Initially no ID
        assert schedule.id is None

        # Generate ID
        schedule_id = schedule.generate_id()

        assert schedule_id is not None
        assert schedule_id.startswith("schedule-")
        assert len(schedule_id) > len("schedule-")
        assert schedule.id == schedule_id

        # Calling again should return same ID
        same_id = schedule.generate_id()
        assert same_id == schedule_id

    def test_schedule_timestamps(self):
        """Should set created_at and updated_at timestamps."""
        schedule = ScheduleConfig(
            name="Test Schedule",
            operations=["verify_disk"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time(3, 0, 0)
        )

        # Initially no timestamps
        assert schedule.created_at is None
        assert schedule.updated_at is None

        # Set timestamps for new schedule
        schedule.set_timestamps(is_new=True)

        assert schedule.created_at is not None
        assert schedule.updated_at is not None
        assert isinstance(schedule.created_at, datetime)
        assert isinstance(schedule.updated_at, datetime)

        # Both should be approximately the same time
        time_diff = (schedule.updated_at - schedule.created_at).total_seconds()
        assert time_diff < 1  # Less than 1 second apart

        # Update timestamps (not new)
        original_created = schedule.created_at
        import time as time_module
        time_module.sleep(0.01)  # Small delay

        schedule.set_timestamps(is_new=False)

        # created_at should not change
        assert schedule.created_at == original_created
        # updated_at should be newer
        assert schedule.updated_at > original_created


class TestScheduleAPICRUD:
    """Test ScheduleAPI CRUD operations.

    Note: These tests require ScheduleAPI implementation.
    Initially will fail (TDD red phase).
    """

    @pytest.fixture
    def temp_schedule_file(self, tmp_path):
        """Create temporary schedules.json file."""
        schedule_file = tmp_path / "schedules.json"
        schedule_file.write_text("[]")  # Empty schedule list
        return schedule_file

    @pytest.fixture
    def schedule_api(self, temp_schedule_file):
        """Create ScheduleAPI instance with temporary storage."""
        from mac_maintenance.api.schedule import ScheduleAPI
        return ScheduleAPI(storage_path=temp_schedule_file)

    def test_api_initialization(self, schedule_api):
        """Should initialize ScheduleAPI without errors."""
        assert schedule_api is not None
        assert hasattr(schedule_api, 'create_schedule')
        assert hasattr(schedule_api, 'get_schedule')
        assert hasattr(schedule_api, 'list_schedules')
        assert hasattr(schedule_api, 'update_schedule')
        assert hasattr(schedule_api, 'delete_schedule')

    def test_create_schedule(self, schedule_api):
        """Should create and persist a new schedule."""
        schedule_data = {
            "name": "Daily Cleanup",
            "operations": ["trim_logs", "flush_dns"],
            "frequency": "daily",
            "time_of_day": "03:00:00",
            "enabled": True
        }

        response = schedule_api.create_schedule(schedule_data)

        assert response.success is True
        assert response.error is None
        assert response.schedule is not None
        assert response.schedule.id is not None
        assert response.schedule.name == "Daily Cleanup"
        assert response.schedule.created_at is not None

    def test_create_schedule_is_idempotent_by_name(self, schedule_api):
        """Creating a schedule with an existing name should update, not create a new ID.

        Hygiene requirement: prevents launchd spam (lots of python3 login items).
        """
        first = schedule_api.create_schedule({
            "name": "Nightly",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00",
            "enabled": True,
        })
        assert first.success
        first_id = first.schedule.id

        second = schedule_api.create_schedule({
            "name": "Nightly",  # same name
            "operations": ["verify_disk", "trim_logs"],
            "frequency": "daily",
            "time_of_day": "03:30:00",
            "enabled": False,
        })
        assert second.success
        assert second.schedule.id == first_id

        # Should still be exactly one schedule stored
        listed = schedule_api.list_schedules()
        assert listed.success
        assert listed.count == 1
        assert listed.schedules[0].id == first_id
        assert listed.schedules[0].enabled is False
        assert "trim_logs" in listed.schedules[0].operations

    def test_get_schedule(self, schedule_api):
        """Should retrieve a schedule by ID."""
        # Create schedule first
        schedule_data = {
            "name": "Test Schedule",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        }
        create_response = schedule_api.create_schedule(schedule_data)
        schedule_id = create_response.schedule.id

        # Get schedule
        response = schedule_api.get_schedule(schedule_id)

        assert response.success is True
        assert response.schedule is not None
        assert response.schedule.id == schedule_id
        assert response.schedule.name == "Test Schedule"

    def test_get_nonexistent_schedule(self, schedule_api):
        """Should handle nonexistent schedule IDs gracefully."""
        response = schedule_api.get_schedule("nonexistent-id")

        assert response.success is False
        assert response.error is not None
        assert "not found" in response.error.lower()
        assert response.schedule is None

    def test_list_schedules_empty(self, schedule_api):
        """Should return empty list when no schedules exist."""
        response = schedule_api.list_schedules()

        assert response.success is True
        assert response.count == 0
        assert len(response.schedules) == 0

    def test_list_schedules_multiple(self, schedule_api):
        """Should list all schedules."""
        # Create multiple schedules
        schedule_api.create_schedule({
            "name": "Schedule 1",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_api.create_schedule({
            "name": "Schedule 2",
            "operations": ["trim_logs"],
            "frequency": "weekly",
            "time_of_day": "04:00:00",
            "days_of_week": ["sunday"]
        })

        # List schedules
        response = schedule_api.list_schedules()

        assert response.success is True
        assert response.count == 2
        assert len(response.schedules) == 2

    def test_update_schedule(self, schedule_api):
        """Should update an existing schedule."""
        # Create schedule
        create_response = schedule_api.create_schedule({
            "name": "Original Name",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_id = create_response.schedule.id

        # Update schedule
        update_response = schedule_api.update_schedule(schedule_id, {
            "name": "Updated Name",
            "operations": ["verify_disk", "trim_logs"]
        })

        assert update_response.success is True
        assert update_response.schedule.name == "Updated Name"
        assert len(update_response.schedule.operations) == 2
        assert update_response.schedule.updated_at > create_response.schedule.created_at

    def test_update_nonexistent_schedule(self, schedule_api):
        """Should handle updating nonexistent schedule."""
        response = schedule_api.update_schedule("nonexistent-id", {
            "name": "New Name"
        })

        assert response.success is False
        assert response.error is not None
        assert "not found" in response.error.lower()

    def test_delete_schedule(self, schedule_api):
        """Should delete a schedule."""
        # Create schedule
        create_response = schedule_api.create_schedule({
            "name": "To Be Deleted",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_id = create_response.schedule.id

        # Delete schedule
        delete_response = schedule_api.delete_schedule(schedule_id)

        assert delete_response.success is True

        # Verify it's gone
        get_response = schedule_api.get_schedule(schedule_id)
        assert get_response.success is False
        assert get_response.schedule is None

    def test_delete_nonexistent_schedule(self, schedule_api):
        """Should handle deleting nonexistent schedule."""
        response = schedule_api.delete_schedule("nonexistent-id")

        assert response.success is False
        assert response.error is not None


class TestScheduleAPILogic:
    """Test ScheduleAPI business logic and calculations."""

    @pytest.fixture
    def temp_schedule_file(self, tmp_path):
        """Create temporary schedules.json file."""
        schedule_file = tmp_path / "schedules.json"
        schedule_file.write_text("[]")
        return schedule_file

    @pytest.fixture
    def schedule_api(self, temp_schedule_file):
        """Create ScheduleAPI instance."""
        from mac_maintenance.api.schedule import ScheduleAPI
        return ScheduleAPI(storage_path=temp_schedule_file)

    def test_enable_disable_schedule(self, schedule_api):
        """Should toggle schedule enabled state."""
        # Create enabled schedule
        create_response = schedule_api.create_schedule({
            "name": "Test Schedule",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00",
            "enabled": True
        })
        schedule_id = create_response.schedule.id
        assert create_response.schedule.enabled is True

        # Disable
        disable_response = schedule_api.update_schedule(schedule_id, {
            "enabled": False
        })
        assert disable_response.success is True
        assert disable_response.schedule.enabled is False

        # Enable again
        enable_response = schedule_api.update_schedule(schedule_id, {
            "enabled": True
        })
        assert enable_response.success is True
        assert enable_response.schedule.enabled is True

    def test_update_last_run(self, schedule_api):
        """Should track last execution time."""
        # Create schedule
        create_response = schedule_api.create_schedule({
            "name": "Test Schedule",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_id = create_response.schedule.id
        assert create_response.schedule.last_run is None

        # Update last run
        now = datetime.now()
        update_response = schedule_api.update_schedule(schedule_id, {
            "last_run": now
        })

        assert update_response.success is True
        assert update_response.schedule.last_run is not None
        # Should be approximately the same time (allowing for serialization)
        time_diff = abs((update_response.schedule.last_run - now).total_seconds())
        assert time_diff < 1

    def test_calculate_next_run_daily(self, schedule_api):
        """Should calculate next run for daily schedules."""
        # Create daily schedule at 3 AM
        create_response = schedule_api.create_schedule({
            "name": "Daily Schedule",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })

        schedule = create_response.schedule
        next_run = schedule_api.calculate_next_run(schedule)

        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run.hour == 3
        assert next_run.minute == 0
        # Next run should be in the future
        assert next_run > datetime.now()
        # For daily, should be within 24 hours
        time_until = (next_run - datetime.now()).total_seconds()
        assert 0 < time_until <= 86400  # 24 hours in seconds

    def test_calculate_next_run_weekly(self, schedule_api):
        """Should calculate next run for weekly schedules."""
        # Create weekly schedule on Sundays at 3 AM
        create_response = schedule_api.create_schedule({
            "name": "Weekly Schedule",
            "operations": ["verify_disk"],
            "frequency": "weekly",
            "time_of_day": "03:00:00",
            "days_of_week": ["sunday"]
        })

        schedule = create_response.schedule
        next_run = schedule_api.calculate_next_run(schedule)

        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run.weekday() == 6  # Sunday is 6
        assert next_run.hour == 3
        assert next_run.minute == 0
        # Next run should be in the future
        assert next_run > datetime.now()
        # For weekly, should be within 7 days
        time_until = (next_run - datetime.now()).total_seconds()
        assert 0 < time_until <= 604800  # 7 days in seconds

    def test_calculate_next_run_monthly(self, schedule_api):
        """Should calculate next run for monthly schedules."""
        # Create monthly schedule on 15th at 4 AM
        create_response = schedule_api.create_schedule({
            "name": "Monthly Schedule",
            "operations": ["verify_disk"],
            "frequency": "monthly",
            "time_of_day": "04:00:00",
            "day_of_month": 15
        })

        schedule = create_response.schedule
        next_run = schedule_api.calculate_next_run(schedule)

        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run.day == 15
        assert next_run.hour == 4
        assert next_run.minute == 0
        # Next run should be in the future
        assert next_run > datetime.now()

    def test_persistence_across_restarts(self, temp_schedule_file):
        """Schedules should persist across API restarts."""
        from mac_maintenance.api.schedule import ScheduleAPI

        # Create schedule with first API instance
        api1 = ScheduleAPI(storage_path=temp_schedule_file)
        create_response = api1.create_schedule({
            "name": "Persistent Schedule",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_id = create_response.schedule.id

        # Create new API instance (simulates restart)
        api2 = ScheduleAPI(storage_path=temp_schedule_file)

        # Should be able to retrieve schedule
        get_response = api2.get_schedule(schedule_id)
        assert get_response.success is True
        assert get_response.schedule.name == "Persistent Schedule"


class TestScheduleAPIConflicts:
    """Test schedule conflict detection."""

    @pytest.fixture
    def temp_schedule_file(self, tmp_path):
        """Create temporary schedules.json file."""
        schedule_file = tmp_path / "schedules.json"
        schedule_file.write_text("[]")
        return schedule_file

    @pytest.fixture
    def schedule_api(self, temp_schedule_file):
        """Create ScheduleAPI instance."""
        from mac_maintenance.api.schedule import ScheduleAPI
        return ScheduleAPI(storage_path=temp_schedule_file)

    def test_no_conflict_different_times(self, schedule_api):
        """Schedules at different times should not conflict."""
        # Create first schedule at 3 AM
        schedule_api.create_schedule({
            "name": "Schedule 1",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })

        # Create second schedule at 4 AM (should be OK)
        response = schedule_api.create_schedule({
            "name": "Schedule 2",
            "operations": ["trim_logs"],
            "frequency": "daily",
            "time_of_day": "04:00:00"
        })

        assert response.success is True
        # Should not have conflict warning
        assert response.message is None or "conflict" not in response.message.lower()

    def test_conflict_warning_same_time(self, schedule_api):
        """Should warn about schedules at the same time."""
        # Create first schedule at 3 AM
        schedule_api.create_schedule({
            "name": "Schedule 1",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })

        # Create second schedule at 3 AM (potential conflict)
        response = schedule_api.create_schedule({
            "name": "Schedule 2",
            "operations": ["trim_logs"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })

        # Should still succeed but with warning
        assert response.success is True
        assert response.message is not None
        assert "conflict" in response.message.lower() or "same time" in response.message.lower()

    def test_get_schedule_conflicts(self, schedule_api):
        """Should be able to query for schedule conflicts."""
        # Create schedules at same time
        schedule_api.create_schedule({
            "name": "Schedule 1",
            "operations": ["verify_disk"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })
        schedule_api.create_schedule({
            "name": "Schedule 2",
            "operations": ["trim_logs"],
            "frequency": "daily",
            "time_of_day": "03:00:00"
        })

        # Check for conflicts
        conflicts = schedule_api.get_conflicts()

        assert len(conflicts) > 0
        # Each conflict should identify the overlapping schedules
        conflict = conflicts[0]
        assert "schedule_ids" in conflict or "schedules" in conflict
        assert "time" in conflict or "time_of_day" in conflict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
