"""Schedule API for recurring maintenance tasks.

API-First Design: Clean interface for schedule management.
Used by Web GUI, CLI, and TUI.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, time as time_type, timedelta

from .base import BaseAPI
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


class ScheduleAPI(BaseAPI):
    """API for schedule management operations.

    Provides:
    - CRUD operations for schedules
    - Next run calculation
    - Conflict detection
    - JSON persistence

    Design Pattern: Repository pattern with in-memory + file storage
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize ScheduleAPI.

        Args:
            storage_path: Path to schedules.json file (default: ~/.mac-maintenance/schedules.json)
        """
        super().__init__()

        # Set storage path
        if storage_path is None:
            storage_path = Path.home() / ".mac-maintenance" / "schedules.json"

        self.storage_path = Path(storage_path)

        # Ensure parent directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize storage file if it doesn't exist
        if not self.storage_path.exists():
            self.storage_path.write_text("[]")

        self.logger.info(f"ScheduleAPI initialized with storage: {self.storage_path}")

    def _load_schedules(self) -> List[ScheduleConfig]:
        """Load all schedules from JSON storage.

        Returns:
            List of ScheduleConfig objects
        """
        try:
            data = json.loads(self.storage_path.read_text())
            schedules = []

            for item in data:
                # Convert time string back to time object
                if isinstance(item.get('time_of_day'), str):
                    time_parts = item['time_of_day'].split(':')
                    item['time_of_day'] = time_type(
                        int(time_parts[0]),
                        int(time_parts[1]),
                        int(time_parts[2]) if len(time_parts) > 2 else 0
                    )

                # Convert datetime strings back to datetime objects
                for field in ['created_at', 'updated_at', 'last_run', 'next_run']:
                    if item.get(field) and isinstance(item[field], str):
                        item[field] = datetime.fromisoformat(item[field])

                schedules.append(ScheduleConfig(**item))

            return schedules
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse schedules.json: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load schedules: {e}")
            return []

    def _save_schedules(self, schedules: List[ScheduleConfig]) -> None:
        """Save all schedules to JSON storage.

        Args:
            schedules: List of ScheduleConfig objects to save
        """
        try:
            # Convert to dict for JSON serialization
            data = []
            for schedule in schedules:
                schedule_dict = schedule.model_dump()

                # Convert time object to string
                if isinstance(schedule_dict.get('time_of_day'), time_type):
                    schedule_dict['time_of_day'] = schedule_dict['time_of_day'].strftime('%H:%M:%S')

                # Convert datetime objects to ISO format strings
                for field in ['created_at', 'updated_at', 'last_run', 'next_run']:
                    if schedule_dict.get(field) and isinstance(schedule_dict[field], datetime):
                        schedule_dict[field] = schedule_dict[field].isoformat()

                data.append(schedule_dict)

            # Write to file with pretty formatting
            self.storage_path.write_text(json.dumps(data, indent=2))
            self.logger.debug(f"Saved {len(schedules)} schedules to {self.storage_path}")

        except Exception as e:
            self.logger.error(f"Failed to save schedules: {e}")
            raise

    def create_schedule(self, schedule_data: Dict[str, Any]) -> ScheduleResponse:
        """Create a new schedule.

        Args:
            schedule_data: Dictionary with schedule configuration

        Returns:
            ScheduleResponse with created schedule

        Raises:
            ValidationError: If schedule data is invalid
        """
        self._log_call("create_schedule", schedule_data=schedule_data)

        try:
            # Convert time string to time object if needed
            if 'time_of_day' in schedule_data and isinstance(schedule_data['time_of_day'], str):
                time_parts = schedule_data['time_of_day'].split(':')
                schedule_data['time_of_day'] = time_type(
                    int(time_parts[0]),
                    int(time_parts[1]),
                    int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            # Create ScheduleConfig (validates automatically via Pydantic)
            schedule = ScheduleConfig(**schedule_data)

            # Generate ID and set timestamps
            schedule.generate_id()
            schedule.set_timestamps(is_new=True)

            # Calculate next run
            schedule.next_run = self.calculate_next_run(schedule)

            # Load existing schedules
            schedules = self._load_schedules()

            # Check for conflicts
            conflict_message = self._check_conflicts(schedule, schedules)

            # Add to schedules list
            schedules.append(schedule)

            # Save to storage
            self._save_schedules(schedules)

            return ScheduleResponse(
                success=True,
                schedule=schedule,
                error=None,
                message=conflict_message
            )

        except ValidationError as e:
            return ScheduleResponse(
                success=False,
                schedule=None,
                error=str(e),
                message=None
            )
        except Exception as e:
            self.logger.error(f"Failed to create schedule: {e}")
            return ScheduleResponse(
                success=False,
                schedule=None,
                error=str(e),
                message=None
            )

    def get_schedule(self, schedule_id: str) -> ScheduleResponse:
        """Get a schedule by ID.

        Args:
            schedule_id: Unique schedule identifier

        Returns:
            ScheduleResponse with schedule data
        """
        self._log_call("get_schedule", schedule_id=schedule_id)

        schedules = self._load_schedules()

        for schedule in schedules:
            if schedule.id == schedule_id:
                return ScheduleResponse(
                    success=True,
                    schedule=schedule,
                    error=None,
                    message=None
                )

        return ScheduleResponse(
            success=False,
            schedule=None,
            error=f"Schedule not found: {schedule_id}",
            message=None
        )

    def list_schedules(self) -> ScheduleListResponse:
        """List all schedules.

        Returns:
            ScheduleListResponse with all schedules
        """
        self._log_call("list_schedules")

        try:
            schedules = self._load_schedules()

            return ScheduleListResponse(
                success=True,
                schedules=schedules,
                count=len(schedules),
                error=None
            )

        except Exception as e:
            self.logger.error(f"Failed to list schedules: {e}")
            return ScheduleListResponse(
                success=False,
                schedules=[],
                count=0,
                error=str(e)
            )

    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> ScheduleResponse:
        """Update an existing schedule.

        Args:
            schedule_id: Schedule ID to update
            updates: Dictionary with fields to update

        Returns:
            ScheduleResponse with updated schedule
        """
        self._log_call("update_schedule", schedule_id=schedule_id, updates=updates)

        try:
            schedules = self._load_schedules()

            # Find schedule
            schedule_index = None
            for i, schedule in enumerate(schedules):
                if schedule.id == schedule_id:
                    schedule_index = i
                    break

            if schedule_index is None:
                return ScheduleResponse(
                    success=False,
                    schedule=None,
                    error=f"Schedule not found: {schedule_id}",
                    message=None
                )

            # Get existing schedule
            schedule = schedules[schedule_index]

            # Convert time string if present
            if 'time_of_day' in updates and isinstance(updates['time_of_day'], str):
                time_parts = updates['time_of_day'].split(':')
                updates['time_of_day'] = time_type(
                    int(time_parts[0]),
                    int(time_parts[1]),
                    int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            # Convert datetime string if present
            if 'last_run' in updates and isinstance(updates['last_run'], datetime):
                # Already a datetime object, keep as-is
                pass

            # Apply updates
            schedule_dict = schedule.model_dump()
            schedule_dict.update(updates)

            # Create updated schedule (validates)
            updated_schedule = ScheduleConfig(**schedule_dict)

            # Update timestamps
            updated_schedule.set_timestamps(is_new=False)

            # Recalculate next run if schedule changed
            if any(key in updates for key in ['frequency', 'time_of_day', 'days_of_week', 'day_of_month']):
                updated_schedule.next_run = self.calculate_next_run(updated_schedule)

            # Replace in list
            schedules[schedule_index] = updated_schedule

            # Save
            self._save_schedules(schedules)

            return ScheduleResponse(
                success=True,
                schedule=updated_schedule,
                error=None,
                message=None
            )

        except ValidationError as e:
            return ScheduleResponse(
                success=False,
                schedule=None,
                error=str(e),
                message=None
            )
        except Exception as e:
            self.logger.error(f"Failed to update schedule: {e}")
            return ScheduleResponse(
                success=False,
                schedule=None,
                error=str(e),
                message=None
            )

    def delete_schedule(self, schedule_id: str) -> ScheduleResponse:
        """Delete a schedule.

        Args:
            schedule_id: Schedule ID to delete

        Returns:
            ScheduleResponse indicating success
        """
        self._log_call("delete_schedule", schedule_id=schedule_id)

        try:
            schedules = self._load_schedules()

            # Find and remove schedule
            original_count = len(schedules)
            schedules = [s for s in schedules if s.id != schedule_id]

            if len(schedules) == original_count:
                return ScheduleResponse(
                    success=False,
                    schedule=None,
                    error=f"Schedule not found: {schedule_id}",
                    message=None
                )

            # Save
            self._save_schedules(schedules)

            return ScheduleResponse(
                success=True,
                schedule=None,
                error=None,
                message=f"Schedule {schedule_id} deleted"
            )

        except Exception as e:
            self.logger.error(f"Failed to delete schedule: {e}")
            return ScheduleResponse(
                success=False,
                schedule=None,
                error=str(e),
                message=None
            )

    def calculate_next_run(self, schedule: ScheduleConfig) -> datetime:
        """Calculate the next run time for a schedule.

        Args:
            schedule: ScheduleConfig to calculate for

        Returns:
            datetime of next scheduled run
        """
        now = datetime.now()
        today = now.date()

        # Combine date and time
        scheduled_time = datetime.combine(today, schedule.time_of_day)

        if schedule.frequency == ScheduleFrequency.DAILY:
            # If time today has passed, schedule for tomorrow
            if scheduled_time <= now:
                return scheduled_time + timedelta(days=1)
            return scheduled_time

        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            # Find next occurrence of any scheduled day
            if not schedule.days_of_week:
                raise ValidationError("Weekly schedule requires days_of_week")

            # Convert DayOfWeek to weekday numbers (0=Monday, 6=Sunday)
            day_map = {
                DayOfWeek.MONDAY: 0,
                DayOfWeek.TUESDAY: 1,
                DayOfWeek.WEDNESDAY: 2,
                DayOfWeek.THURSDAY: 3,
                DayOfWeek.FRIDAY: 4,
                DayOfWeek.SATURDAY: 5,
                DayOfWeek.SUNDAY: 6,
            }

            scheduled_weekdays = sorted([day_map[day] for day in schedule.days_of_week])
            current_weekday = today.weekday()

            # Find next scheduled day
            for day in scheduled_weekdays:
                if day > current_weekday:
                    days_until = day - current_weekday
                    next_date = today + timedelta(days=days_until)
                    return datetime.combine(next_date, schedule.time_of_day)
                elif day == current_weekday and scheduled_time > now:
                    return scheduled_time

            # No day found this week, take first day next week
            days_until = 7 - current_weekday + scheduled_weekdays[0]
            next_date = today + timedelta(days=days_until)
            return datetime.combine(next_date, schedule.time_of_day)

        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            # Schedule for specific day of month
            if schedule.day_of_month is None:
                raise ValidationError("Monthly schedule requires day_of_month")

            # Try this month first
            try:
                next_date = today.replace(day=schedule.day_of_month)
                next_run = datetime.combine(next_date, schedule.time_of_day)
                if next_run > now:
                    return next_run
            except ValueError:
                pass  # Day doesn't exist in this month

            # Try next month
            next_month = today.month + 1
            next_year = today.year
            if next_month > 12:
                next_month = 1
                next_year += 1

            try:
                next_date = today.replace(year=next_year, month=next_month, day=schedule.day_of_month)
                return datetime.combine(next_date, schedule.time_of_day)
            except ValueError:
                # Day doesn't exist in next month either, try month after
                next_month += 1
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_date = today.replace(year=next_year, month=next_month, day=schedule.day_of_month)
                return datetime.combine(next_date, schedule.time_of_day)

        else:
            # Custom frequency not implemented yet
            raise ValidationError(f"Frequency {schedule.frequency} not supported yet")

    def _check_conflicts(self, schedule: ScheduleConfig, existing_schedules: List[ScheduleConfig]) -> Optional[str]:
        """Check if schedule conflicts with existing schedules.

        Args:
            schedule: New schedule to check
            existing_schedules: List of existing schedules

        Returns:
            Warning message if conflict detected, None otherwise
        """
        conflicts = []

        for existing in existing_schedules:
            # Skip disabled schedules
            if not existing.enabled:
                continue

            # Check if same time
            if existing.time_of_day == schedule.time_of_day:
                # Check if same frequency overlaps
                if existing.frequency == schedule.frequency:
                    if schedule.frequency == ScheduleFrequency.DAILY:
                        conflicts.append(existing.name)
                    elif schedule.frequency == ScheduleFrequency.WEEKLY:
                        # Check if any days overlap
                        if schedule.days_of_week and existing.days_of_week:
                            overlap = set(schedule.days_of_week) & set(existing.days_of_week)
                            if overlap:
                                conflicts.append(existing.name)
                    elif schedule.frequency == ScheduleFrequency.MONTHLY:
                        if schedule.day_of_month == existing.day_of_month:
                            conflicts.append(existing.name)

        if conflicts:
            return f"Warning: Schedule conflicts with existing schedules at same time: {', '.join(conflicts)}"

        return None

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get list of all schedule conflicts.

        Returns:
            List of conflict information
        """
        self._log_call("get_conflicts")

        schedules = self._load_schedules()
        conflicts = []

        # Check each pair of schedules
        for i, schedule1 in enumerate(schedules):
            if not schedule1.enabled:
                continue

            for schedule2 in schedules[i+1:]:
                if not schedule2.enabled:
                    continue

                # Check if they conflict
                if schedule1.time_of_day == schedule2.time_of_day:
                    conflict_detected = False

                    if schedule1.frequency == schedule2.frequency == ScheduleFrequency.DAILY:
                        conflict_detected = True
                    elif schedule1.frequency == schedule2.frequency == ScheduleFrequency.WEEKLY:
                        if schedule1.days_of_week and schedule2.days_of_week:
                            overlap = set(schedule1.days_of_week) & set(schedule2.days_of_week)
                            if overlap:
                                conflict_detected = True
                    elif schedule1.frequency == schedule2.frequency == ScheduleFrequency.MONTHLY:
                        if schedule1.day_of_month == schedule2.day_of_month:
                            conflict_detected = True

                    if conflict_detected:
                        conflicts.append({
                            'schedule_ids': [schedule1.id, schedule2.id],
                            'schedules': [schedule1.name, schedule2.name],
                            'time_of_day': schedule1.time_of_day.strftime('%H:%M:%S')
                        })

        return conflicts
