#!/usr/bin/env python3
"""
Mac Maintenance Daemon

Root-privileged worker that executes maintenance operations.
Runs as launchd daemon, polls job queue directory for work.

Security:
- Only accepts whitelisted operations (no arbitrary commands)
- Runs as root via launchd (proper OS authorization)
- Communicates via job queue directory (no network exposure)
- Never handles passwords
"""

import json
import os
import sys
import time
import subprocess
import pwd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configuration
QUEUE_DIR = Path("/var/local/upkeep-jobs")
MAINTAIN_SH = Path("/usr/local/lib/upkeep/upkeep.sh")
POLL_INTERVAL = 2  # seconds
LOG_FILE = Path("/var/log/upkeep-daemon.log")
STATUS_FILE = QUEUE_DIR / "daemon-status.json"  # Current operation status (for skip button)
SKIP_FLAG_FILE = QUEUE_DIR / "skip.flag"  # Skip current operation flag

# Whitelist of allowed operations
# Each operation maps to: [arguments, timeout_in_seconds]
# Timeouts based on expected duration (Task #132 fix):
# - Quick operations: 300s (5 min)
# - Homebrew: 900s (15 min) - can download large packages
# - mas: 1200s (20 min) - App Store downloads can be slow (WhatsApp, etc.)
# - macOS updates: 1800s (30 min) - system updates take time
ALLOWED_OPERATIONS = {
    "macos-check": (["--list-macos-updates"], 300),
    "macos-install": (["--install-macos-updates", "--assume-yes"], 1800),
    "brew-update": (["--brew", "--assume-yes"], 900),
    "brew-cleanup": (["--brew-cleanup", "--assume-yes"], 600),
    "mas-update": (["--mas", "--assume-yes"], 1200),
    "disk-verify": (["--verify-disk"], 300),
    "disk-repair": (["--repair-disk", "--assume-yes"], 600),
    "smart-check": (["--smart"], 300),
    "trim-logs": (["--trim-logs", "30", "--assume-yes"], 300),
    "trim-caches": (["--trim-caches", "30", "--assume-yes"], 300),
    "thin-tm": (["--thin-tm-snapshots", "--assume-yes"], 300),
    "spotlight-status": (["--spotlight-status"], 300),
    "spotlight-reindex": (["--spotlight-reindex", "--assume-yes"], 300),
    "dns-flush": (["--flush-dns", "--assume-yes"], 300),
    "periodic": (["--periodic", "--assume-yes"], 300),
    "space-report": (["--space-report"], 300),
    # User-specific operations (require user context)
    "browser-cache": (["--browser-cache", "--assume-yes"], 300),
    "dev-cache": (["--dev-cache", "--assume-yes"], 300),
    "dev-tools-cache": (["--dev-tools-cache", "--assume-yes"], 300),
    "mail-optimize": (["--mail-optimize", "--assume-yes"], 300),
    "messages-cache": (["--messages-cache", "--assume-yes"], 300),
    "wallpaper-aerials": (["--wallpaper-aerials", "--assume-yes"], 600),
}


def log(message: str, level: str = "INFO") -> None:
    """Write to daemon log file."""
    timestamp = datetime.now().isoformat()
    log_message = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_message)
    except Exception:
        print(log_message, file=sys.stderr)


