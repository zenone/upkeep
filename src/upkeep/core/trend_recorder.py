"""
Trend Recorder - Track health metrics over time.

Records system state at intervals and provides historical data
for trend visualization and alerts.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import psutil


@dataclass
class TrendDataPoint:
    """A single trend measurement."""

    timestamp: str  # ISO 8601 UTC
    health_score: float  # 0-100
    disk_used: int  # bytes
    disk_total: int  # bytes
    disk_free_percent: float  # 0-100
    cache_size: int  # bytes
    trash_size: int  # bytes
    log_size: int  # bytes

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "healthScore": self.health_score,
            "diskUsed": self.disk_used,
            "diskTotal": self.disk_total,
            "diskFreePercent": self.disk_free_percent,
            "cacheSize": self.cache_size,
            "trashSize": self.trash_size,
            "logSize": self.log_size,
        }


def _sum_directory(path: Path) -> int:
    """Sum total size of files in a directory (non-recursive for speed)."""
    total = 0
    try:
        if not path.exists():
            return 0
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    # Only go one level deep for performance
                    for subentry in os.scandir(entry.path):
                        try:
                            if subentry.is_file(follow_symlinks=False):
                                total += subentry.stat(follow_symlinks=False).st_size
                        except (OSError, PermissionError):
                            pass
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return total


def _calculate_simple_health_score() -> float:
    """Calculate a simplified health score (0-100).

    Factors:
    - Disk free space (40% weight)
    - Memory availability (30% weight)
    - CPU not overloaded (30% weight)
    """
    try:
        # Disk score (0-40 points)
        disk = psutil.disk_usage("/")
        disk_free_pct = (disk.free / disk.total) * 100
        if disk_free_pct >= 20:
            disk_score = 40
        elif disk_free_pct >= 10:
            disk_score = 30
        elif disk_free_pct >= 5:
            disk_score = 20
        else:
            disk_score = 10

        # Memory score (0-30 points)
        mem = psutil.virtual_memory()
        mem_available_pct = (mem.available / mem.total) * 100
        if mem_available_pct >= 30:
            mem_score = 30
        elif mem_available_pct >= 20:
            mem_score = 25
        elif mem_available_pct >= 10:
            mem_score = 15
        else:
            mem_score = 5

        # CPU score (0-30 points) - lower is better
        cpu_pct = psutil.cpu_percent(interval=0.1)
        if cpu_pct <= 30:
            cpu_score = 30
        elif cpu_pct <= 60:
            cpu_score = 25
        elif cpu_pct <= 80:
            cpu_score = 15
        else:
            cpu_score = 5

        return disk_score + mem_score + cpu_score

    except Exception:
        return 50.0  # Default middle score on error


class TrendRecorder:
    """Record and retrieve historical trend data."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        health_score REAL NOT NULL,
        disk_used INTEGER NOT NULL,
        disk_total INTEGER NOT NULL,
        disk_free_percent REAL NOT NULL,
        cache_size INTEGER NOT NULL,
        trash_size INTEGER NOT NULL,
        log_size INTEGER NOT NULL,
        resolution TEXT DEFAULT 'high',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_trends_timestamp ON trends(timestamp);
    CREATE INDEX IF NOT EXISTS idx_trends_resolution ON trends(resolution);
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize with optional custom DB path."""
        self.db_path = db_path or self._default_db_path()
        self._init_db()

    @staticmethod
    def _default_db_path() -> Path:
        """Return default database path: ~/.upkeep/trends.db"""
        upkeep_dir = Path.home() / ".upkeep"
        upkeep_dir.mkdir(parents=True, exist_ok=True)
        return upkeep_dir / "trends.db"

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def record_snapshot(self, resolution: str = "high") -> TrendDataPoint:
        """Capture current system state and store it.

        Args:
            resolution: Data resolution level (high, daily, weekly, monthly)

        Returns:
            The recorded data point
        """
        # Get disk usage
        disk = psutil.disk_usage("/")
        disk_used = disk.used
        disk_total = disk.total
        disk_free_percent = (disk.free / disk.total) * 100

        # Calculate health score
        health_score = _calculate_simple_health_score()

        # Calculate directory sizes
        home = Path.home()
        cache_size = _sum_directory(home / "Library" / "Caches")
        trash_size = _sum_directory(home / ".Trash")
        log_size = _sum_directory(home / "Library" / "Logs")

        # Create data point
        timestamp = datetime.utcnow().isoformat() + "Z"
        point = TrendDataPoint(
            timestamp=timestamp,
            health_score=round(health_score, 1),
            disk_used=disk_used,
            disk_total=disk_total,
            disk_free_percent=round(disk_free_percent, 2),
            cache_size=cache_size,
            trash_size=trash_size,
            log_size=log_size,
        )

        # Store in database
        self._store(point, resolution)
        return point

    def _store(self, point: TrendDataPoint, resolution: str = "high") -> None:
        """Store a data point in the database."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO trends (
                    timestamp, health_score, disk_used, disk_total,
                    disk_free_percent, cache_size, trash_size, log_size,
                    resolution
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    point.timestamp,
                    point.health_score,
                    point.disk_used,
                    point.disk_total,
                    point.disk_free_percent,
                    point.cache_size,
                    point.trash_size,
                    point.log_size,
                    resolution,
                ),
            )

    def get_latest(self, count: int = 30) -> list[TrendDataPoint]:
        """Get most recent N data points.

        Args:
            count: Number of points to retrieve

        Returns:
            List of data points, newest first
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, health_score, disk_used, disk_total,
                       disk_free_percent, cache_size, trash_size, log_size
                FROM trends
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (count,),
            )
            rows = cursor.fetchall()

        return [
            TrendDataPoint(
                timestamp=row[0],
                health_score=row[1],
                disk_used=row[2],
                disk_total=row[3],
                disk_free_percent=row[4],
                cache_size=row[5],
                trash_size=row[6],
                log_size=row[7],
            )
            for row in rows
        ]

    def get_range(
        self,
        start: datetime,
        end: datetime,
        resolution: Literal["all", "daily", "weekly", "monthly"] = "all",
    ) -> list[TrendDataPoint]:
        """Retrieve data points in time range.

        Args:
            start: Start of range (UTC)
            end: End of range (UTC)
            resolution: Filter by resolution level

        Returns:
            List of data points, oldest first
        """
        start_str = start.isoformat() + "Z"
        end_str = end.isoformat() + "Z"

        query = """
            SELECT timestamp, health_score, disk_used, disk_total,
                   disk_free_percent, cache_size, trash_size, log_size
            FROM trends
            WHERE timestamp >= ? AND timestamp <= ?
        """
        params: list = [start_str, end_str]

        if resolution != "all":
            query += " AND resolution = ?"
            params.append(resolution)

        query += " ORDER BY timestamp ASC"

        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            TrendDataPoint(
                timestamp=row[0],
                health_score=row[1],
                disk_used=row[2],
                disk_total=row[3],
                disk_free_percent=row[4],
                cache_size=row[5],
                trash_size=row[6],
                log_size=row[7],
            )
            for row in rows
        ]

    def get_days(self, days: int = 30) -> list[TrendDataPoint]:
        """Get data points from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of data points, oldest first
        """
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        return self.get_range(start, end)

    def compact(self) -> int:
        """Run compaction to downsample old data.

        Retention policy:
        - Keep high-res (all) for last 7 days
        - Keep daily summaries for 8-90 days
        - Keep weekly summaries for 91-365 days
        - Keep monthly summaries beyond 365 days

        Returns:
            Number of rows removed
        """
        now = datetime.utcnow()
        removed = 0

        with self._get_conn() as conn:
            # Get count before
            before_count = conn.execute("SELECT COUNT(*) FROM trends").fetchone()[0]

            # 1. Remove high-res data older than 7 days (but keep other resolutions)
            cutoff_7d = (now - timedelta(days=7)).isoformat() + "Z"
            conn.execute(
                """
                DELETE FROM trends
                WHERE timestamp < ? AND resolution = 'high'
                """,
                (cutoff_7d,),
            )

            # 2. Remove daily data older than 90 days
            cutoff_90d = (now - timedelta(days=90)).isoformat() + "Z"
            conn.execute(
                """
                DELETE FROM trends
                WHERE timestamp < ? AND resolution = 'daily'
                """,
                (cutoff_90d,),
            )

            # 3. Remove weekly data older than 365 days
            cutoff_365d = (now - timedelta(days=365)).isoformat() + "Z"
            conn.execute(
                """
                DELETE FROM trends
                WHERE timestamp < ? AND resolution = 'weekly'
                """,
                (cutoff_365d,),
            )

            # Get count after
            after_count = conn.execute("SELECT COUNT(*) FROM trends").fetchone()[0]
            removed = before_count - after_count

        # Vacuum to reclaim space (requires autocommit mode)
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            conn.execute("VACUUM")
        finally:
            conn.close()

        return removed

    def stats(self) -> dict:
        """Return database statistics.

        Returns:
            Dict with row_count, oldest, newest, db_size_bytes
        """
        with self._get_conn() as conn:
            row_count = conn.execute("SELECT COUNT(*) FROM trends").fetchone()[0]

            oldest_row = conn.execute(
                "SELECT timestamp FROM trends ORDER BY timestamp ASC LIMIT 1"
            ).fetchone()
            newest_row = conn.execute(
                "SELECT timestamp FROM trends ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()

        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "row_count": row_count,
            "oldest": oldest_row[0] if oldest_row else None,
            "newest": newest_row[0] if newest_row else None,
            "db_size_bytes": db_size,
        }

    def should_record(self, min_hours: float = 4.0) -> bool:
        """Check if enough time has passed since last recording.

        Args:
            min_hours: Minimum hours between recordings

        Returns:
            True if we should record a new snapshot
        """
        latest = self.get_latest(1)
        if not latest:
            return True

        last_time = datetime.fromisoformat(latest[0].timestamp.replace("Z", "+00:00"))
        now = datetime.now(last_time.tzinfo)
        elapsed = now - last_time

        return elapsed >= timedelta(hours=min_hours)
