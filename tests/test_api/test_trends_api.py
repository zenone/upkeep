"""Tests for Trends API endpoints.

Tests the REST API for historical trend tracking:
- GET /api/trends
- POST /api/trends/record
- POST /api/trends/compact
- GET /api/trends/stats
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from upkeep.core.trend_recorder import TrendRecorder


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "test_trends.db"


@pytest.fixture
def recorder(temp_db: Path) -> TrendRecorder:
    """Create a TrendRecorder with temp database."""
    return TrendRecorder(db_path=temp_db)


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    """Create a test client with isolated TrendRecorder per test."""
    import upkeep.web.server as server_module

    # Create isolated temp DB for this test
    test_db = tmp_path / "test_trends.db"

    # Create a fresh recorder with temp DB
    test_recorder = TrendRecorder(db_path=test_db)

    # Reset and replace the global recorder
    old_recorder = server_module._trend_recorder
    server_module._trend_recorder = test_recorder

    try:
        yield TestClient(server_module.app)
    finally:
        # Restore original state
        server_module._trend_recorder = old_recorder


class TestGetTrends:
    """Tests for GET /api/trends endpoint."""

    def test_get_trends_empty_db(self, client: TestClient):
        """Empty database returns empty points list."""
        response = client.get("/api/trends")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert "stats" in data
        assert data["points"] == []

    def test_get_trends_with_data(self, client: TestClient):
        """Request with data returns points."""
        # Record some data first
        client.post("/api/trends/record")
        client.post("/api/trends/record")

        response = client.get("/api/trends")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert len(data["points"]) == 2

    def test_get_trends_custom_days(self, client: TestClient):
        """Can specify custom number of days."""
        response = client.get("/api/trends?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data

    def test_get_trends_with_resolution(self, client: TestClient):
        """Can filter by resolution."""
        response = client.get("/api/trends?resolution=daily")
        assert response.status_code == 200


class TestRecordSnapshot:
    """Tests for POST /api/trends/record endpoint."""

    def test_record_snapshot_creates_point(self, client: TestClient):
        """Recording creates a new data point."""
        response = client.post("/api/trends/record")
        assert response.status_code == 200
        data = response.json()
        assert "point" in data
        assert "message" in data

        point = data["point"]
        assert "timestamp" in point
        assert "healthScore" in point
        assert "diskUsed" in point
        assert "diskTotal" in point
        assert 0 <= point["healthScore"] <= 100

    def test_record_snapshot_persists(self, client: TestClient):
        """Recorded snapshot persists in database."""
        # Record a snapshot
        response = client.post("/api/trends/record")
        assert response.status_code == 200

        # Verify via stats endpoint
        stats_response = client.get("/api/trends/stats")
        assert stats_response.json()["row_count"] == 1


class TestCompact:
    """Tests for POST /api/trends/compact endpoint."""

    def test_compact_returns_stats(self, client: TestClient):
        """Compaction returns removed and remaining counts."""
        response = client.post("/api/trends/compact")
        assert response.status_code == 200
        data = response.json()
        assert "removed" in data
        assert "remaining" in data
        assert isinstance(data["removed"], int)
        assert isinstance(data["remaining"], int)


class TestGetStats:
    """Tests for GET /api/trends/stats endpoint."""

    def test_get_stats_empty_db(self, client: TestClient):
        """Stats on empty database."""
        response = client.get("/api/trends/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 0
        assert data["oldest"] is None
        assert data["newest"] is None
        assert data["db_size_bytes"] > 0  # DB file exists

    def test_get_stats_with_data(self, client: TestClient):
        """Stats with recorded data."""
        # Record some data
        client.post("/api/trends/record")
        client.post("/api/trends/record")

        response = client.get("/api/trends/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 2
        assert data["oldest"] is not None
        assert data["newest"] is not None
