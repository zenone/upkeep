"""FastAPI server for upkeep web interface.

Provides REST API endpoints and serves static web UI.
Uses secure launchd daemon for privileged operations (no password handling).
"""

import json
import logging
import sys
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from upkeep import __version__
from upkeep.api import MaintenanceAPI, ScheduleAPI, StorageAPI
from upkeep.core import system as system_utils
from upkeep.core.launchd import LaunchdGenerator
from upkeep.web.models import (
    DeleteResponse,
    LastRunResponse,
    OperationsListResponse,
    ProcessesResponse,
    RunOperationsRequest,
    SparklineResponse,
    StorageAnalyzeResponse,
    SuccessResponse,
    SystemHealthResponse,
    SystemInfoResponse,
)

# Configure logging for API modules
# This ensures API loggers (api.MaintenanceAPI, api.StorageAPI, etc.) output to console
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
    force=True,  # Override any existing configuration
)

# System metrics history (circular buffer for last 60 data points)
system_history = {
    "cpu": deque(maxlen=60),
    "memory": deque(maxlen=60),
    "disk": deque(maxlen=60),
    "timestamps": deque(maxlen=60),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler.

    Pre-populate system history for immediate sparklines on first page load.
    """
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        current_time = time.time()

        # Pre-populate with 3 initial identical values so sparklines appear immediately
        # (sparklines require at least 2 data points to draw)
        for _ in range(3):
            system_history["cpu"].append(cpu)
            system_history["memory"].append(memory)
            system_history["disk"].append(disk)
            system_history["timestamps"].append(current_time)
    except Exception as e:
        # Don't fail startup if metrics can't be collected
        print(f"Warning: Could not initialize system history: {e}")

    yield


# Initialize FastAPI app with comprehensive OpenAPI configuration
app = FastAPI(
    lifespan=lifespan,
    title="Upkeep API",
    version=__version__,
    description="""
# Upkeep REST API

Comprehensive API for macOS system maintenance, monitoring, and automation.

## Features

- **System Monitoring**: Real-time CPU, memory, and disk metrics
- **Storage Management**: Analyze and clean up disk space
- **Maintenance Operations**: Execute system maintenance tasks
- **Scheduled Tasks**: Automate maintenance with cron-based scheduling
- **Secure**: Uses launchd daemon for privileged operations (no password handling in API)

## API-First Design

All endpoints follow RESTful principles with comprehensive request/response validation.

## Authentication

Currently localhost-only. Authentication planned for remote access.
    """,
    terms_of_service=None,
    contact={
        "name": "Upkeep Support",
        "url": "https://github.com/yourusername/upkeep",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "system",
            "description": "System information and health monitoring",
        },
        {
            "name": "storage",
            "description": "Storage analysis and file management",
        },
        {
            "name": "maintenance",
            "description": "Maintenance operations and execution",
        },
        {
            "name": "schedules",
            "description": "Scheduled maintenance task management",
        },
    ],
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative documentation
    openapi_url="/openapi.json",  # OpenAPI schema
)

# CORS - localhost only for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize APIs
storage_api = StorageAPI()
maintenance_api = MaintenanceAPI()


# Startup event - pre-populate system history for immediate sparklines
# (startup handled by lifespan)
# @app.on_event("startup")
async def startup_event():
    """Initialize system history with current metrics for immediate chart display."""
    try:
        # Get current metrics
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        current_time = time.time()

        # Pre-populate with 3 initial identical values so sparklines appear immediately
        # (sparklines require at least 2 data points to draw)
        for _ in range(3):
            system_history["cpu"].append(cpu)
            system_history["memory"].append(memory)
            system_history["disk"].append(disk)
            system_history["timestamps"].append(current_time)
    except Exception as e:
        # Don't fail startup if metrics can't be collected
        print(f"Warning: Could not initialize system history: {e}")


# Health check
@app.get("/api/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}


# System information
@app.get(
    "/api/system/info",
    tags=["system"],
    response_model=SystemInfoResponse,
    summary="Get system information",
    description="Returns real-time CPU, memory, disk usage, and system details with historical data for trend analysis.",
)
async def get_system_info() -> dict[str, Any]:
    """Get system information (CPU, memory, disk, username) with history for trends."""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Memory
        memory = psutil.virtual_memory()

        # Disk
        disk = psutil.disk_usage("/")

        # Network I/O
        net_io = psutil.net_io_counters()
        current_time = time.time()

        # Calculate network rates (bytes per second)
        if hasattr(get_system_info, "_last_net_io") and hasattr(get_system_info, "_last_time"):
            time_delta = current_time - get_system_info._last_time
            if time_delta > 0:
                bytes_sent_delta = net_io.bytes_sent - get_system_info._last_net_io.bytes_sent
                bytes_recv_delta = net_io.bytes_recv - get_system_info._last_net_io.bytes_recv
                upload_rate = bytes_sent_delta / time_delta / 1024 / 1024  # MB/s
                download_rate = bytes_recv_delta / time_delta / 1024 / 1024  # MB/s
            else:
                upload_rate = 0
                download_rate = 0
        else:
            upload_rate = 0
            download_rate = 0

        # Store for next calculation
        get_system_info._last_net_io = net_io
        get_system_info._last_time = current_time

        # Swap usage
        swap = psutil.swap_memory()

        # System info (includes username)
        sys_info = system_utils.get_system_info()

        # Store in history (for sparklines and trends)
        system_history["cpu"].append(cpu_percent)
        system_history["memory"].append(memory.percent)
        system_history["disk"].append(disk.percent)
        system_history["timestamps"].append(time.time())

        # Get last 3 values for trend calculation (or fewer if just started)
        cpu_history = list(system_history["cpu"])[-3:]
        memory_history = list(system_history["memory"])[-3:]
        disk_history = list(system_history["disk"])[-3:]

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "history": cpu_history,
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent": memory.percent,
                "history": memory_history,
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent,
                "history": disk_history,
            },
            "network": {
                "upload_mbps": round(upload_rate, 2),
                "download_mbps": round(download_rate, 2),
                "total_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
                "total_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percent": swap.percent,
            },
            "system": {
                "username": sys_info["username"],
                "hostname": sys_info["hostname"],
                "version": sys_info["version"],
                "architecture": sys_info["architecture"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system info: {e}")


# System health score
@app.get(
    "/api/system/health",
    tags=["system"],
    response_model=SystemHealthResponse,
    summary="Get system health assessment",
    description="Calculates overall system health score (0-100) based on CPU, memory, and disk usage with issue detection.",
)
async def get_system_health() -> dict[str, Any]:
    """Calculate overall system health score (0-100)."""
    try:
        # Get current metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent

        # Calculate component scores (invert percentages: lower usage = higher score)
        cpu_score = max(0, 100 - cpu_percent)
        memory_score = max(0, 100 - memory_percent)
        disk_score = max(0, 100 - disk_percent)

        # Weighted average: Memory 40%, CPU 30%, Disk 30%
        overall_score = int((cpu_score * 0.3) + (memory_score * 0.4) + (disk_score * 0.3))

        # Determine overall status based on worst component
        # Map to expected values: "good", "warning", "critical"
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            overall = "critical"
        elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
            overall = "warning"
        else:
            overall = "good"

        # Identify issues (must be strings, not dicts)
        issues = []
        if cpu_percent > 80:
            severity = "Critical" if cpu_percent >= 90 else "Warning"
            issues.append(f"{severity}: CPU usage high ({cpu_percent:.1f}%)")
        if memory_percent > 80:
            severity = "Critical" if memory_percent >= 90 else "Warning"
            issues.append(f"{severity}: Memory usage high ({memory_percent:.1f}%)")
        if disk_percent > 80:
            severity = "Critical" if disk_percent >= 90 else "Warning"
            issues.append(f"{severity}: Disk usage high ({disk_percent:.1f}%)")

        return {
            "overall": overall,
            "score": overall_score,
            "issues": issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating health: {e}")


# Top resource consumers
@app.get(
    "/api/system/processes",
    tags=["system"],
    response_model=ProcessesResponse,
    summary="Get top resource consumers",
    description="Returns top CPU and memory consuming processes for resource monitoring.",
)
async def get_top_processes(limit: int = 3) -> dict[str, Any]:
    """Get top CPU and memory consuming processes."""
    try:
        processes = []

        # Iterate through all processes
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                pinfo = proc.info
                processes.append(
                    {
                        "pid": pinfo["pid"],
                        "name": pinfo["name"],
                        "cpu_percent": pinfo["cpu_percent"] or 0.0,
                        "memory_mb": (pinfo["memory_info"].rss / (1024 * 1024))
                        if pinfo["memory_info"]
                        else 0.0,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU and get top N
        top_cpu = sorted(processes, key=lambda x: x["cpu_percent"], reverse=True)[:limit]

        # Sort by memory and get top N
        top_memory = sorted(processes, key=lambda x: x["memory_mb"], reverse=True)[:limit]

        # Return with ALL fields required by ProcessInfo model
        return {
            "top_cpu": [
                {
                    "name": p["name"],
                    "cpu_percent": round(p["cpu_percent"], 1),
                    "memory_mb": round(p["memory_mb"], 1),
                }
                for p in top_cpu
            ],
            "top_memory": [
                {
                    "name": p["name"],
                    "cpu_percent": round(p["cpu_percent"], 1),
                    "memory_mb": round(p["memory_mb"], 1),
                }
                for p in top_memory
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting processes: {e}")


# Sparkline data (full history)
@app.get(
    "/api/system/sparkline",
    tags=["system"],
    response_model=SparklineResponse,
    summary="Get historical metrics for charts",
    description="Returns historical CPU, memory, and disk usage data for sparkline chart visualization.",
)
async def get_sparkline_data() -> dict[str, Any]:
    """Get full historical data for sparkline charts (last 60 data points)."""
    try:
        return {
            "cpu": list(system_history["cpu"]),
            "memory": list(system_history["memory"]),
            "disk": list(system_history["disk"]),
            "timestamps": list(system_history["timestamps"]),
            "count": len(system_history["cpu"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sparkline data: {e}")


# Reload scripts (copy maintain.sh to system location)
@app.post(
    "/api/system/reload-scripts",
    tags=["system"],
    response_model=SuccessResponse,
    summary="Reload maintenance scripts",
    description="Copies the updated maintain.sh script from source to the system location used by the daemon.",
)
async def reload_scripts() -> dict[str, Any]:
    """Copy maintain.sh from source to /usr/local/lib/upkeep/."""
    import shutil
    import subprocess

    try:
        # Source and destination paths
        source_path = Path(__file__).parent.parent.parent.parent / "maintain.sh"
        dest_path = Path("/usr/local/lib/upkeep/maintain.sh")

        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Source script not found at {source_path}")

        # Check if destination directory exists
        if not dest_path.parent.exists():
            raise HTTPException(
                status_code=404, detail=f"Destination directory not found: {dest_path.parent}"
            )

        # Copy file without sudo - will work if user has write permissions
        # If this fails, user needs to add sudoers rule or run with appropriate permissions
        try:
            shutil.copy2(str(source_path), str(dest_path))
        except PermissionError:
            # Fall back to sudo if needed
            result = subprocess.run(
                ["sudo", "-n", "cp", str(source_path), str(dest_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Add sudoers rule: 'sudo tee /etc/sudoers.d/upkeep-reload <<< \"$(whoami) ALL=(ALL) NOPASSWD: /bin/cp {source_path} {dest_path}\"'",
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to copy: {e}")

        # Verify succeeded
        result = type("obj", (object,), {"returncode": 0, "stderr": ""})()

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to copy script: {result.stderr}")

        # Verify the copy succeeded
        if not dest_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Script copy appeared to succeed but destination file not found",
            )

        return {
            "success": True,
            "message": "Scripts reloaded successfully. Changes will take effect on next operation.",
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Script reload timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading scripts: {e}")


# Storage analysis
@app.get(
    "/api/storage/analyze",
    tags=["storage"],
    response_model=StorageAnalyzeResponse,
    summary="Analyze storage usage",
    description="Analyzes disk usage for a given path and returns largest files/directories (up to 50 entries).",
)
async def analyze_storage(path: str = str(Path.home())) -> dict[str, Any]:
    """Analyze storage usage for a given path."""
    try:
        result = storage_api.analyze_path(path, max_depth=3, max_entries=20)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing storage: {e}")


# Delete file/directory
@app.delete(
    "/api/storage/delete",
    tags=["storage"],
    response_model=DeleteResponse,
    summary="Delete file or directory",
    description="Deletes a file or directory either by moving to Trash (recoverable) or permanently (cannot be undone).",
)
async def delete_path(path: str, mode: str = "trash") -> dict[str, Any]:
    """Delete or move to trash a file or directory.

    Args:
        path: Path to delete
        mode: 'trash' (default, recoverable) or 'permanent' (cannot be undone)

    Returns:
        Dict with success, error, and mode used
    """
    try:
        # Validate mode parameter
        if mode not in ["trash", "permanent"]:
            raise HTTPException(
                status_code=400, detail=f"Invalid mode: {mode}. Use 'trash' or 'permanent'"
            )

        result = storage_api.delete_path(path, mode=mode)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Add path to response (required by DeleteResponse model)
        return {"success": result["success"], "path": path, "error": result.get("error")}
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting path: {e}")


# Maintenance operations
@app.get(
    "/api/maintenance/operations",
    tags=["maintenance"],
    response_model=OperationsListResponse,
    summary="List available maintenance operations",
    description="Returns all available maintenance operations with their metadata, categories, and requirements.",
)
async def get_operations() -> dict[str, Any]:
    """Get list of available maintenance operations."""
    try:
        operations = maintenance_api.get_operations()
        return {
            "operations": operations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting operations: {e}")


@app.post(
    "/api/maintenance/run",
    tags=["maintenance"],
    summary="Run maintenance operations",
    description="""
Execute selected maintenance operations with real-time progress streaming.

Returns a Server-Sent Events (SSE) stream with progress updates for each operation.
Operations are executed by the secure launchd daemon (no authentication needed).

**Event Types:**
- `start`: Operation starting
- `progress`: Step-by-step progress
- `complete`: Operation completed successfully
- `skip`: Operation skipped
- `error`: Operation failed
- `done`: All operations finished
    """,
)
async def run_operations(request: RunOperationsRequest):
    """
    Run selected maintenance operations and stream progress.

    Returns a Server-Sent Events (SSE) stream with real-time progress.
    Operations are executed by the secure launchd daemon (no authentication needed).
    """

    async def event_generator():
        """Generate SSE events from maintenance operations."""
        try:
            async for event in maintenance_api.run_operations(request.operation_ids):
                # Format as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@app.post(
    "/api/maintenance/skip",
    tags=["maintenance"],
    response_model=SuccessResponse,
    summary="Skip current operation",
    description="Skips the currently running maintenance operation and proceeds to the next one in the queue.",
)
async def skip_current_operation() -> dict[str, Any]:
    """Skip the current maintenance operation and move to the next."""
    try:
        skipped = maintenance_api.skip_current_operation()
        return {
            "success": True,
            "skipped": skipped,
            "message": "Skip initiated" if skipped else "No operation running",
        }
    except Exception as e:
        import traceback

        logger.error(f"Skip operation error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error skipping operation: {e}")


@app.post(
    "/api/maintenance/cancel",
    tags=["maintenance"],
    response_model=SuccessResponse,
    summary="Cancel all operations",
    description="Cancels all currently running maintenance operations immediately.",
)
async def cancel_operations() -> dict[str, Any]:
    """Cancel running maintenance operations."""
    try:
        cancelled = maintenance_api.cancel_operations()
        return {
            "success": True,
            "cancelled": cancelled,
            "message": "Cancellation initiated" if cancelled else "No operations running",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling operations: {e}")


@app.get(
    "/api/maintenance/queue",
    tags=["maintenance"],
    summary="Get queue status",
    description="""
Get current queue status and running operation information (Task #129).

Provides real-time visibility into:
- Current operation being processed by daemon
- How long current operation has been running
- Number of operations waiting in queue
- Daemon running status

This prevents confusion when operations appear hung - user can see if daemon is actively processing.
    """,
)
async def get_queue_status() -> dict[str, Any]:
    """Get current queue status and operation progress."""
    try:
        return maintenance_api.get_queue_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting queue status: {e}")


@app.get(
    "/api/maintenance/doctor",
    tags=["maintenance"],
    summary="Doctor / preflight checks",
    description="""
Runs a quick preflight to detect missing tools and common issues that would cause maintenance operations to fail.

Returns a list of issues with optional guided fixes.
    """,
)
async def maintenance_doctor() -> dict[str, Any]:
    import shutil
    import subprocess

    def _has(cmd: str) -> bool:
        return shutil.which(cmd) is not None

    issues: list[dict[str, Any]] = []

    # Homebrew
    if (
        not _has("brew")
        and not Path("/opt/homebrew/bin/brew").exists()
        and not Path("/usr/local/bin/brew").exists()
    ):
        issues.append(
            {
                "id": "missing_brew",
                "severity": "warning",
                "title": "Homebrew not installed",
                "detail": "Homebrew is required for Homebrew and mas-based update operations.",
                "affects_operations": ["brew-update", "brew-cleanup", "mas-update"],
                "fix_action": "install_homebrew",
                "fix_label": "Install Homebrew",
            }
        )

    # mas (Mac App Store CLI)
    if (
        not _has("mas")
        and not Path("/opt/homebrew/bin/mas").exists()
        and not Path("/usr/local/bin/mas").exists()
    ):
        issues.append(
            {
                "id": "missing_mas",
                "severity": "warning",
                "title": "mas (App Store CLI) not installed",
                "detail": "mas is used to update Mac App Store applications.",
                "affects_operations": ["mas-update"],
                "fix_action": "install_mas",
                "fix_label": "Install mas",
            }
        )

    # Xcode Command Line Tools (common Homebrew prerequisite)
    try:
        res = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, timeout=3)
        if res.returncode != 0:
            issues.append(
                {
                    "id": "missing_xcode_clt",
                    "severity": "warning",
                    "title": "Xcode Command Line Tools not installed",
                    "detail": "Some tools (especially Homebrew) require Xcode Command Line Tools.",
                    "affects_operations": ["brew-update", "brew-cleanup", "mas-update"],
                    "fix_action": "install_xcode_clt",
                    "fix_label": "Install Xcode CLT",
                }
            )
    except Exception:
        pass

    return {"success": True, "issues": issues}


@app.post(
    "/api/maintenance/doctor/fix",
    tags=["maintenance"],
    summary="Start a guided fix for a doctor issue",
)
async def maintenance_doctor_fix(request: Request) -> dict[str, Any]:
    data = await request.json()
    action = data.get("action")

    allowed = {"install_homebrew", "install_mas", "install_xcode_clt"}
    if action not in allowed:
        raise HTTPException(status_code=400, detail="Unknown fix action")

    # Open Terminal for interactive installers (avoids hanging the web server)
    def open_terminal(command: str) -> None:
        script = f'''tell application "Terminal"
  activate
  do script "{command.replace("\\", "\\\\").replace('"', '\\"')}"
end tell'''
        subprocess.Popen(["osascript", "-e", script])

    if action == "install_homebrew":
        open_terminal(
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        return {"success": True, "message": "Opened Terminal to install Homebrew"}

    if action == "install_mas":
        # Requires brew; if brew is missing the user should run Homebrew install first.
        open_terminal("brew install mas")
        return {"success": True, "message": "Opened Terminal to install mas"}

    if action == "install_xcode_clt":
        open_terminal("xcode-select --install")
        return {"success": True, "message": "Opened the Xcode Command Line Tools installer"}

    return {"success": False, "message": "No action taken"}


@app.get(
    "/api/maintenance/last-run",
    tags=["maintenance"],
    response_model=LastRunResponse,
    summary="Get last run information",
    description="""
Returns timestamp and status information for maintenance operations.

Includes:
- Global last run time (most recent operation)
- Per-operation history with individual timestamps
- Human-readable relative times (e.g., "2 hours ago")
- Operation durations and status

Checks ~/Library/Logs/upkeep for operation history.
    """,
)
async def get_last_run() -> dict[str, Any]:
    """Get timestamp of last maintenance run from timestamp file.

    Checks the ~/Library/Logs/upkeep directory for the last_run_timestamp.txt
    file which contains the actual completion time (not log file mtime).

    Returns:
        Dict with:
        - last_run: ISO format timestamp or None if never run
        - status: "completed" if timestamp found, "never" if no timestamp
        - last_run_relative: Human-readable relative time (e.g., "2 hours ago")
    """
    try:
        log_dir = Path.home() / "Library" / "Logs" / "upkeep"
        timestamp_file = log_dir / "last_run_timestamp.txt"

        if not timestamp_file.exists():
            # Fallback to most recent log file if timestamp doesn't exist yet
            log_files = sorted(log_dir.glob("upkeep-*.log"), reverse=True)
            if not log_files:
                return {
                    "success": True,
                    "global_last_run": None,
                    "global_last_run_relative": "Never",
                    "status": "never",
                    "operations": {},  # TODO: Phase 3 - Per-operation history
                }
            # Use log file mtime as fallback
            last_log = log_files[0]
            mtime = last_log.stat().st_mtime
            last_run_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(mtime))

            # Calculate relative time and return
            now = time.time()
            delta_seconds = int(now - mtime)

            if delta_seconds < 60:
                relative = f"{delta_seconds} seconds ago"
            elif delta_seconds < 3600:
                minutes = delta_seconds // 60
                relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif delta_seconds < 86400:
                hours = delta_seconds // 3600
                relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = delta_seconds // 86400
                relative = f"{days} day{'s' if days != 1 else ''} ago"

            return {
                "success": True,
                "global_last_run": last_run_iso,
                "global_last_run_relative": relative,
                "status": "completed",
                "operations": {},  # TODO: Phase 3 - Per-operation history
            }

        # Read actual completion timestamp from file
        try:
            timestamp_str = timestamp_file.read_text().strip()
            # Parse ISO format timestamp
            from datetime import datetime

            last_run_datetime = datetime.fromisoformat(timestamp_str)
            mtime = last_run_datetime.timestamp()
            last_run_iso = timestamp_str
        except (ValueError, OSError):
            # Fallback to log file mtime if timestamp file is corrupted
            log_files = sorted(log_dir.glob("upkeep-*.log"), reverse=True)
            if not log_files:
                return {
                    "success": True,
                    "global_last_run": None,
                    "global_last_run_relative": "Never",
                    "status": "never",
                    "operations": {},  # TODO: Phase 3 - Per-operation history
                }
            last_log = log_files[0]
            mtime = last_log.stat().st_mtime
            last_run_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(mtime))

        # Calculate relative time
        now = time.time()
        delta_seconds = int(now - mtime)

        if delta_seconds < 60:
            relative = f"{delta_seconds} seconds ago"
        elif delta_seconds < 3600:
            minutes = delta_seconds // 60
            relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif delta_seconds < 86400:
            hours = delta_seconds // 3600
            relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = delta_seconds // 86400
            relative = f"{days} day{'s' if days != 1 else ''} ago"

        # Load per-operation history
        operations_history = {}
        history_file = log_dir / "operation_history.json"
        if history_file.exists():
            try:
                history_data = json.loads(history_file.read_text())

                def _format_seconds(seconds: float) -> str:
                    seconds = max(0.0, float(seconds))
                    if seconds < 60:
                        return f"{int(round(seconds))}s"
                    if seconds < 3600:
                        minutes = int(seconds // 60)
                        rem = int(round(seconds % 60))
                        return f"{minutes}m {rem}s" if rem else f"{minutes}m"
                    hours = int(seconds // 3600)
                    minutes = int(round((seconds % 3600) / 60))
                    return f"{hours}h {minutes}m" if minutes else f"{hours}h"

                def _median(nums: list[float]) -> float | None:
                    if not nums:
                        return None
                    s = sorted(float(n) for n in nums)
                    mid = len(s) // 2
                    if len(s) % 2:
                        return s[mid]
                    return (s[mid - 1] + s[mid]) / 2

                # Calculate relative time for each operation
                for op_id, op_data in history_data.items():
                    try:
                        op_timestamp = datetime.fromisoformat(op_data["last_run"]).timestamp()
                        op_delta = int(now - op_timestamp)

                        if op_delta < 60:
                            op_relative = f"{op_delta} seconds ago"
                        elif op_delta < 3600:
                            minutes = op_delta // 60
                            op_relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                        elif op_delta < 86400:
                            hours = op_delta // 3600
                            op_relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
                        else:
                            days = op_delta // 86400
                            op_relative = f"{days} day{'s' if days != 1 else ''} ago"

                        durations_success = op_data.get("durations_seconds", [])
                        if not isinstance(durations_success, list):
                            durations_success = []
                        med_success = _median(
                            [d for d in durations_success if isinstance(d, (int, float))]
                        )

                        durations_all = op_data.get("durations_all_seconds", [])
                        if not isinstance(durations_all, list):
                            durations_all = []
                        med_all = _median([d for d in durations_all if isinstance(d, (int, float))])

                        # Prefer median of successful runs; fallback to median of all runs.
                        med = med_success if med_success is not None else med_all
                        basis = (
                            "success"
                            if med_success is not None
                            else ("all" if med_all is not None else None)
                        )

                        operations_history[op_id] = {
                            "last_run": op_data["last_run"],
                            "last_run_relative": op_relative,
                            "success": op_data.get("success", True),
                            "last_duration_seconds": op_data.get("last_duration_seconds"),
                            "typical_seconds": round(med, 3) if med is not None else None,
                            "typical_display": _format_seconds(med) if med is not None else None,
                            "typical_runs": len(durations_success),
                            "typical_runs_all": len(durations_all),
                            "typical_basis": basis,
                        }
                    except (ValueError, KeyError):
                        continue
            except json.JSONDecodeError:
                pass

        return {
            "success": True,
            "global_last_run": last_run_iso,
            "global_last_run_relative": relative,
            "status": "completed",
            "operations": operations_history,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting last run: {e}")


# ===================================================================
# SCHEDULE ENDPOINTS
# ===================================================================


@app.get("/api/schedules", tags=["schedules"])
async def list_schedules():
    """List all scheduled maintenance tasks.

    Returns:
        ScheduleListResponse with all schedules
    """
    try:
        # Get storage path from environment or use default
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.list_schedules()

        return response.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing schedules: {e}")


@app.get("/api/schedules/templates", tags=["schedules"])
async def get_schedule_templates():
    """Get preset schedule templates.

    Returns:
        List of schedule templates
    """
    # Research-based schedule templates for Mac maintenance (2025-2026 best practices)
    templates = [
        {
            "name": "Essential Weekly Maintenance",
            "description": "Recommended weekly maintenance: updates, disk health, and basic cleanup",
            "operations": [
                "disk-verify",
                "trim-caches",
                "trim-logs",
                "brew-update",
                "mas-update",
                "periodic",
            ],
            "frequency": "weekly",
            "time_of_day": "03:00:00",
            "days_of_week": ["sunday"],
            "icon": "⭐",
            "recommended": True,
        },
        {
            "name": "Light Daily Cleanup",
            "description": "Quick daily cleanup: logs and DNS cache (runs at 2 AM)",
            "operations": ["trim-logs", "dns-flush"],
            "frequency": "daily",
            "time_of_day": "02:00:00",
            "icon": "🧹",
        },
        {
            "name": "Deep Monthly Maintenance",
            "description": "Comprehensive monthly check: disk health, caches, and system scripts",
            "operations": [
                "disk-verify",
                "smart-check",
                "trim-caches",
                "browser-cache",
                "mail-optimize",
                "periodic",
                "spotlight-status",
            ],
            "frequency": "monthly",
            "time_of_day": "04:00:00",
            "day_of_month": 1,
            "icon": "🔧",
        },
        {
            "name": "Software Updates Weekly",
            "description": "Keep software current: macOS, App Store, and Homebrew updates",
            "operations": ["macos-check", "mas-update", "brew-update", "brew-cleanup"],
            "frequency": "weekly",
            "time_of_day": "10:00:00",
            "days_of_week": ["saturday"],
            "icon": "📦",
        },
        {
            "name": "Developer Cleanup Monthly",
            "description": "Developer-focused cleanup: Xcode, npm, pip, Go caches (20-60GB savings)",
            "operations": [
                "dev-cache",
                "dev-tools-cache",
                "browser-cache",
                "trim-caches",
                "brew-cleanup",
            ],
            "frequency": "monthly",
            "time_of_day": "03:00:00",
            "day_of_month": 15,
            "icon": "💻",
        },
        {
            "name": "Security Focus Weekly",
            "description": "Security-first maintenance: all updates plus disk integrity checks",
            "operations": [
                "macos-check",
                "brew-update",
                "mas-update",
                "disk-verify",
                "smart-check",
            ],
            "frequency": "weekly",
            "time_of_day": "09:00:00",
            "days_of_week": ["monday"],
            "icon": "🔒",
        },
        {
            "name": "Storage Recovery",
            "description": "Maximum space recovery: all cleanup operations (run when disk is full)",
            "operations": [
                "browser-cache",
                "dev-cache",
                "dev-tools-cache",
                "trim-caches",
                "trim-logs",
                "brew-cleanup",
            ],
            "frequency": "monthly",
            "time_of_day": "02:00:00",
            "day_of_month": 1,
            "icon": "💾",
        },
    ]

    return {"templates": templates}


@app.get("/api/schedules/{schedule_id}", tags=["schedules"])
async def get_schedule(schedule_id: str):
    """Get a specific schedule by ID.

    Args:
        schedule_id: Schedule ID

    Returns:
        ScheduleResponse with schedule data
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.get_schedule(schedule_id)

        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)

        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schedule: {e}")


def _configure_pmset_wake(schedule) -> None:
    """Best-effort: configure macOS wake schedule via pmset.

    Notes:
    - Requires admin privileges (sudo). If the server isn't running with sufficient rights,
      this will fail harmlessly.
    - pmset repeat supports daily/weekly patterns but not "monthly day N".
    """
    import subprocess

    freq = getattr(schedule, "frequency", None)
    time_of_day = getattr(schedule, "time_of_day", None)
    days = getattr(schedule, "days_of_week", None) or []

    if not time_of_day:
        return

    hhmm = str(time_of_day)[:5]  # HH:MM

    if freq == "daily":
        # pmset uses MTWRFSU token; daily == all days.
        day_token = "MTWRFSU"
    elif freq == "weekly":
        map_token = {
            "monday": "M",
            "tuesday": "T",
            "wednesday": "W",
            "thursday": "R",
            "friday": "F",
            "saturday": "S",
            "sunday": "U",
        }
        day_token = "".join(map_token.get(str(d).lower(), "") for d in days)
        if not day_token:
            return
    else:
        # Monthly/custom not supported by pmset repeat.
        return

    cmd = ["sudo", "pmset", "repeat", "wakeorpoweron", day_token, hhmm + ":00"]
    subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=10)


