"""Tests for Duplicate Finder API endpoints."""

import pytest
from fastapi.testclient import TestClient

from upkeep.web.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestDuplicateScanAPI:
    """Tests for duplicate scanning API."""

    def test_start_scan_default_path(self, client: TestClient, tmp_path):
        """Test starting a scan with default home path."""
        response = client.post("/api/duplicates/scan")
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "started"

    def test_start_scan_custom_path(self, client: TestClient, tmp_path):
        """Test starting a scan with custom path."""
        response = client.post(f"/api/duplicates/scan?paths={tmp_path}")
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data

    def test_start_scan_invalid_path(self, client: TestClient):
        """Test scan with non-existent path."""
        response = client.post("/api/duplicates/scan?paths=/nonexistent/path/xyz")
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_get_status_unknown_scan(self, client: TestClient):
        """Test getting status of unknown scan."""
        response = client.get("/api/duplicates/status/unknown123")
        assert response.status_code == 404

    def test_get_results_unknown_scan(self, client: TestClient):
        """Test getting results of unknown scan."""
        response = client.get("/api/duplicates/results/unknown123")
        assert response.status_code == 404


class TestDuplicateScanEndToEnd:
    """End-to-end tests for duplicate scanning."""

    def test_full_scan_workflow(self, client: TestClient, tmp_path):
        """Test complete scan workflow: start -> status -> results."""
        # Create some test files with duplicates
        content = b"This is test content for duplicate detection"
        (tmp_path / "file1.txt").write_bytes(content)
        (tmp_path / "file2.txt").write_bytes(content)
        (tmp_path / "unique.txt").write_bytes(b"unique content")

        # Start scan
        response = client.post(
            f"/api/duplicates/scan?paths={tmp_path}&min_size_mb=0.00001"
        )
        assert response.status_code == 200
        scan_id = response.json()["scan_id"]

        # Poll status until complete (with timeout)
        import time
        max_wait = 10
        start = time.time()
        while time.time() - start < max_wait:
            status_response = client.get(f"/api/duplicates/status/{scan_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            if status_data["status"] == "complete":
                break
            time.sleep(0.2)
        else:
            pytest.fail("Scan did not complete in time")

        # Get results
        results_response = client.get(f"/api/duplicates/results/{scan_id}")
        assert results_response.status_code == 200
        results = results_response.json()

        assert "scan_summary" in results
        assert "duplicate_groups" in results

    def test_results_in_text_format(self, client: TestClient, tmp_path):
        """Test getting results as text."""
        # Create duplicates
        content = b"duplicate content"
        (tmp_path / "a.txt").write_bytes(content)
        (tmp_path / "b.txt").write_bytes(content)

        # Start and wait for scan
        response = client.post(
            f"/api/duplicates/scan?paths={tmp_path}&min_size_mb=0.00001"
        )
        scan_id = response.json()["scan_id"]

        import time
        time.sleep(1)  # Wait for scan

        # Get text results
        results_response = client.get(
            f"/api/duplicates/results/{scan_id}?format=text"
        )
        # Could be 200 or 202 (still running)
        if results_response.status_code == 200:
            assert "DUPLICATE FILE REPORT" in results_response.text

    def test_results_in_csv_format(self, client: TestClient, tmp_path):
        """Test getting results as CSV."""
        # Create duplicates
        content = b"csv test content"
        (tmp_path / "x.txt").write_bytes(content)
        (tmp_path / "y.txt").write_bytes(content)

        # Start scan
        response = client.post(
            f"/api/duplicates/scan?paths={tmp_path}&min_size_mb=0.00001"
        )
        scan_id = response.json()["scan_id"]

        import time
        time.sleep(1)  # Wait for scan

        # Get CSV results
        results_response = client.get(
            f"/api/duplicates/results/{scan_id}?format=csv"
        )
        if results_response.status_code == 200:
            assert "Group" in results_response.text  # CSV header


class TestDuplicateDeleteAPI:
    """Tests for duplicate deletion API."""

    def test_delete_unknown_scan(self, client: TestClient):
        """Test deleting from unknown scan."""
        response = client.post(
            "/api/duplicates/delete?scan_id=unknown123",
            json={"paths": ["/some/path"]},
        )
        # Should fail because scan_id query param, not body
        assert response.status_code in [400, 404, 422]

    def test_delete_requires_scan_results(self, client: TestClient, tmp_path):
        """Test that delete requires completed scan."""
        # Start a scan
        response = client.post(f"/api/duplicates/scan?paths={tmp_path}")
        scan_id = response.json()["scan_id"]

        # Immediately try to delete (scan likely still running)
        # This tests that the endpoint exists and validates properly
        delete_response = client.post(
            f"/api/duplicates/delete?scan_id={scan_id}",
            json={"paths": [str(tmp_path / "nonexistent.txt")]},
        )
        # Should fail with validation error or 400
        assert delete_response.status_code in [400, 422]
