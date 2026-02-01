#!/usr/bin/env python3
"""Scheduler entry point script.

This script is called by launchd at scheduled times to execute
maintenance operations.

Usage:
    python3 run_schedule.py <schedule_id>
"""

import sys
import logging
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".mac-maintenance" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("Usage: run_schedule.py <schedule_id>")
        print("Usage: run_schedule.py <schedule_id>", file=sys.stderr)
        sys.exit(1)

    schedule_id = sys.argv[1]
    logger.info(f"Scheduler entry point called for: {schedule_id}")

    try:
        # Import and run scheduled task
        from mac_maintenance.core.launchd import run_scheduled_task

        success = run_scheduled_task(schedule_id)

        if success:
            logger.info(f"Schedule {schedule_id} executed successfully")
            sys.exit(0)
        else:
            logger.error(f"Schedule {schedule_id} execution failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error executing schedule {schedule_id}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