@app.post("/api/schedules", tags=["schedules"])
async def create_schedule(request: Request):
    """Create a new schedule.

    Request body should contain schedule configuration:
    - name: Schedule name
    - operations: List of operation IDs
    - frequency: daily, weekly, or monthly
    - time_of_day: Time as HH:MM:SS
    - days_of_week: For weekly schedules (list of day names)
    - day_of_month: For monthly schedules (1-28)
    - enabled: Whether schedule is active

    Returns:
        ScheduleResponse with created schedule
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        # Parse request body
        schedule_data = await request.json()

        # Create schedule via API
        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.create_schedule(schedule_data)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        # Register with launchd (if enabled)
        if response.schedule and response.schedule.enabled:
            launchd = LaunchdGenerator()
            try:
                launchd.save_plist(response.schedule)
                launchd.register_schedule(response.schedule.id)
            except Exception as e:
                # Log error but don't fail - schedule is created
                print(f"Warning: Failed to register with launchd: {e}")

            # Best-effort wake scheduling (optional)
            try:
                if getattr(response.schedule, "wake_mac", False):
                    _configure_pmset_wake(response.schedule)
            except Exception as e:
                print(f"Warning: Failed to configure wake schedule: {e}")

        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating schedule: {e}")


@app.put("/api/schedules/{schedule_id}", tags=["schedules"])
async def update_schedule(schedule_id: str, request: Request):
    """Update an existing schedule.

    Args:
        schedule_id: Schedule ID
        request: Request with fields to update

    Returns:
        ScheduleResponse with updated schedule
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        # Parse request body
        updates = await request.json()

        # Update schedule via API
        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.update_schedule(schedule_id, updates)

        if not response.success:
            if "not found" in response.error.lower():
                raise HTTPException(status_code=404, detail=response.error)
            else:
                raise HTTPException(status_code=400, detail=response.error)

        # Update launchd registration if enabled state changed
        if "enabled" in updates or any(
            key in updates for key in ["frequency", "time_of_day", "days_of_week", "day_of_month"]
        ):
            launchd = LaunchdGenerator()
            try:
                # Unregister old plist
                launchd.unregister_schedule(schedule_id)

                # Register new plist if enabled
                if response.schedule and response.schedule.enabled:
                    launchd.save_plist(response.schedule)
                    launchd.register_schedule(schedule_id)
            except Exception as e:
                print(f"Warning: Failed to update launchd: {e}")

        # Best-effort wake scheduling (optional)
        if "wake_mac" in updates or any(
            key in updates for key in ["frequency", "time_of_day", "days_of_week"]
        ):
            try:
                if (
                    response.schedule
                    and getattr(response.schedule, "wake_mac", False)
                    and response.schedule.enabled
                ):
                    _configure_pmset_wake(response.schedule)
            except Exception as e:
                print(f"Warning: Failed to configure wake schedule: {e}")

        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating schedule: {e}")