def get_console_user() -> Tuple[Optional[str], Optional[str]]:
    """
    Detect the user currently logged into the Mac console.

    Returns:
        Tuple of (username, home_directory) or (None, None) if can't detect.

    Business logic:
    1. Try to get console user via 'who' command
    2. Get user's home directory from system database
    3. Fall back to first non-system user in /Users if 'who' fails
    """
    try:
        # Method 1: Get console user via 'who' command
        result = subprocess.run(
            ["who"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse output: "username console ..."
            for line in result.stdout.strip().split('\n'):
                if 'console' in line:
                    username = line.split()[0]

                    # Get user's home directory from passwd database
                    try:
                        pw_record = pwd.getpwnam(username)
                        home = pw_record.pw_dir
                        log(f"Detected console user: {username} ({home})")
                        return (username, home)
                    except KeyError:
                        log(f"Warning: Found console user {username} but no passwd entry", "WARN")
                        continue

        # Method 2: Fall back to first user in /Users (common for single-user Macs)
        users_dir = Path("/Users")
        if users_dir.exists():
            for user_dir in sorted(users_dir.iterdir()):
                if user_dir.is_dir() and user_dir.name not in ["Shared", ".localized", "Guest"]:
                    username = user_dir.name
                    home = str(user_dir)

                    # Verify this is a real user account
                    try:
                        pwd.getpwnam(username)
                        log(f"Detected primary user (fallback): {username} ({home})")
                        return (username, home)
                    except KeyError:
                        continue

        log("Warning: Could not detect console user", "WARN")
        return (None, None)

    except Exception as e:
        log(f"Exception in get_console_user: {e}", "ERROR")
        return (None, None)


def cleanup_mas_zombies() -> None:
    """
    Kill zombie mas processes before starting mas operations (Task #132).

    Business Logic:
    - mas processes can hang indefinitely, accumulating over time
    - Old mas processes from previous sessions block new operations
    - Must kill zombies before starting new mas operation

    Safety:
    - Only kills 'mas' processes (not other apps)
    - Best effort - doesn't fail if no zombies found
    - Logs all kill attempts for debugging
    """
    try:
        # Find all mas processes
        result = subprocess.run(
            ["pgrep", "-f", "mas"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            log(f"Found {len(pids)} mas zombie process(es), killing: {', '.join(pids)}", "WARN")

            # Kill each process
            for pid in pids:
                try:
                    subprocess.run(["kill", "-9", pid], timeout=2, capture_output=True)
                except Exception as e:
                    log(f"Failed to kill mas process {pid}: {e}", "WARN")

            # Wait for processes to die
            time.sleep(1)
            log("Zombie mas processes cleaned up")
        else:
            log("No zombie mas processes found")

    except subprocess.TimeoutExpired:
        log("Timeout while checking for mas zombies", "WARN")
    except Exception as e:
        log(f"Error cleaning up mas zombies: {e}", "WARN")


def run_operation(operation_id: str, job_id: str = "") -> Dict[str, Any]:
    """
    Execute a whitelisted maintenance operation.

    Args:
        operation_id: ID of the operation to run
        job_id: Job ID for status tracking (optional)

    Returns:
        Result dictionary with status, output, exit code
    """
    result: Dict[str, Any] = {
        "operation_id": operation_id,
        "status": "error",
        "timestamp": datetime.now().isoformat(),
    }

    # Validate operation is whitelisted
    if operation_id not in ALLOWED_OPERATIONS:
        result["error"] = f"Operation not allowed: {operation_id}"
        log(f"Rejected unknown operation: {operation_id}", "ERROR")
        return result

    # Check upkeep.sh exists
    if not MAINTAIN_SH.exists():
        result["error"] = f"upkeep.sh not found at {MAINTAIN_SH}"
        log(f"upkeep.sh not found: {MAINTAIN_SH}", "ERROR")
        return result

    # Extract args and timeout from operation config
    args, timeout_seconds = ALLOWED_OPERATIONS[operation_id]
    command = [str(MAINTAIN_SH)] + args

    # Task #132: Kill zombie mas processes before mas operations
    if operation_id == "mas-update":
        log("Cleaning up zombie mas processes before starting operation")
        cleanup_mas_zombies()

    # Detect console user for operations that need user context
    actual_user, actual_home = get_console_user()

    log(f"Executing: {operation_id} -> {' '.join(command)}")
    if actual_user:
        log(f"User context: {actual_user} ({actual_home})")
    else:
        log("Warning: No user context detected, using root context", "WARN")

    try:
        # Execute as root (we're already root via launchd)
        # No need for sudo - we ARE root
        # Set environment variables for upkeep.sh
        env = os.environ.copy()
        env["MAC_MAINTENANCE_DAEMON"] = "1"  # Allow root execution from daemon
        env["MAINTAIN_SH"] = str(MAINTAIN_SH)  # Path to upkeep.sh for timestamp checks

        # CRITICAL: Pass actual user context to upkeep.sh
        # This allows operations to access user's home directory
        if actual_user and actual_home:
            env["ACTUAL_USER"] = actual_user
            env["ACTUAL_HOME"] = actual_home
            # Set SUDO_USER so upkeep.sh's get_actual_user_home() can use it
            env["SUDO_USER"] = actual_user
            # Set HOME to root's home for logging (upkeep.sh needs it for LOG_DIR)
            env["HOME"] = "/var/root"
        else:
            # Fallback: use root context
            env["ACTUAL_USER"] = "root"
            env["ACTUAL_HOME"] = "/var/root"
            env["SUDO_USER"] = "root"
            env["HOME"] = "/var/root"

        # Set SUDO_ASKPASS to prevent password prompts in non-interactive daemon context
        # When Homebrew cask uninstall or other commands call sudo internally,
        # this prevents password prompts that would hang the daemon
        # Reference: https://github.com/orgs/Homebrew/discussions/3966
        env["SUDO_ASKPASS"] = "/usr/bin/false"

        # Set COLUMNS to prevent terminal width truncation (Task #105 fix)
        # In non-interactive daemon context, COLUMNS defaults to 80
        # This causes programs to truncate output at 80 characters
        # Examples: "Job enqueued:" → "Job enb-...", "diskutil repair" → "diskutiir"
        # Setting COLUMNS=999 tells programs not to truncate output
        # Business logic: Web UI has no terminal width limitation, needs full text
        env["COLUMNS"] = "999"
        env["LINES"] = "999"  # Also set LINES for completeness

        # Task #128: Use Popen with external watchdog for reliable timeout enforcement
        # subprocess.run(timeout=X) doesn't work if process hangs without returning
        # External watchdog monitors elapsed time and force-kills hung processes
        start_time = time.time()

        # 🔧 Feature Flag: ENFORCE_TIMEOUT (easy disable if issues found)
        # Default: true (prevents infinite hangs)
        enforce_timeout = os.environ.get("ENFORCE_TIMEOUT", "true").lower() == "true"

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid chars instead of crashing
            bufsize=-1,  # Use system default buffering (fully buffered)
            cwd=MAINTAIN_SH.parent,
            env=env,
        )

        # Task #133: Write status file so API can track current operation
        # This allows Skip Current button to kill the subprocess
        try:
            status_data = {
                "job_id": job_id,
                "operation_id": operation_id,
                "pid": proc.pid,
                "start_time": start_time,
                "timeout_seconds": timeout_seconds,
            }
            with open(STATUS_FILE, "w") as f:
                json.dump(status_data, f, indent=2)
            os.chmod(STATUS_FILE, 0o644)  # Readable by web backend
            log(f"Wrote status file (PID: {proc.pid})")
        except Exception as e:
            log(f"Failed to write status file: {e}", "WARN")

        # Watchdog loop: monitor process, enforce timeout, check for skip flag
        skip_requested = False
        while proc.poll() is None:
            elapsed = time.time() - start_time

            # Task #133: Check for skip flag
            if SKIP_FLAG_FILE.exists():
                skip_requested = True
                log(f"SKIP: User requested skip for {operation_id}, killing process", "WARN")

                try:
                    # Delete skip flag
                    SKIP_FLAG_FILE.unlink()

                    # Kill subprocess
                    proc.terminate()
                    time.sleep(2)

                    if proc.poll() is None:
                        proc.kill()
                        log(f"Force killed skipped process (PID: {proc.pid})", "WARN")

                    # Kill child processes
                    try:
                        subprocess.run(
                            ["pkill", "-P", str(proc.pid)],
                            timeout=5,
                            capture_output=True
                        )
                    except:
                        pass

                except Exception as e:
                    log(f"Error killing skipped process: {e}", "ERROR")

                result["status"] = "skipped"
                result["error"] = "Operation skipped by user"
                result["exit_code"] = -125  # Custom skip exit code
                result["stdout"] = ""
                result["stderr"] = "Operation skipped by user request"
                break

            # Check for timeout
            if enforce_timeout and elapsed > timeout_seconds:
                # Process exceeded timeout - force kill
                log(f"TIMEOUT: {operation_id} exceeded {timeout_seconds/60:.1f} minutes, killing process", "ERROR")

                try:
                    # Try graceful termination first (SIGTERM)
                    proc.terminate()
                    time.sleep(2)

                    # If still running, force kill (SIGKILL)
                    if proc.poll() is None:
                        proc.kill()
                        log(f"Force killed hung process (PID: {proc.pid})", "WARN")

                    # Also kill any child processes (prevent zombies)
                    try:
                        subprocess.run(
                            ["pkill", "-P", str(proc.pid)],
                            timeout=5,
                            capture_output=True
                        )
                    except:
                        pass  # Best effort, don't fail if pkill doesn't work

                except Exception as kill_error:
                    log(f"Error killing process: {kill_error}", "ERROR")

                result["error"] = f"Operation timed out ({timeout_seconds/60:.1f} minute limit)"
                result["exit_code"] = -124  # Standard timeout exit code
                result["stdout"] = ""
                result["stderr"] = f"Operation exceeded {timeout_seconds/60:.1f} minute timeout and was terminated"
                break

            # Check every 1 second
            time.sleep(1)

        # Process completed - get results (unless skipped/timeout)
        if not skip_requested and result.get("exit_code") != -124:
            stdout, stderr = proc.communicate()

            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["exit_code"] = proc.returncode
            result["stdout"] = stdout or ""
            result["stderr"] = stderr or ""

        elapsed_time = time.time() - start_time
        log(f"Completed: {operation_id} (exit={result.get('exit_code', 'unknown')}, time={elapsed_time:.1f}s)")

        # Task #133: Clean up status file
        try:
            if STATUS_FILE.exists():
                STATUS_FILE.unlink()
        except Exception as e:
            log(f"Failed to delete status file: {e}", "WARN")

    except Exception as e:
        result["error"] = str(e)
        result["exit_code"] = -1
        log(f"Exception: {operation_id} - {e}", "ERROR")

    return result


def process_job_file(job_file: Path) -> None:
    """
    Process a single job file.

    Reads job JSON, executes operation, writes result, deletes job.
    """
    # Extract job_id from filename (remove .job.json extension)
    # Example: "uuid.job.json" -> "uuid"
    job_id = job_file.name.replace(".job.json", "")
    result_file = QUEUE_DIR / f"{job_id}.result.json"

    try:
        # Read job
        with open(job_file, "r") as f:
            job = json.load(f)

        operation_id = job.get("operation_id")
        if not operation_id:
            log(f"Job {job_id} missing operation_id", "ERROR")
            return

        log(f"Processing job: {job_id} ({operation_id})")

        # Execute operation (pass job_id for status tracking)
        result = run_operation(operation_id, job_id=job_id)
        result["job_id"] = job_id

        # Write result
        with open(result_file, "w", encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Set permissions so web backend can read
        os.chmod(result_file, 0o644)

    except json.JSONDecodeError as e:
        log(f"Invalid JSON in {job_file}: {e}", "ERROR")
    except Exception as e:
        log(f"Error processing {job_file}: {e}", "ERROR")
    finally:
        # Always delete job file
        try:
            job_file.unlink()
        except FileNotFoundError:
            pass


def setup_queue_directory() -> None:
    """Create and configure queue directory."""
    try:
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        # Permissions: rwxrwxrwx (world-writable so web backend can write jobs)
        # This is safe since it's localhost-only and daemon validates all jobs
        os.chmod(QUEUE_DIR, 0o777)
        log(f"Queue directory ready: {QUEUE_DIR}")
    except Exception as e:
        log(f"Failed to setup queue directory: {e}", "ERROR")
        sys.exit(1)


def cleanup_stale_jobs() -> None:
    """
    Clear stale job files on daemon startup (Task #126).

    Business Logic:
    - Jobs older than 5 minutes are considered stale (likely from interrupted sessions)
    - Daemon may have crashed/restarted, leaving old jobs in queue
    - Processing stale jobs causes hangs (e.g., zombie processes from previous session)
    - Better to clear and have user re-run than hang indefinitely

    Safety:
    - Only runs on daemon startup (not during normal operation)
    - Uses conservative 5-minute threshold (fresh jobs are preserved)
    - Logs which jobs are cleared (for debugging)
    - Graceful degradation (if cleanup fails, daemon still starts)
    """
    # 🔧 Feature Flag: CLEAR_STALE_JOBS (easy disable if issues found)
    # Default: true (prevents hangs from stale jobs)
    # Set to false to disable this feature
    if not os.environ.get("CLEAR_STALE_JOBS", "true").lower() == "true":
        log("Stale job cleanup disabled (CLEAR_STALE_JOBS=false)")
        return

    try:
        now = time.time()
        stale_threshold = 300  # 5 minutes in seconds
        cleared_count = 0

        # Find all .job.json files
        job_files = list(QUEUE_DIR.glob("*.job.json"))

        if not job_files:
            log("No pending jobs in queue")
            return

        # Check age of each job
        for job_file in job_files:
            try:
                # Get file modification time
                file_age = now - job_file.stat().st_mtime

                if file_age > stale_threshold:
                    # Job is stale - clear it
                    age_minutes = file_age / 60
                    log(f"Clearing stale job: {job_file.name} (age: {age_minutes:.1f} minutes)", "WARN")
                    job_file.unlink()
                    cleared_count += 1
                else:
                    # Job is fresh - keep it
                    age_seconds = int(file_age)
                    log(f"Preserving recent job: {job_file.name} (age: {age_seconds}s)")

            except Exception as e:
                # If we can't process this job file, log but continue
                log(f"Error checking job file {job_file.name}: {e}", "WARN")
                continue

        if cleared_count > 0:
            log(f"Cleared {cleared_count} stale job(s) from queue", "INFO")
        else:
            log(f"All {len(job_files)} job(s) in queue are recent (< 5 min old)")

    except Exception as e:
        # Cleanup failed, but don't crash daemon - just log and continue
        log(f"Error during stale job cleanup: {e}", "WARN")
        log("Daemon will continue with existing queue state", "WARN")


def main() -> None:
    """Main daemon loop."""
    log("=== Mac Maintenance Daemon Starting ===")
    log(f"Queue directory: {QUEUE_DIR}")
    log(f"upkeep.sh: {MAINTAIN_SH}")
    log(f"Poll interval: {POLL_INTERVAL}s")

    # Verify we're running as root
    if os.geteuid() != 0:
        log("ERROR: Daemon must run as root", "ERROR")
        sys.exit(1)

    log("Running as root ✓")

    # Setup queue directory
    setup_queue_directory()

    # Clear stale jobs from previous sessions (Task #126)
    # Prevents daemon from getting stuck on zombie jobs
    cleanup_stale_jobs()

    # Main loop
    log("Entering main loop")
    while True:
        try:
            # Process all pending job files
            job_files = sorted(QUEUE_DIR.glob("*.job.json"))

            for job_file in job_files:
                process_job_file(job_file)

            # Sleep before next poll
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log("Received interrupt signal, shutting down")
            break
        except Exception as e:
            log(f"Unexpected error in main loop: {e}", "ERROR")
            time.sleep(POLL_INTERVAL)

    log("=== Mac Maintenance Daemon Stopped ===")


if __name__ == "__main__":
    main()
