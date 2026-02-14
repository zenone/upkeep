"""Tests for TrendRecorder."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from upkeep.core.trend_recorder import TrendDataPoint, TrendRecorder


@pytest.fixture
def recorder(tmp_path: Path) -> TrendRecorder:
    """Create a TrendRecorder with temp database."""
    return TrendRecorder(db_path=tmp_path / "test_trends.db")


@pytest.fixture
def populated_recorder(tmp_path: Path) -> TrendRecorder:
    """Create a TrendRecorder with sample data."""
    recorder = TrendRecorder(db_path=tmp_path / "test_trends.db")

    # Insert test data points over several days
    base_time = datetime.utcnow() - timedelta(days=10)

    for i in range(20):
        point = TrendDataPoint(
            timestamp=(base_time + timedelta(hours=i * 12)).isoformat() + "Z",
            health_score=70 + (i % 10),  # Varies 70-79
            disk_used=100_000_000_000 + i * 1_000_000_000,
            disk_total=500_000_000_000,
            disk_free_percent=80 - (i * 0.2),
            cache_size=5_000_000_000 + i * 100_000_000,
            trash_size=1_000_000_000,
            log_size=500_000_000,
        )
        recorder._store(point, resolution="high")

    return recorder


class TestTrendDataPoint:
    """Tests for TrendDataPoint dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        point = TrendDataPoint(
            timestamp="2026-02-14T12:00:00Z",
            health_score=75.5,
            disk_used=100_000_000_000,
            disk_total=500_000_000_000,
            disk_free_percent=80.0,
            cache_size=5_000_000_000,
            trash_size=1_000_000_000,
            log_size=500_000_000,
        )

        d = point.to_dict()

        assert d["timestamp"] == "2026-02-14T12:00:00Z"
        assert d["healthScore"] == 75.5
        assert d["diskUsed"] == 100_000_000_000
        assert d["diskFreePercent"] == 80.0


class TestTrendRecorder:
    """Tests for TrendRecorder class."""

    def test_init_creates_db(self, tmp_path: Path):
        """Database is created on init."""
        db_path = tmp_path / "new_trends.db"
        assert not db_path.exists()

        TrendRecorder(db_path=db_path)

        assert db_path.exists()

    def test_record_snapshot(self, recorder: TrendRecorder):
        """Recording creates valid data point."""
        point = recorder.record_snapshot()

        assert 0 <= point.health_score <= 100
        assert point.disk_total > 0
        assert point.disk_used > 0
        assert point.disk_used <= point.disk_total
        assert 0 <= point.disk_free_percent <= 100
        assert point.timestamp.endswith("Z")

    def test_get_latest_empty(self, recorder: TrendRecorder):
        """Getting latest from empty DB returns empty list."""
        result = recorder.get_latest(10)
        assert result == []

    def test_get_latest(self, populated_recorder: TrendRecorder):
        """Getting latest returns most recent points."""
        result = populated_recorder.get_latest(5)

        assert len(result) == 5
        # Should be newest first
        timestamps = [p.timestamp for p in result]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_days(self, populated_recorder: TrendRecorder):
        """Getting by days returns correct range."""
        result = populated_recorder.get_days(7)

        # All results should be within last 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        for point in result:
            ts = datetime.fromisoformat(point.timestamp.replace("Z", ""))
            assert ts >= cutoff

    def test_get_range(self, populated_recorder: TrendRecorder):
        """Range query returns correct data."""
        end = datetime.utcnow()
        start = end - timedelta(days=5)

        result = populated_recorder.get_range(start, end)

        # Results should be in chronological order
        assert len(result) > 0
        timestamps = [p.timestamp for p in result]
        assert timestamps == sorted(timestamps)

    def test_stats_empty(self, recorder: TrendRecorder):
        """Stats on empty DB."""
        stats = recorder.stats()

        assert stats["row_count"] == 0
        assert stats["oldest"] is None
        assert stats["newest"] is None
        assert stats["db_size_bytes"] > 0  # DB file exists

    def test_stats_with_data(self, populated_recorder: TrendRecorder):
        """Stats with data."""
        stats = populated_recorder.stats()

        assert stats["row_count"] == 20
        assert stats["oldest"] is not None
        assert stats["newest"] is not None
        assert stats["db_size_bytes"] > 0

    def test_should_record_empty_db(self, recorder: TrendRecorder):
        """Should record if DB is empty."""
        assert recorder.should_record() is True

    def test_should_record_recent(self, recorder: TrendRecorder):
        """Should not record if recent snapshot exists."""
        recorder.record_snapshot()
        assert recorder.should_record(min_hours=4.0) is False

    def test_compact_removes_old_high_res(self, tmp_path: Path):
        """Compaction removes high-res data older than 7 days."""
        recorder = TrendRecorder(db_path=tmp_path / "test.db")

        # Insert old high-res data (10 days ago)
        old_time = datetime.utcnow() - timedelta(days=10)
        old_point = TrendDataPoint(
            timestamp=old_time.isoformat() + "Z",
            health_score=70,
            disk_used=100_000_000_000,
            disk_total=500_000_000_000,
            disk_free_percent=80,
            cache_size=5_000_000_000,
            trash_size=1_000_000_000,
            log_size=500_000_000,
        )
        recorder._store(old_point, resolution="high")

        # Insert recent high-res data
        recorder.record_snapshot()

        # Verify we have 2 rows
        assert recorder.stats()["row_count"] == 2

        # Run compaction
        removed = recorder.compact()

        # Old high-res should be removed
        assert removed == 1
        assert recorder.stats()["row_count"] == 1

    def test_compact_keeps_monthly(self, tmp_path: Path):
        """Compaction keeps monthly data indefinitely."""
        recorder = TrendRecorder(db_path=tmp_path / "test.db")

        # Insert old monthly data (2 years ago)
        old_time = datetime.utcnow() - timedelta(days=730)
        old_point = TrendDataPoint(
            timestamp=old_time.isoformat() + "Z",
            health_score=70,
            disk_used=100_000_000_000,
            disk_total=500_000_000_000,
            disk_free_percent=80,
            cache_size=5_000_000_000,
            trash_size=1_000_000_000,
            log_size=500_000_000,
        )
        recorder._store(old_point, resolution="monthly")

        # Run compaction
        removed = recorder.compact()

        # Monthly should be kept
        assert removed == 0
        assert recorder.stats()["row_count"] == 1


class TestMultipleSnapshots:
    """Tests for recording multiple snapshots."""

    def test_multiple_snapshots_stored(self, recorder: TrendRecorder):
        """Multiple snapshots are all stored."""
        for _ in range(5):
            recorder.record_snapshot()

        assert recorder.stats()["row_count"] == 5

    def test_health_scores_vary(self, recorder: TrendRecorder):
        """Health scores can vary between snapshots."""
        point1 = recorder.record_snapshot()
        point2 = recorder.record_snapshot()

        # Both should be valid
        assert 0 <= point1.health_score <= 100
        assert 0 <= point2.health_score <= 100
