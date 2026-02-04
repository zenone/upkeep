"""Launchd integration for macOS scheduled tasks.

API-First Design: This module provides a clean interface for managing
launchd plists and registering scheduled maintenance tasks.

Key Concepts:
- Launchd manages schedules (daemon doesn't need to run continuously)
- Each schedule gets its own plist file
- Plists use StartCalendarInterval for timing
- Uses per-user LaunchAgents by default (no sudo prompts; daemon handles privileged ops)
"""

import asyncio
import logging
import os
import subprocess
import plistlib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from upkeep.api.models.schedule import (
    ScheduleConfig,
    ScheduleFrequency,
    DayOfWeek,
)
from upkeep.core.exceptions import ValidationError


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
            plist_dir: Directory for plist files (default: ~/Library/LaunchAgents)
        """
        self.logger = logging.getLogger("core.LaunchdGenerator")

        # Default to per-user LaunchAgents directory (avoids sudo and interactive auth)
        if plist_dir is None:
            plist_dir = Path.home() / "Library" / "LaunchAgents"

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

        # Build program arguments.
        # IMPORTANT: Avoid showing "python3" as a macOS Login Item / Background Item.
        # We do this by using a small runner script as ProgramArguments[0] (named for the app),
        # which then invokes the correct interpreter.
        runner = self._ensure_runner_script()
        if runner is not None:
            program_arguments = [
                str(runner),
                schedule.id,
            ]
        else:
            # Fallback: use the current interpreter to ensure the environment has upkeep installed.
            program_arguments = [
                sys.executable,
                "-m",
                "upkeep.scripts.run_schedule",
                schedule.id,
            ]

        # Build calendar interval based on frequency
        calendar_interval = self._build_calendar_interval(schedule)

        # Build plist structure
        plist = {
            "Label": f"com.upkeep.schedule.{schedule.id}",
            "ProgramArguments": program_arguments,
            "StartCalendarInterval": calendar_interval,
            "RunAtLoad": False,  # Don't run immediately when loaded
            "StandardOutPath": str(Path.home() / ".upkeep" / "logs" / f"{schedule.id}.log"),
            "StandardErrorPath": str(Path.home() / ".upkeep" / "logs" / f"{schedule.id}.error.log"),
            # Make Homebrew and other common CLI tools available when running under launchd
            "EnvironmentVariables": {
                "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            },
        }

        # Add disabled flag if schedule is disabled
        if not schedule.enabled:
            plist["Disabled"] = True

        return plist

    def _ensure_runner_script(self) -> Optional[Path]:
        """Ensure the schedule runner exists and is executable.

        We intentionally make the runner script the *first* ProgramArguments entry so
        macOS doesn't surface "python3" as a Background Item in Login Items.
        """
        bin_dir = Path.home() / ".upkeep" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        runner_path = bin_dir / "upkeep-run-schedule"

        # Ensure the project sources are importable even when running under launchd.
        # We embed the repo's src/ path at generation time (works for local clones).
        project_src = str((Path(__file__).resolve().parents[3] / "src").resolve())

        content = f"""#!/bin/bash
set -euo pipefail

PYTHON={sys.executable!s}
export PYTHONPATH=\"{project_src}${{PYTHONPATH:+:$PYTHONPATH}}\"

