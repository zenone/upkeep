"""Launchd integration for macOS scheduled tasks.

API-First Design: This module provides a clean interface for managing
launchd plists and registering scheduled maintenance tasks.

Key Concepts:
- Launchd manages schedules (daemon doesn't need to run continuously)
- Each schedule gets its own plist file
- Plists use StartCalendarInterval for timing
- Registration requires sudo (system-level LaunchDaemons)
"""

import logging
import subprocess
import plistlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from mac_maintenance.api.models.schedule import (
    ScheduleConfig,
    ScheduleFrequency,
    DayOfWeek,
)
from mac_maintenance.core.exceptions import ValidationError


class LaunchdGenerator:
    """Generator for launchd plist files and schedule registration.

    API-First Design:
    - Clean interface for plist generation
    - Handles launchctl commands
    - Validates schedule IDs for security
    - Provides registration status checks
    """

    def __init__(self, plist_dir: Optional[Path] = None):
        """Initialize LaunchdGenerator.

        Args:
            plist_dir: Directory for plist files (default: /Library/LaunchDaemons)
        """
        self.logger = logging.getLogger("core.LaunchdGenerator")

        # Default to system LaunchDaemons directory
        if plist_dir is None:
            plist_dir = Path("/Library/LaunchDaemons")

        self.plist_dir = Path(plist_dir)

        # Ensure directory exists
        if not self.plist_dir.exists():
            self.plist_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created plist directory: {self.plist_dir}")

        self.logger.info(f"LaunchdGenerator initialized with plist_dir: {self.plist_dir}")

    def generate_plist(self, schedule: ScheduleConfig) -> Dict[str, Any]:
        """Generate launchd plist dictionary for a schedule.

        Args:
            schedule: ScheduleConfig to generate plist for

        Returns:
            Dictionary representing plist structure
        """
        self.logger.debug(f"Generating plist for schedule: {schedule.id}")

        # Build program arguments (path to scheduler script + schedule ID)
        program_arguments = [
            "/usr/bin/python3",
            str(Path(__file__).parent.parent / "scripts" / "run_schedule.py"),
            schedule.id
        ]

        # Build calendar interval based on frequency
        calendar_interval = self._build_calendar_interval(schedule)

        # Build plist structure
        plist = {
            "Label": f"com.mac-maintenance.schedule.{schedule.id}",
            "ProgramArguments": program_arguments,
            "StartCalendarInterval": calendar_interval,
            "RunAtLoad": False,  # Don't run immediately when loaded
            "StandardOutPath": str(Path.home() / ".mac-maintenance" / "logs" / f"{schedule.id}.log"),
            "StandardErrorPath": str(Path.home() / ".mac-maintenance" / "logs" / f"{schedule.id}.error.log"),
            "UserName": "root",  # Run as root for system maintenance tasks
        }

        # Add disabled flag if schedule is disabled
        if not schedule.enabled:
            plist["Disabled"] = True

        return plist

    def _build_calendar_interval(self, schedule: ScheduleConfig) -> Any:
        """Build StartCalendarInterval for schedule.

        Args:
            schedule: ScheduleConfig to build interval for

        Returns:
            Calendar interval dict or list of dicts
        """
        hour = schedule.time_of_day.hour
        minute = schedule.time_of_day.minute

        if schedule.frequency == ScheduleFrequency.DAILY:
            # Daily: Run every day at specified time
            return {
                "Hour": hour,
                "Minute": minute,
            }

        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            # Weekly: Run on specific days of week
            # Create separate interval for each day
            if not schedule.days_of_week:
                raise ValidationError("Weekly schedule requires days_of_week")

            # Map DayOfWeek to launchd Weekday (0=Sunday, 1=Monday, etc.)
            day_map = {
                DayOfWeek.SUNDAY: 0,
                DayOfWeek.MONDAY: 1,
                DayOfWeek.TUESDAY: 2,
                DayOfWeek.WEDNESDAY: 3,
                DayOfWeek.THURSDAY: 4,
                DayOfWeek.FRIDAY: 5,
                DayOfWeek.SATURDAY: 6,
            }

            # Create interval for each day
            intervals = []
            for day in schedule.days_of_week:
                intervals.append({
                    "Hour": hour,
                    "Minute": minute,
                    "Weekday": day_map[day],
                })

            return intervals

        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            # Monthly: Run on specific day of month
            if schedule.day_of_month is None:
                raise ValidationError("Monthly schedule requires day_of_month")

            return {
                "Hour": hour,
                "Minute": minute,
                "Day": schedule.day_of_month,
            }

        else:
            raise ValidationError(f"Unsupported frequency: {schedule.frequency}")

    def save_plist(self, schedule: ScheduleConfig) -> Path:
        """Save plist to file.

        Args:
            schedule: ScheduleConfig to save plist for

        Returns:
            Path to saved plist file
        """
        self.logger.debug(f"Saving plist for schedule: {schedule.id}")

        # Ensure directory exists
        self.plist_dir.mkdir(parents=True, exist_ok=True)

        # Ensure log directory exists
        log_dir = Path.home() / ".mac-maintenance" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Generate plist
        plist_dict = self.generate_plist(schedule)

        # Get plist path
        plist_path = self.get_plist_path(schedule.id)

        # Write plist
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_dict, f)

        self.logger.info(f"Saved plist: {plist_path}")
        return plist_path

    def register_schedule(self, schedule_id: str) -> bool:
        """Register schedule with launchctl.

        Args:
            schedule_id: Schedule ID to register

        Returns:
            True if registration successful, False otherwise
        """
        self.logger.info(f"Registering schedule: {schedule_id}")

        # Validate schedule ID
        if not self.validate_schedule_id(schedule_id):
            self.logger.error(f"Invalid schedule ID: {schedule_id}")
            return False

        # Get plist path
        plist_path = self.get_plist_path(schedule_id)

        if not plist_path.exists():
            self.logger.error(f"Plist not found: {plist_path}")
            return False

        # Register with launchctl (requires sudo)
        try:
            result = subprocess.run(
                ["sudo", "launchctl", "load", str(plist_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully registered schedule: {schedule_id}")
                return True
            else:
                self.logger.error(f"Failed to register schedule: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout registering schedule: {schedule_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error registering schedule: {e}")
            return False

    def unregister_schedule(self, schedule_id: str) -> bool:
        """Unregister schedule with launchctl.

        Args:
            schedule_id: Schedule ID to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        self.logger.info(f"Unregistering schedule: {schedule_id}")

        # Validate schedule ID
        if not self.validate_schedule_id(schedule_id):
            self.logger.error(f"Invalid schedule ID: {schedule_id}")
            return False

        # Get plist path
        plist_path = self.get_plist_path(schedule_id)

        if not plist_path.exists():
            self.logger.debug(f"Plist not found (may already be unregistered): {plist_path}")
            return True  # Consider success if already gone

        # Unregister with launchctl (requires sudo)
        try:
            result = subprocess.run(
                ["sudo", "launchctl", "unload", str(plist_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully unregistered schedule: {schedule_id}")
                return True
            else:
                # Launchctl unload returns error if job not running, but that's OK
                self.logger.warning(f"launchctl unload returned error (may be OK): {result.stderr}")
                return True

        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout unregistering schedule: {schedule_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error unregistering schedule: {e}")
            return False

    def remove_plist(self, schedule_id: str) -> bool:
        """Remove plist file.

        Args:
            schedule_id: Schedule ID to remove plist for

        Returns:
            True if removal successful, False otherwise
        """
        self.logger.info(f"Removing plist for schedule: {schedule_id}")

        plist_path = self.get_plist_path(schedule_id)

        if not plist_path.exists():
            self.logger.debug(f"Plist not found: {plist_path}")
            return True  # Already gone

        try:
            plist_path.unlink()
            self.logger.info(f"Removed plist: {plist_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error removing plist: {e}")
            return False

    def get_plist_path(self, schedule_id: str) -> Path:
        """Get plist file path for schedule ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            Path to plist file
        """
        return self.plist_dir / f"com.mac-maintenance.schedule.{schedule_id}.plist"

    def is_registered(self, schedule_id: str) -> bool:
        """Check if schedule is registered with launchctl.

        Args:
            schedule_id: Schedule ID to check

        Returns:
            True if registered, False otherwise
        """
        # Check if plist exists (simple check for now)
        # TODO: Actually check launchctl list for more accurate status
        return self.get_plist_path(schedule_id).exists()

    def validate_schedule_id(self, schedule_id: str) -> bool:
        """Validate schedule ID format for security.

        Prevents path traversal and command injection attacks.

        Args:
            schedule_id: Schedule ID to validate

        Returns:
            True if valid, False otherwise
        """
        # Must start with "schedule-"
        if not schedule_id.startswith("schedule-"):
            return False

        # Must contain only alphanumeric, dash, and underscore
        # Prevents path traversal (../) and command injection (; rm -rf /)
        pattern = re.compile(r'^schedule-[a-zA-Z0-9\-]+$')
        return pattern.match(schedule_id) is not None

    def list_registered_schedules(self) -> List[str]:
        """List all registered schedule IDs.

        Returns:
            List of schedule IDs
        """
        schedule_ids = []

        # Find all plist files
        for plist_path in self.plist_dir.glob("com.mac-maintenance.schedule.*.plist"):
            # Extract schedule ID from filename
            filename = plist_path.stem  # com.mac-maintenance.schedule.schedule-abc123
            parts = filename.split(".")
            if len(parts) >= 4:
                schedule_id = parts[3]  # schedule-abc123
                schedule_ids.append(schedule_id)

        return schedule_ids


def run_scheduled_task(schedule_id: str) -> bool:
    """Entry point for scheduled task execution.

    This function is called by launchd at scheduled times.

    Args:
        schedule_id: Schedule ID to execute

    Returns:
        True if execution successful, False otherwise
    """
    logger = logging.getLogger("core.run_scheduled_task")
    logger.info(f"Running scheduled task: {schedule_id}")

    try:
        # Load schedule from API
        from mac_maintenance.api.schedule import ScheduleAPI

        schedule_api = ScheduleAPI()
        response = schedule_api.get_schedule(schedule_id)

        if not response.success or response.schedule is None:
            logger.error(f"Schedule not found: {schedule_id}")
            return False

        schedule = response.schedule

        # Check if schedule is enabled
        if not schedule.enabled:
            logger.warning(f"Schedule is disabled: {schedule_id}")
            return False

        logger.info(f"Executing operations for schedule: {schedule.name}")

        # Execute each operation
        from mac_maintenance.api.maintenance import MaintenanceAPI

        maintenance_api = MaintenanceAPI()

        for operation_id in schedule.operations:
            logger.info(f"Executing operation: {operation_id}")
            try:
                # Execute operation
                # Note: This is a simplified version; actual implementation
                # would need async handling or subprocess for operations
                result = maintenance_api.execute_operation(operation_id)
                logger.info(f"Operation {operation_id} completed: {result}")

            except Exception as e:
                logger.error(f"Operation {operation_id} failed: {e}")
                # Continue with other operations even if one fails

        # Update last_run timestamp
        schedule_api.update_schedule(schedule_id, {
            "last_run": datetime.now()
        })

        logger.info(f"Scheduled task completed: {schedule_id}")
        return True

    except Exception as e:
        logger.error(f"Error running scheduled task: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Entry point when called from launchd
    import sys

    if len(sys.argv) < 2:
        print("Usage: run_schedule.py <schedule_id>")
        sys.exit(1)

    schedule_id = sys.argv[1]
    success = run_scheduled_task(schedule_id)
    sys.exit(0 if success else 1)