@app.delete("/api/schedules/{schedule_id}", tags=["schedules"])
async def delete_schedule(schedule_id: str):
    """Delete a schedule.

    Args:
        schedule_id: Schedule ID

    Returns:
        ScheduleResponse indicating success
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        # Unregister from launchd first
        launchd = LaunchdGenerator()
        try:
            launchd.unregister_schedule(schedule_id)
            launchd.remove_plist(schedule_id)
        except Exception as e:
            print(f"Warning: Failed to unregister from launchd: {e}")

        # Delete schedule via API
        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.delete_schedule(schedule_id)

        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)

        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting schedule: {e}")


@app.patch("/api/schedules/{schedule_id}/enabled", tags=["schedules"])
async def toggle_schedule_enabled(schedule_id: str, request: Request):
    """Enable or disable a schedule.

    Args:
        schedule_id: Schedule ID
        request: Request body with {"enabled": true/false}

    Returns:
        ScheduleResponse with updated schedule
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        # Parse request body
        data = await request.json()
        enabled = data.get("enabled", True)

        # Update schedule
        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.update_schedule(schedule_id, {"enabled": enabled})

        if not response.success:
            if "not found" in response.error.lower():
                raise HTTPException(status_code=404, detail=response.error)
            else:
                raise HTTPException(status_code=400, detail=response.error)

        # Update launchd registration
        launchd = LaunchdGenerator()
        try:
            if enabled:
                # Enable: register with launchd
                launchd.save_plist(response.schedule)
                launchd.register_schedule(schedule_id)
            else:
                # Disable: unregister from launchd
                launchd.unregister_schedule(schedule_id)
        except Exception as e:
            print(f"Warning: Failed to update launchd: {e}")

        return response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling schedule: {e}")