# Run the schedule by id
exec \"$PYTHON\" -m upkeep.scripts.run_schedule \"$1\"
"""

        try:
            if (not runner_path.exists()) or (runner_path.read_text(encoding="utf-8") != content):
                runner_path.write_text(content, encoding="utf-8")
                runner_path.chmod(0o755)
        except Exception as e:
            # If we can't create the runner for some reason, let the caller fall back.
            self.logger.warning(f"Failed to create runner script {runner_path}: {e}")
            return None

        return runner_path

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
        log_dir = Path.home() / ".upkeep" / "logs"
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

        # Register with launchctl (user LaunchAgent)
        try:
            uid = os.getuid()

            # Hygiene: make registration idempotent.
            # If a job with this label already exists, boot it out first (best effort).
            # This avoids accumulating stale launchd state during rapid create/update cycles.
            try:
                subprocess.run(
                    ["launchctl", "bootout", f"gui/{uid}", str(plist_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
            except Exception:
                pass

            # Preferred modern API (Ventura+)
            result = subprocess.run(
                ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            # Fallback for older systems
            if result.returncode != 0:
                result = subprocess.run(
                    ["launchctl", "load", str(plist_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
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

        # Unregister with launchctl
        try:
            uid = os.getuid()
            # Preferred modern API
            result = subprocess.run(
                ["launchctl", "bootout", f"gui/{uid}", str(plist_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            # Fallback
            if result.returncode != 0:
                result = subprocess.run(
                    ["launchctl", "unload", str(plist_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
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
        return self.plist_dir / f"com.upkeep.schedule.{schedule_id}.plist"

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
        for plist_path in self.plist_dir.glob("com.upkeep.schedule.*.plist"):
            # Extract schedule ID from filename
            filename = plist_path.stem  # com.upkeep.schedule.schedule-abc123
            parts = filename.split(".")
            if len(parts) >= 4:
                schedule_id = parts[3]  # schedule-abc123
                schedule_ids.append(schedule_id)

        return schedule_ids


async def run_scheduled_task_async(schedule_id: str, *, lock_wait_seconds: int = 30 * 60) -> bool:
    """Entry point for scheduled task execution.

    This function is called by launchd at scheduled times.

    Guarantees:
    - Non-overlap by default (global file lock). If another batch is running, we skip.
    - Logs everything to per-schedule log paths in the LaunchAgent plist.
    - Optional user notification for success/failure.

    Args:
        schedule_id: Schedule ID to execute

    Returns:
        True if execution successful (or skipped due to overlap), False otherwise
    """
    logger = logging.getLogger("core.run_scheduled_task")
    logger.info(f"Running scheduled task: {schedule_id}")

    try:
        # Load schedule from API
        from upkeep.api.schedule import ScheduleAPI

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

        # Prevent overlap: acquire a global lock.
        # This protects against two schedules firing near-simultaneously.
        import fcntl
        import time as _time
        from contextlib import contextmanager

        locks_dir = Path.home() / ".upkeep" / "locks"
        locks_dir.mkdir(parents=True, exist_ok=True)
        lock_path = locks_dir / "scheduler.lock"

        @contextmanager
        def _acquire_lock(wait_seconds: int):
            """Acquire the global scheduler lock.

            Best practice: queue (wait) rather than skip to avoid missed maintenance.
            We still enforce an upper bound to prevent hanging forever.
            """
            fh = open(lock_path, "w")
            acquired = False
            try:
                deadline = _time.time() + max(0, int(wait_seconds))
                # Poll with a short sleep so we can log waiting and honor a timeout.
                while True:
                    try:
                        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                        yield True
                        break
                    except BlockingIOError:
                        if _time.time() >= deadline:
                            yield False
                            break
                        _time.sleep(1)
            finally:
                if acquired:
                    try:
                        fcntl.flock(fh, fcntl.LOCK_UN)
                    except Exception:
                        pass
                fh.close()

        def _notify(title: str, message: str) -> None:
            # Best-effort macOS notification; safe no-op if osascript fails.
            try:
                import subprocess

                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{message.replace("\"", "\\\"")}" with title "{title.replace("\"", "\\\"")}"',
                    ],
                    check=False,
                    timeout=5,
                )
            except Exception:
                pass

        start_ts = _time.time()
        successful = 0
        failed = 0
        total = len(schedule.operations)

        logger.info(f"Waiting for scheduler lock (up to {lock_wait_seconds}s)...")

        with _acquire_lock(lock_wait_seconds) as have_lock:
            if not have_lock:
                msg = (
                    f"Skipped {schedule.name}: another maintenance batch is already running "
                    f"(lock wait timeout after {lock_wait_seconds}s)"
                )
                logger.warning(msg)
                # Don't update last_run on a skip.
                if getattr(schedule, "notify", True):
                    _notify("Mac Maintenance (Skipped)", msg)
                return True

            logger.info(f"Executing operations for schedule: {schedule.name}")

            # Execute operations via the daemon-backed batch runner (records history + durations)
            from upkeep.api.maintenance import MaintenanceAPI

            maintenance_api = MaintenanceAPI()

            async def _run_batch() -> None:
                nonlocal successful, failed, total
                async for event in maintenance_api.run_operations(schedule.operations):
                    # Mirror key events to the scheduler log
                    if event.get("type") == "operation_start":
                        logger.info(f"[{event.get('progress')}] Starting: {event.get('operation_name')}")
                    elif event.get("type") == "output":
                        # Keep logs readable; output already cleaned by API
                        line = event.get("line", "")
                        if line:
                            logger.info(line)
                    elif event.get("type") == "operation_complete":
                        status = "SUCCESS" if event.get("success") else "FAILED"
                        logger.info(f"Completed {event.get('operation_id')}: {status} (code {event.get('returncode')})")
                    elif event.get("type") == "summary":
                        total = int(event.get("total") or total)
                        successful = int(event.get("successful") or 0)
                        failed = int(event.get("failed") or 0)
                        logger.info(
                            f"Summary: total={total} success={successful} failed={failed}"
                        )

            await _run_batch()

        duration_s = int(max(0, _time.time() - start_ts))

        # Update last_run timestamp
        schedule_api.update_schedule(schedule_id, {"last_run": datetime.now()})

        if getattr(schedule, "notify", True):
            if failed > 0:
                _notify(
                    "Mac Maintenance (Failed)",
                    f"{schedule.name}: {successful}/{total} ok, {failed} failed in {duration_s}s",
                )
            else:
                _notify(
                    "Mac Maintenance (Success)",
                    f"{schedule.name}: {successful}/{total} ok in {duration_s}s",
                )

        logger.info(f"Scheduled task completed: {schedule_id}")
        return failed == 0

    except Exception as e:
        logger.error(f"Error running scheduled task: {e}", exc_info=True)
        return False


def run_scheduled_task(schedule_id: str) -> bool:
    """Synchronous wrapper.

    - Used by launchd / CLI entrypoints (no running event loop)
    - Safe to call from non-async contexts.

    For FastAPI endpoints (already in an event loop), call `await run_scheduled_task_async(...)`.
    """
    return asyncio.run(run_scheduled_task_async(schedule_id))


if __name__ == "__main__":
    # Entry point when called from launchd
    import sys

    if len(sys.argv) < 2:
        print("Usage: run_schedule.py <schedule_id>")
        sys.exit(1)

    schedule_id = sys.argv[1]
    success = run_scheduled_task(schedule_id)
    sys.exit(0 if success else 1)
