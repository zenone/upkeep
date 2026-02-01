"""
Maintenance API - Core operations for system maintenance.

API-first architecture: All maintenance operations exposed via clean API.
"""

import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncIterator
from datetime import datetime


class MaintenanceAPI:
    """API for system maintenance operations."""

    # Define all operations with metadata
    OPERATIONS = {
        # System Updates
        "macos-check": {
            "id": "macos-check",
            "name": "Check macOS Updates",
            "description": "Check for available macOS system updates",
            "category": "System Updates",
            "command": ["./maintain.sh", "--list-macos-updates"],
            "safe": True,
            "recommended": False,
        },
        "macos-install": {
            "id": "macos-install",
            "name": "Install macOS Updates",
            "description": "Install available macOS system updates",
            "category": "System Updates",
            "command": ["./maintain.sh", "--install-macos-updates", "--assume-yes"],
            "safe": False,
            "recommended": False,
        },
        "brew-update": {
            "id": "brew-update",
            "name": "Update Homebrew",
            "description": "Update Homebrew packages",
            "category": "System Updates",
            "command": ["./maintain.sh", "--brew", "--assume-yes"],
            "safe": True,
            "recommended": True,
        },
        "mas-update": {
            "id": "mas-update",
            "name": "Update App Store Apps",
            "description": "Update Mac App Store applications",
            "category": "System Updates",
            "command": ["./maintain.sh", "--mas", "--assume-yes"],
            "safe": True,
            "recommended": True,
        },

        # Disk Operations
        "disk-verify": {
            "id": "disk-verify",
            "name": "Verify Disk",
            "description": "Verify disk health and integrity",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--verify-disk"],
            "safe": True,
            "recommended": True,
        },
        "disk-repair": {
            "id": "disk-repair",
            "name": "Repair Disk",
            "description": "Repair disk errors if found",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--repair-disk", "--assume-yes"],
            "safe": False,
            "recommended": False,
        },
        "smart-check": {
            "id": "smart-check",
            "name": "Check SMART Status",
            "description": "Check disk SMART health status",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--smart"],
            "safe": True,
            "recommended": False,
        },

        # Cleanup Operations
        "trim-logs": {
            "id": "trim-logs",
            "name": "Trim User Logs",
            "description": "Remove user logs older than 30 days",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--trim-logs", "30", "--assume-yes"],
            "safe": True,
            "recommended": False,
        },
        "trim-caches": {
            "id": "trim-caches",
            "name": "Trim User Caches",
            "description": "Remove user caches older than 30 days",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--trim-caches", "30", "--assume-yes"],
            "safe": True,
            "recommended": False,
        },
        "thin-tm": {
            "id": "thin-tm",
            "name": "Thin Time Machine Snapshots",
            "description": "Remove old Time Machine local snapshots",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--thin-tm-snapshots", "--assume-yes"],
            "safe": False,
            "recommended": False,
        },

        # System Operations
        "spotlight-status": {
            "id": "spotlight-status",
            "name": "Check Spotlight Status",
            "description": "Check Spotlight indexing status",
            "category": "System Operations",
            "command": ["./maintain.sh", "--spotlight-status"],
            "safe": True,
            "recommended": False,
        },
        "spotlight-reindex": {
            "id": "spotlight-reindex",
            "name": "Rebuild Spotlight Index",
            "description": "Rebuild Spotlight search index",
            "category": "System Operations",
            "command": ["./maintain.sh", "--spotlight-reindex", "--assume-yes"],
            "safe": False,
            "recommended": False,
        },
        "dns-flush": {
            "id": "dns-flush",
            "name": "Flush DNS Cache",
            "description": "Clear DNS resolver cache",
            "category": "System Operations",
            "command": ["./maintain.sh", "--flush-dns", "--assume-yes"],
            "safe": True,
            "recommended": False,
        },
        "periodic": {
            "id": "periodic",
            "name": "Run Periodic Scripts",
            "description": "Run macOS daily/weekly/monthly maintenance scripts",
            "category": "System Operations",
            "command": ["./maintain.sh", "--periodic", "--assume-yes"],
            "safe": True,
            "recommended": True,
        },

        # Reports
        "space-report": {
            "id": "space-report",
            "name": "Disk Space Report",
            "description": "Generate detailed disk space usage report",
            "category": "Reports & Analysis",
            "command": ["./maintain.sh", "--space-report"],
            "safe": True,
            "recommended": False,
        },
    }

    def __init__(self):
        """Initialize the Maintenance API."""
        self._current_proc: Optional[asyncio.subprocess.Process] = None
        self._cancel_requested = False
        self._skip_requested = False
        self._sudo_keepalive_task: Optional[asyncio.Task] = None
        self._askpass_script: Optional[str] = None
        self._sudo_wrapper_dir: Optional[str] = None
        self._sudo_wrapper: Optional[str] = None

    def get_operations(self) -> List[Dict[str, Any]]:
        """
        Get list of all available maintenance operations.

        Returns:
            List of operation dictionaries with metadata
        """
        return list(self.OPERATIONS.values())

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific operation by ID.

        Args:
            operation_id: ID of the operation

        Returns:
            Operation dictionary or None if not found
        """
        return self.OPERATIONS.get(operation_id)

    def _create_askpass_script(self, sudo_password: str) -> str:
        """
        Create a temporary SUDO_ASKPASS script that outputs the password.

        This allows sudo to get the password non-interactively when stdin is not a TTY.

        Args:
            sudo_password: The sudo password to use

        Returns:
            Path to the temporary script
        """
        # Create temporary script
        fd, script_path = tempfile.mkstemp(suffix='.sh', prefix='sudo_askpass_')

        # Write script that echoes the password
        script_content = f"#!/bin/sh\necho '{sudo_password}'\n"
        os.write(fd, script_content.encode())
        os.close(fd)

        # Make executable
        os.chmod(script_path, 0o700)

        return script_path

    def _create_sudo_wrapper(self, askpass_script: str) -> tuple[str, str]:
        """
        Create a sudo wrapper script that forces askpass usage.

        Args:
            askpass_script: Path to the askpass script

        Returns:
            Tuple of (wrapper_dir, wrapper_path) where wrapper is named "sudo"
        """
        # Create temporary directory for wrapper
        wrapper_dir = tempfile.mkdtemp(prefix='sudo_wrapper_')

        # Create wrapper named "sudo" in this directory
        wrapper_path = os.path.join(wrapper_dir, 'sudo')

        # Write wrapper that calls real sudo with -A flag
        wrapper_content = f"""#!/bin/sh