@app.post("/api/schedules/{schedule_id}/run-now", tags=["schedules"])
async def run_schedule_now(schedule_id: str):
    """Trigger immediate execution of a schedule (test run).

    Args:
        schedule_id: Schedule ID

    Returns:
        Success response
    """
    try:
        import os

        storage_path = os.getenv("MAC_MAINTENANCE_SCHEDULE_STORAGE")

        # Get schedule
        schedule_api = ScheduleAPI(storage_path=Path(storage_path) if storage_path else None)
        response = schedule_api.get_schedule(schedule_id)

        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)

        # Execute operations
        from upkeep.core.launchd import run_scheduled_task_async

        try:
            # For interactive runs, don't block forever behind another scheduled batch.
            success = await run_scheduled_task_async(schedule_id, lock_wait_seconds=60)
        except Exception as e:
            # Surface the underlying reason to the UI
            return {"success": False, "message": f"Schedule execution error: {e}"}

        if success:
            return {
                "success": True,
                "message": f"Schedule '{response.schedule.name}' executed successfully",
            }
        else:
            return {"success": False, "message": "Schedule execution failed (check ~/.upkeep/logs)"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running schedule: {e}")


# Serve static files (web UI)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():

    @app.get("/", response_class=FileResponse)
    async def read_root():
        """Serve the main HTML page."""
        return FileResponse(static_dir / "index.html")

    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon."""
        favicon_path = static_dir / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        # Fallback if SVG doesn't exist
        return (
            FileResponse(static_dir / "favicon.ico")
            if (static_dir / "favicon.ico").exists()
            else None
        )

    # Mount static files for CSS/JS
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:

    @app.get("/")
    async def read_root():
        """API root - static files not found."""
        return {
            "message": "Upkeep API",
            "version": __version__,
            "docs": "/docs",
            "note": "Static files not found. Web UI unavailable.",
        }


if __name__ == "__main__":
    import uvicorn

    from .port_utils import find_available_port

    # Find available port (8080-8089)
    port = find_available_port(8080, 8089)

    if port is None:
        print("ERROR: No available ports in range 8080-8089", file=sys.stderr)
        print("Close other applications or specify a different port", file=sys.stderr)
        sys.exit(1)

    if port != 8080:
        print(f"⚠️  Port 8080 in use, using port {port} instead")

    print(f"\n🚀 Starting server on http://127.0.0.1:{port}\n")

    uvicorn.run(app, host="127.0.0.1", port=port)
