"""
SystemAPI - System information and monitoring.

API-First Design: Clean interface for system metrics, health scoring,
and process monitoring. Used by Web GUI, CLI, and TUI.
"""

import psutil
from dataclasses import dataclass
from typing import List, Dict, Any

from .base import BaseAPI
from upkeep.core import system as system_utils
from upkeep.core.exceptions import SystemMetricsError
from upkeep.core.types import HealthStatus, ProcessSortBy


@dataclass
class SystemInfo:
    """System information (OS details)."""

    username: str
    hostname: str
    version: str  # macOS version
    architecture: str  # arm64, x86_64


@dataclass
class SystemMetrics:
    """Current system resource usage."""

    cpu_percent: float
    cpu_count: int
    memory_total_gb: float
    memory_used_gb: float
    memory_available_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float


@dataclass
class HealthIssue:
    """A system health issue."""

    severity: str  # "warning" or "critical"
    message: str


@dataclass
class HealthScore:
    """System health assessment."""

    score: int  # 0-100
    status: HealthStatus
    breakdown: Dict[str, Dict[str, Any]]
    issues: List[Dict[str, str]]


@dataclass
class ProcessInfo:
    """Process resource usage information."""

    pid: int
    name: str
    cpu_percent: float
    memory_mb: float


class SystemAPI(BaseAPI):
    """API for system information and monitoring.

    Provides:
    - System information (OS, architecture)
    - Real-time metrics (CPU, memory, disk)
    - Health scoring (0-100 with breakdown)
    - Top processes (CPU/memory consumers)
    """

    def get_info(self) -> SystemInfo:
        """Get comprehensive system information.

        Returns:
            SystemInfo with OS version, hostname, architecture

        Raises:
            SystemMetricsError: If system info cannot be retrieved
        """
        self._log_call("get_info")

        try:
            info = system_utils.get_system_info()
            return SystemInfo(
                username=info['username'],
                hostname=info['hostname'],
                version=info['version'],
                architecture=info['architecture']
            )
        except SystemMetricsError:
            raise
        except Exception as e:
            raise SystemMetricsError(f"Failed to get system info: {e}")

    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics.

        Returns:
            SystemMetrics with CPU, memory, disk usage

        Raises:
            SystemMetricsError: If metrics cannot be retrieved
        """
        self._log_call("get_metrics")

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage("/")

            return SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_total_gb=memory.total / (1024**3),
                memory_used_gb=memory.used / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                memory_percent=memory.percent,
                disk_total_gb=disk.total / (1024**3),
                disk_used_gb=disk.used / (1024**3),
                disk_free_gb=disk.free / (1024**3),
                disk_percent=disk.percent,
            )
        except Exception as e:
            raise SystemMetricsError(f"Failed to get system metrics: {e}")

    def get_health_score(self) -> HealthScore:
        """Calculate system health score (0-100).

        Score based on weighted average:
        - CPU: 30%
        - Memory: 40%
        - Disk: 30%

        Returns:
            HealthScore with score, status, breakdown, and issues

        Raises:
            SystemMetricsError: If health cannot be calculated
        """
        self._log_call("get_health_score")

        try:
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

            # Calculate component scores (invert: lower usage = higher score)
            cpu_score = max(0, 100 - cpu_percent)
            memory_score = max(0, 100 - memory_percent)
            disk_score = max(0, 100 - disk_percent)

            # Weighted average
            overall_score = int(
                (cpu_score * 0.3) + (memory_score * 0.4) + (disk_score * 0.3)
            )

            # Determine status
            if overall_score >= 80:
                status = HealthStatus.EXCELLENT
            elif overall_score >= 60:
                status = HealthStatus.GOOD
            elif overall_score >= 40:
                status = HealthStatus.FAIR
            else:
                status = HealthStatus.POOR

            # Identify issues
            issues = []
            if cpu_percent > 80:
                issues.append({
                    "severity": "warning" if cpu_percent < 90 else "critical",
                    "message": f"CPU usage high ({cpu_percent:.1f}%)"
                })
            if memory_percent > 80:
                issues.append({
                    "severity": "warning" if memory_percent < 90 else "critical",
                    "message": f"Memory usage high ({memory_percent:.1f}%)"
                })
            if disk_percent > 80:
                issues.append({
                    "severity": "warning" if disk_percent < 90 else "critical",
                    "message": f"Disk usage high ({disk_percent:.1f}%)"
                })

            return HealthScore(
                score=overall_score,
                status=status,
                breakdown={
                    "cpu": {
                        "score": int(cpu_score),
                        "weight": 0.3,
                        "usage": cpu_percent
                    },
                    "memory": {
                        "score": int(memory_score),
                        "weight": 0.4,
                        "usage": memory_percent
                    },
                    "disk": {
                        "score": int(disk_score),
                        "weight": 0.3,
                        "usage": disk_percent
                    },
                },
                issues=issues
            )
        except Exception as e:
            raise SystemMetricsError(f"Failed to calculate health score: {e}")

    def get_top_processes(
        self,
        by: ProcessSortBy = ProcessSortBy.CPU,
        limit: int = 5
    ) -> List[ProcessInfo]:
        """Get top resource-consuming processes.

        Args:
            by: Sort by 'cpu' or 'memory'
            limit: Number of processes to return

        Returns:
            List of ProcessInfo objects sorted by resource usage

        Raises:
            SystemMetricsError: If processes cannot be retrieved
        """
        self._log_call("get_top_processes", by=by, limit=limit)

        try:
            processes = []

            # Iterate through all processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'] or 0.0,
                        'memory_mb': (pinfo['memory_info'].rss / (1024 * 1024)) if pinfo['memory_info'] else 0.0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Skip processes we can't access
                    continue

            # Sort based on requested metric
            if by == ProcessSortBy.CPU:
                sorted_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
            else:  # ProcessSortBy.MEMORY
                sorted_processes = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)

            # Take top N
            top_processes = sorted_processes[:limit]

            # Convert to ProcessInfo objects
            return [
                ProcessInfo(
                    pid=p['pid'],
                    name=p['name'],
                    cpu_percent=round(p['cpu_percent'], 1),
                    memory_mb=round(p['memory_mb'], 1)
                )
                for p in top_processes
            ]

        except Exception as e:
            raise SystemMetricsError(f"Failed to get top processes: {e}")