# Sudo wrapper that forces askpass mode
export SUDO_ASKPASS="{askpass_script}"
export DISPLAY=:0
exec /usr/bin/sudo -A "$@"
"""
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)

        # Make executable
        os.chmod(wrapper_path, 0o700)

        return wrapper_dir, wrapper_path

    def _cleanup_askpass_script(self):
        """Clean up the temporary askpass script and sudo wrapper."""
        if self._askpass_script and os.path.exists(self._askpass_script):
            try:
                os.unlink(self._askpass_script)
            except Exception:
                pass
            self._askpass_script = None

        if self._sudo_wrapper_dir and os.path.exists(self._sudo_wrapper_dir):
            try:
                import shutil
                shutil.rmtree(self._sudo_wrapper_dir)
            except Exception:
                pass
            self._sudo_wrapper_dir = None
            self._sudo_wrapper = None

    async def _sudo_keepalive(self, sudo_password: str):
        """Keep sudo credentials alive by refreshing every 60 seconds."""
        while not self._cancel_requested:
            try:
                await asyncio.sleep(60)  # Refresh every 60 seconds
                if not self._cancel_requested:
                    proc = await asyncio.create_subprocess_exec(
                        "sudo", "-S", "-v",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    proc.stdin.write(f"{sudo_password}\n".encode())
                    await proc.stdin.drain()
                    proc.stdin.close()
                    await proc.wait()
            except Exception:
                pass  # Ignore keepalive errors

    async def run_operations(
        self,
        operation_ids: List[str],
        sudo_password: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run multiple maintenance operations sequentially and stream progress.

        Args:
            operation_ids: List of operation IDs to run
            sudo_password: Optional sudo password for privileged operations

        Yields:
            Progress events as dictionaries
        """
        self._cancel_requested = False
        total = len(operation_ids)
        results = []

        # Create SUDO_ASKPASS script if password provided
        # This allows sudo to get password non-interactively in subprocesses
        if sudo_password:
            self._askpass_script = self._create_askpass_script(sudo_password)
            self._sudo_wrapper_dir, self._sudo_wrapper = self._create_sudo_wrapper(self._askpass_script)
            self._sudo_keepalive_task = asyncio.create_task(
                self._sudo_keepalive(sudo_password)
            )

        try:
            yield {
                "type": "start",
                "message": f"Starting {total} maintenance operation(s)...",
                "total": total,
                "timestamp": datetime.now().isoformat(),
            }

            for idx, op_id in enumerate(operation_ids, 1):
                if self._cancel_requested:
                    yield {
                        "type": "cancelled",
                        "message": "Batch cancelled by user",
                        "timestamp": datetime.now().isoformat(),
                    }
                    break

                operation = self.OPERATIONS.get(op_id)
                if not operation:
                    yield {
                        "type": "error",
                        "operation_id": op_id,
                        "message": f"Unknown operation: {op_id}",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                yield {
                    "type": "operation_start",
                    "operation_id": op_id,
                    "operation_name": operation["name"],
                    "progress": f"{idx}/{total}",
                    "timestamp": datetime.now().isoformat(),
                }

                # Run the operation
                async for event in self._run_single_operation(op_id, operation, sudo_password):
                    yield event

                # Check if skip was requested
                if self._skip_requested:
                    self._skip_requested = False  # Reset for next operation
                    yield {
                        "type": "operation_skipped",
                        "operation_id": op_id,
                        "message": f"{operation['name']} skipped by user",
                        "timestamp": datetime.now().isoformat(),
                    }
                    results.append({
                        "operation_id": op_id,
                        "success": False,
                        "returncode": -2,  # -2 indicates skipped
                        "skipped": True,
                    })
                    continue  # Move to next operation

                # Check if operation succeeded
                if event.get("type") == "operation_complete":
                    results.append({
                        "operation_id": op_id,
                        "success": event.get("success", False),
                        "returncode": event.get("returncode", -1),
                    })

            # Send summary
            successful = sum(1 for r in results if r.get("success"))
            failed = len(results) - successful

            yield {
                "type": "summary",
                "total": total,
                "successful": successful,
                "failed": failed,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

            yield {
                "type": "complete",
                "message": f"Completed {total} operation(s): {successful} successful, {failed} failed",
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            # Stop sudo keepalive task
            if self._sudo_keepalive_task:
                self._cancel_requested = True  # Signal keepalive to stop
                try:
                    self._sudo_keepalive_task.cancel()
                    await self._sudo_keepalive_task
                except asyncio.CancelledError:
                    pass
                self._sudo_keepalive_task = None

            # Clean up askpass script
            self._cleanup_askpass_script()

    async def _run_single_operation(
        self, op_id: str, operation: Dict[str, Any], sudo_password: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run a single operation and stream output.

        Args:
            op_id: Operation ID
            operation: Operation metadata dictionary
            sudo_password: Optional sudo password for privileged operations

        Yields:
            Progress events
        """
        # Find maintain.sh
        script_path = Path(__file__).parent.parent.parent.parent / "maintain.sh"
        if not script_path.exists():
            script_path = Path.cwd() / "maintain.sh"

        if not script_path.exists():
            yield {
                "type": "operation_error",
                "operation_id": op_id,
                "message": f"Cannot find maintain.sh at {script_path}",
                "timestamp": datetime.now().isoformat(),
            }
            yield {
                "type": "operation_complete",
                "operation_id": op_id,
                "success": False,
                "returncode": -1,
                "timestamp": datetime.now().isoformat(),
            }
            return

        # Update command with resolved path
        command = operation["command"].copy()
        if command[0] == "./maintain.sh":
            command[0] = str(script_path)

        try:
            # If we have a sudo password, refresh sudo timestamp before running
            # This ensures maintain.sh's internal sudo calls won't prompt for password
            if sudo_password:
                try:
                    refresh_proc = await asyncio.create_subprocess_exec(
                        "sudo", "-S", "-v",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    refresh_proc.stdin.write(f"{sudo_password}\n".encode())
                    await refresh_proc.stdin.drain()
                    refresh_proc.stdin.close()
                    await refresh_proc.wait()
                except Exception as e:
                    yield {
                        "type": "operation_error",
                        "operation_id": op_id,
                        "message": f"Failed to refresh sudo timestamp: {e}",
                        "timestamp": datetime.now().isoformat(),
                    }

            # Set up environment with sudo wrapper to intercept sudo calls
            env = os.environ.copy()
            if sudo_password and self._sudo_wrapper_dir:
                # Put wrapper directory at the START of PATH
                # This makes maintain.sh call our wrapper instead of /usr/bin/sudo
                original_path = env.get('PATH', '/usr/local/bin:/usr/bin:/bin')
                env['PATH'] = f"{self._sudo_wrapper_dir}:{original_path}"

                # Also set SUDO_ASKPASS for fallback
                env['SUDO_ASKPASS'] = self._askpass_script
                env['DISPLAY'] = ':0'

            # Run command normally (not as root)
            # The script will call sudo internally when needed
            # Sudo will use SUDO_ASKPASS to get the password
            # CRITICAL: stdin must be DEVNULL so sudo knows it's non-interactive
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.DEVNULL,  # Force non-interactive mode
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=script_path.parent,
                env=env if sudo_password else None,
            )

            self._current_proc = proc

            # Stream output
            async def read_stdout():
                while True:
                    if self._cancel_requested and proc.returncode is None:
                        try:
                            proc.terminate()
                            await asyncio.sleep(0.5)
                            if proc.returncode is None:
                                proc.kill()
                        except ProcessLookupError:
                            pass
                        return

                    line = await proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip()
                    yield {
                        "type": "output",
                        "operation_id": op_id,
                        "stream": "stdout",
                        "line": decoded,
                        "timestamp": datetime.now().isoformat(),
                    }

            async def read_stderr():
                while True:
                    if self._cancel_requested and proc.returncode is None:
                        return

                    line = await proc.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip()
                    yield {
                        "type": "output",
                        "operation_id": op_id,
                        "stream": "stderr",
                        "line": decoded,
                        "timestamp": datetime.now().isoformat(),
                    }

            # Stream both stdout and stderr
            async for event in read_stdout():
                yield event
            async for event in read_stderr():
                yield event

            # Wait for completion with timeout
            await asyncio.wait_for(proc.wait(), timeout=1800)  # 30 minute timeout

            self._current_proc = None

            yield {
                "type": "operation_complete",
                "operation_id": op_id,
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "timestamp": datetime.now().isoformat(),
            }

        except asyncio.TimeoutError:
            self._current_proc = None
            yield {
                "type": "operation_error",
                "operation_id": op_id,
                "message": "Operation timed out (30 minute limit)",
                "timestamp": datetime.now().isoformat(),
            }
            yield {
                "type": "operation_complete",
                "operation_id": op_id,
                "success": False,
                "returncode": -1,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self._current_proc = None
            yield {
                "type": "operation_error",
                "operation_id": op_id,
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            yield {
                "type": "operation_complete",
                "operation_id": op_id,
                "success": False,
                "returncode": -1,
                "timestamp": datetime.now().isoformat(),
            }

    def skip_current_operation(self) -> bool:
        """
        Skip the current operation and move to the next.

        Returns:
            True if skip was initiated
        """
        self._skip_requested = True
        if self._current_proc and self._current_proc.returncode is None:
            try:
                self._current_proc.terminate()
                return True
            except ProcessLookupError:
                pass
        return False

    def cancel_operations(self) -> bool:
        """
        Cancel running operations.

        Returns:
            True if cancellation was initiated
        """
        self._cancel_requested = True
        if self._current_proc and self._current_proc.returncode is None:
            try:
                self._current_proc.terminate()
                return True
            except ProcessLookupError:
                pass
        return False
