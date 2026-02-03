"""Tests for launchd integration.

TDD approach: These tests define the expected behavior of LaunchdGenerator
before implementation.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import time as time_type
from unittest.mock import Mock, patch, MagicMock
import plistlib

from mac_maintenance.core.launchd import LaunchdGenerator
from mac_maintenance.api.models.schedule import (
    ScheduleConfig,
    ScheduleFrequency,
    DayOfWeek,
)
from mac_maintenance.core.exceptions import (
    ValidationError,
    DaemonNotAvailableError,
)


class TestLaunchdGenerator:
    """Test launchd plist generation and registration."""

    @pytest.fixture
    def temp_plist_dir(self, tmp_path):
        """Create temporary directory for plist files."""
        plist_dir = tmp_path / "LaunchDaemons"
        plist_dir.mkdir()
        return plist_dir

    @pytest.fixture
    def generator(self, temp_plist_dir):
        """Create LaunchdGenerator with temp directory."""
        return LaunchdGenerator(plist_dir=temp_plist_dir)

    @pytest.fixture
    def daily_schedule(self):
        """Create a daily schedule for testing."""
        schedule = ScheduleConfig(
            name="Daily Cleanup",
            operations=["trim_logs", "flush_dns"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time_type(3, 0, 0),
            enabled=True
        )
        schedule.generate_id()
        return schedule

    @pytest.fixture
    def weekly_schedule(self):
        """Create a weekly schedule for testing."""
        schedule = ScheduleConfig(
            name="Weekly Maintenance",
            operations=["verify_disk"],
            frequency=ScheduleFrequency.WEEKLY,
            time_of_day=time_type(3, 0, 0),
            days_of_week=[DayOfWeek.SUNDAY, DayOfWeek.WEDNESDAY],
            enabled=True
        )
        schedule.generate_id()
        return schedule

    @pytest.fixture
    def monthly_schedule(self):
        """Create a monthly schedule for testing."""
        schedule = ScheduleConfig(
            name="Monthly Maintenance",
            operations=["repair_disk"],
            frequency=ScheduleFrequency.MONTHLY,
            time_of_day=time_type(4, 0, 0),
            day_of_month=15,
            enabled=True
        )
        schedule.generate_id()
        return schedule

    def test_generator_initialization(self, generator, temp_plist_dir):
        """Should initialize with plist directory."""
        assert generator is not None
        assert generator.plist_dir == temp_plist_dir
        assert temp_plist_dir.exists()

    def test_generate_plist_daily(self, generator, daily_schedule):
        """Should generate valid plist for daily schedule."""
        plist_content = generator.generate_plist(daily_schedule)

        assert plist_content is not None
        assert isinstance(plist_content, dict)

        # Check required keys
        assert "Label" in plist_content
        assert "ProgramArguments" in plist_content
        assert "StartCalendarInterval" in plist_content

        # Check label format
        assert plist_content["Label"] == f"com.mac-maintenance.schedule.{daily_schedule.id}"

        # Check program arguments
        assert len(plist_content["ProgramArguments"]) > 0

        # Check calendar interval for daily (should have Hour and Minute only)
        interval = plist_content["StartCalendarInterval"]
        assert interval["Hour"] == 3
        assert interval["Minute"] == 0
        # Daily schedules should NOT have Weekday or Day
        assert "Weekday" not in interval
        assert "Day" not in interval

    def test_generate_plist_weekly(self, generator, weekly_schedule):
        """Should generate valid plist for weekly schedule."""
        plist_content = generator.generate_plist(weekly_schedule)

        assert plist_content is not None

        # Check calendar interval for weekly (should have Hour, Minute, and Weekday)
        interval = plist_content["StartCalendarInterval"]

        # Weekly schedules generate multiple intervals (one per day)
        # OR a single interval with Weekday array
        # Let's check that it's a list with multiple entries
        assert isinstance(interval, list)
        assert len(interval) == 2  # Sunday and Wednesday

        # Check first interval (should be Sunday = 0)
        assert interval[0]["Hour"] == 3
        assert interval[0]["Minute"] == 0
        assert interval[0]["Weekday"] == 0  # Sunday

        # Check second interval (should be Wednesday = 3)
        assert interval[1]["Hour"] == 3
        assert interval[1]["Minute"] == 0
        assert interval[1]["Weekday"] == 3  # Wednesday

    def test_generate_plist_monthly(self, generator, monthly_schedule):
        """Should generate valid plist for monthly schedule."""
        plist_content = generator.generate_plist(monthly_schedule)

        assert plist_content is not None

        # Check calendar interval for monthly (should have Hour, Minute, and Day)
        interval = plist_content["StartCalendarInterval"]
        assert interval["Hour"] == 4
        assert interval["Minute"] == 0
        assert interval["Day"] == 15
        # Monthly schedules should NOT have Weekday
        assert "Weekday" not in interval

    def test_generate_plist_includes_logging(self, generator, daily_schedule):
        """Should include stdout/stderr logging paths."""
        plist_content = generator.generate_plist(daily_schedule)

        assert "StandardOutPath" in plist_content
        assert "StandardErrorPath" in plist_content

        # Check paths are reasonable
        stdout_path = plist_content["StandardOutPath"]
        stderr_path = plist_content["StandardErrorPath"]

        assert ".mac-maintenance" in stdout_path or "/var/log" in stdout_path
        assert ".mac-maintenance" in stderr_path or "/var/log" in stderr_path

    def test_generate_plist_disabled_schedule(self, generator, daily_schedule):
        """Disabled schedules should still generate plist but not be loaded."""
        daily_schedule.enabled = False
        plist_content = generator.generate_plist(daily_schedule)

        # Should still generate valid plist
        assert plist_content is not None
        assert "Disabled" in plist_content
        assert plist_content["Disabled"] is True

    def test_save_plist(self, generator, daily_schedule, temp_plist_dir):
        """Should save plist to file."""
        plist_path = generator.save_plist(daily_schedule)

        assert plist_path is not None
        assert plist_path.exists()
        assert plist_path.parent == temp_plist_dir
        assert plist_path.name == f"com.mac-maintenance.schedule.{daily_schedule.id}.plist"

        # Verify file is valid plist
        with open(plist_path, 'rb') as f:
            plist_data = plistlib.load(f)
            assert "Label" in plist_data

    def test_save_plist_creates_directory(self, daily_schedule):
        """Should create plist directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_dir = Path(tmpdir) / "new_dir" / "LaunchDaemons"
            generator = LaunchdGenerator(plist_dir=nonexistent_dir)

            plist_path = generator.save_plist(daily_schedule)

            assert nonexistent_dir.exists()
            assert plist_path.exists()

    @patch('subprocess.run')
    def test_register_schedule(self, mock_run, generator, daily_schedule):
        """Should register schedule with launchctl."""
        # Mock successful launchctl load
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Save plist first
        plist_path = generator.save_plist(daily_schedule)

        # Register
        result = generator.register_schedule(daily_schedule.id)

        assert result is True

        # Check launchctl was called (idempotent registration does a best-effort bootout first)
        assert mock_run.call_count in (1, 2)

        # Last call should be the registration (bootstrap/load)
        args = mock_run.call_args[0][0]
        assert "launchctl" in args
        assert "bootstrap" in args or "load" in args
        assert str(plist_path) in args

    @patch('subprocess.run')
    def test_register_schedule_requires_sudo(self, mock_run, generator, daily_schedule):
        """LaunchAgents should not require sudo for registration."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        generator.save_plist(daily_schedule)
        generator.register_schedule(daily_schedule.id)

        args = mock_run.call_args[0][0]
        assert args[0] != "sudo"
        assert "launchctl" in args

    @patch('subprocess.run')
    def test_register_schedule_failure(self, mock_run, generator, daily_schedule):
        """Should handle launchctl failure."""
        # Mock failed launchctl load
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Operation not permitted"
        )

        generator.save_plist(daily_schedule)
        result = generator.register_schedule(daily_schedule.id)

        assert result is False

    @patch('subprocess.run')
    def test_unregister_schedule(self, mock_run, generator, daily_schedule):
        """Should unregister schedule with launchctl."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        generator.save_plist(daily_schedule)
        result = generator.unregister_schedule(daily_schedule.id)

        assert result is True

        # Check launchctl unload was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "launchctl" in args
        assert "bootout" in args or "unload" in args

    @patch('subprocess.run')
    def test_remove_plist(self, mock_run, generator, daily_schedule):
        """Should remove plist file after unregistering."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        plist_path = generator.save_plist(daily_schedule)
        assert plist_path.exists()

        generator.unregister_schedule(daily_schedule.id)
        generator.remove_plist(daily_schedule.id)

        assert not plist_path.exists()

    def test_get_plist_path(self, generator, daily_schedule):
        """Should return correct plist path for schedule ID."""
        path = generator.get_plist_path(daily_schedule.id)

        assert path.parent == generator.plist_dir
        assert path.name == f"com.mac-maintenance.schedule.{daily_schedule.id}.plist"

    def test_is_registered(self, generator, daily_schedule):
        """Should check if schedule is registered."""
        # Not registered yet
        assert generator.is_registered(daily_schedule.id) is False

        # Save plist
        generator.save_plist(daily_schedule)

        # Still not registered (plist exists but not loaded)
        # In real implementation, this would check launchctl list
        # For now, just check plist exists
        assert generator.get_plist_path(daily_schedule.id).exists()

    def test_validate_schedule_id(self, generator):
        """Should validate schedule ID format."""
        # Valid IDs
        assert generator.validate_schedule_id("schedule-abc123") is True
        assert generator.validate_schedule_id("schedule-12345678-1234-1234-1234-123456789012") is True

        # Invalid IDs
        assert generator.validate_schedule_id("invalid") is False
        assert generator.validate_schedule_id("../etc/passwd") is False
        assert generator.validate_schedule_id("schedule; rm -rf /") is False

    def test_list_registered_schedules(self, generator, daily_schedule, weekly_schedule):
        """Should list all registered schedule IDs."""
        # Save multiple plists
        generator.save_plist(daily_schedule)
        generator.save_plist(weekly_schedule)

        # List schedules
        schedule_ids = generator.list_registered_schedules()

        assert len(schedule_ids) >= 2
        assert daily_schedule.id in schedule_ids
        assert weekly_schedule.id in schedule_ids


class TestSchedulerEntryPoint:
    """Test the scheduler entry point script that executes scheduled tasks."""

    def test_entry_point_exists(self):
        """Scheduler entry point script should exist."""
        from mac_maintenance.core.launchd import run_scheduled_task
        assert run_scheduled_task is not None

    @patch('mac_maintenance.api.schedule.ScheduleAPI')
    @patch('mac_maintenance.api.maintenance.MaintenanceAPI')
    def test_run_scheduled_task(self, mock_maintenance_api, mock_schedule_api):
        """Should load schedule and execute operations."""
        from mac_maintenance.core.launchd import run_scheduled_task

        # Mock schedule
        schedule = ScheduleConfig(
            id="schedule-test",
            name="Test Schedule",
            operations=["trim_logs", "flush_dns"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time_type(3, 0, 0)
        )

        # Mock API responses
        mock_schedule_api.return_value.get_schedule.return_value.success = True
        mock_schedule_api.return_value.get_schedule.return_value.schedule = schedule

        # Run scheduled task
        result = run_scheduled_task("schedule-test")

        assert result is True

        # Verify schedule was loaded
        mock_schedule_api.return_value.get_schedule.assert_called_once_with("schedule-test")

    @patch('mac_maintenance.api.schedule.ScheduleAPI')
    def test_run_scheduled_task_not_found(self, mock_schedule_api):
        """Should handle schedule not found."""
        from mac_maintenance.core.launchd import run_scheduled_task

        # Mock schedule not found
        mock_schedule_api.return_value.get_schedule.return_value.success = False
        mock_schedule_api.return_value.get_schedule.return_value.schedule = None

        result = run_scheduled_task("nonexistent")

        assert result is False

    @patch('mac_maintenance.api.schedule.ScheduleAPI')
    def test_run_scheduled_task_updates_last_run(self, mock_schedule_api):
        """Should update schedule last_run timestamp after execution."""
        from mac_maintenance.core.launchd import run_scheduled_task
        from datetime import datetime

        schedule = ScheduleConfig(
            id="schedule-test",
            name="Test Schedule",
            operations=["trim_logs"],
            frequency=ScheduleFrequency.DAILY,
            time_of_day=time_type(3, 0, 0)
        )

        mock_schedule_api.return_value.get_schedule.return_value.success = True
        mock_schedule_api.return_value.get_schedule.return_value.schedule = schedule

        run_scheduled_task("schedule-test")

        # Verify last_run was updated
        mock_schedule_api.return_value.update_schedule.assert_called_once()
        update_call = mock_schedule_api.return_value.update_schedule.call_args
        assert update_call[0][0] == "schedule-test"
        assert "last_run" in update_call[0][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
