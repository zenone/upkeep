"""Tests for DuplicateReporter."""

import json
from pathlib import Path

import pytest

from upkeep.core.duplicate_reporter import DuplicateReporter, format_bytes
from upkeep.core.duplicate_scanner import (
    DuplicateGroup,
    FileInfo,
    ScanResult,
)


@pytest.fixture
def sample_scan_result() -> ScanResult:
    """Create a sample scan result for testing."""
    file1 = FileInfo(
        path=Path("/home/user/Documents/photo.jpg"),
        size_bytes=1024000,
        partial_hash="abc123",
        full_hash="abc123def456",
        mtime=1700000000.0,
    )
    file2 = FileInfo(
        path=Path("/home/user/Downloads/photo_copy.jpg"),
        size_bytes=1024000,
        partial_hash="abc123",
        full_hash="abc123def456",
        mtime=1700001000.0,
    )
    file3 = FileInfo(
        path=Path("/home/user/Backup/photo.jpg"),
        size_bytes=1024000,
        partial_hash="abc123",
        full_hash="abc123def456",
        mtime=1699999000.0,
    )

    group1 = DuplicateGroup(
        hash="abc123def456",
        size_bytes=1024000,
        files=[file1, file2, file3],
    )

    file4 = FileInfo(
        path=Path("/tmp/small.txt"),
        size_bytes=5000,
        full_hash="xyz789",
        mtime=1700002000.0,
    )
    file5 = FileInfo(
        path=Path("/tmp/small_copy.txt"),
        size_bytes=5000,
        full_hash="xyz789",
        mtime=1700003000.0,
    )

    group2 = DuplicateGroup(
        hash="xyz789",
        size_bytes=5000,
        files=[file4, file5],
    )

    return ScanResult(
        duplicate_groups=[group1, group2],  # group1 has more savings, should be first
        total_files_scanned=1000,
        total_duplicates=5,
        total_wasted_bytes=group1.potential_savings + group2.potential_savings,
        scan_duration_seconds=2.5,
        errors=["Permission denied: /root/secret"],
    )


@pytest.fixture
def empty_scan_result() -> ScanResult:
    """Create an empty scan result."""
    return ScanResult(
        duplicate_groups=[],
        total_files_scanned=500,
        total_duplicates=0,
        total_wasted_bytes=0,
        scan_duration_seconds=1.0,
        errors=[],
    )


class TestFormatBytes:
    """Tests for format_bytes helper function."""

    def test_bytes(self):
        """Test formatting small byte values."""
        assert format_bytes(0) == "0 B"
        assert format_bytes(100) == "100 B"
        assert format_bytes(1023) == "1023 B"

    def test_kilobytes(self):
        """Test formatting kilobyte values."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(5000) == "4.9 KB"
        assert format_bytes(1024 * 500) == "500.0 KB"

    def test_megabytes(self):
        """Test formatting megabyte values."""
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 50) == "50.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabyte values."""
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert format_bytes(1024 * 1024 * 1024 * 2.5) == "2.50 GB"


class TestDuplicateReporter:
    """Tests for DuplicateReporter class."""

    def test_to_json_structure(self, sample_scan_result: ScanResult):
        """Test JSON output has correct structure."""
        reporter = DuplicateReporter()
        json_str = reporter.to_json(sample_scan_result)
        data = json.loads(json_str)

        assert "scan_summary" in data
        assert "duplicate_groups" in data
        assert "errors" in data

        summary = data["scan_summary"]
        assert summary["total_files_scanned"] == 1000
        assert summary["total_duplicates"] == 5
        assert summary["duplicate_groups_count"] == 2

    def test_to_json_groups(self, sample_scan_result: ScanResult):
        """Test JSON duplicate groups contain expected fields."""
        reporter = DuplicateReporter()
        json_str = reporter.to_json(sample_scan_result)
        data = json.loads(json_str)

        groups = data["duplicate_groups"]
        assert len(groups) == 2

        # First group (larger)
        group1 = groups[0]
        assert "hash" in group1
        assert "full_hash" in group1
        assert "size_bytes" in group1
        assert "size_formatted" in group1
        assert "file_count" in group1
        assert "files" in group1
        assert len(group1["files"]) == 3

    def test_to_json_compact(self, sample_scan_result: ScanResult):
        """Test compact JSON output."""
        reporter = DuplicateReporter()
        compact = reporter.to_json(sample_scan_result, pretty=False)
        pretty = reporter.to_json(sample_scan_result, pretty=True)

        # Compact should be shorter
        assert len(compact) < len(pretty)
        # Both should be valid JSON
        assert json.loads(compact) == json.loads(pretty)

    def test_to_json_empty_result(self, empty_scan_result: ScanResult):
        """Test JSON output with no duplicates."""
        reporter = DuplicateReporter()
        json_str = reporter.to_json(empty_scan_result)
        data = json.loads(json_str)

        assert data["scan_summary"]["total_duplicates"] == 0
        assert data["duplicate_groups"] == []
        assert data["errors"] == []

    def test_to_text_contains_summary(self, sample_scan_result: ScanResult):
        """Test text output contains summary info."""
        reporter = DuplicateReporter()
        text = reporter.to_text(sample_scan_result)

        assert "DUPLICATE FILE REPORT" in text
        assert "1,000" in text  # formatted file count
        assert "2.5" in text  # scan duration

    def test_to_text_contains_groups(self, sample_scan_result: ScanResult):
        """Test text output contains duplicate groups."""
        reporter = DuplicateReporter()
        text = reporter.to_text(sample_scan_result)

        assert "Group 1:" in text
        assert "Group 2:" in text
        assert "photo.jpg" in text
        assert "small.txt" in text

    def test_to_text_contains_errors(self, sample_scan_result: ScanResult):
        """Test text output contains errors."""
        reporter = DuplicateReporter()
        text = reporter.to_text(sample_scan_result)

        assert "ERRORS" in text
        assert "Permission denied" in text

    def test_to_text_empty_result(self, empty_scan_result: ScanResult):
        """Test text output with no duplicates."""
        reporter = DuplicateReporter()
        text = reporter.to_text(empty_scan_result)

        assert "No duplicates found!" in text
        assert "🎉" in text

    def test_to_csv_header(self, sample_scan_result: ScanResult):
        """Test CSV output has correct header."""
        reporter = DuplicateReporter()
        csv_str = reporter.to_csv(sample_scan_result)
        lines = csv_str.strip().split("\n")

        header = lines[0]
        assert "Group" in header
        assert "Hash" in header
        assert "File Path" in header
        assert "Size" in header
        assert "Modified" in header

    def test_to_csv_row_count(self, sample_scan_result: ScanResult):
        """Test CSV has correct number of rows."""
        reporter = DuplicateReporter()
        csv_str = reporter.to_csv(sample_scan_result)
        lines = csv_str.strip().split("\n")

        # Header + 5 files = 6 lines
        assert len(lines) == 6

    def test_to_csv_empty_result(self, empty_scan_result: ScanResult):
        """Test CSV output with no duplicates."""
        reporter = DuplicateReporter()
        csv_str = reporter.to_csv(empty_scan_result)
        lines = csv_str.strip().split("\n")

        # Just header
        assert len(lines) == 1

    def test_summary(self, sample_scan_result: ScanResult):
        """Test summary output."""
        reporter = DuplicateReporter()
        summary = reporter.summary(sample_scan_result)

        assert summary["files_scanned"] == 1000
        assert summary["duplicates_found"] == 5
        assert summary["groups"] == 2
        assert "wasted_formatted" in summary
        assert "top_savings" in summary
        assert len(summary["top_savings"]) <= 5

    def test_summary_empty(self, empty_scan_result: ScanResult):
        """Test summary with empty result."""
        reporter = DuplicateReporter()
        summary = reporter.summary(empty_scan_result)

        assert summary["duplicates_found"] == 0
        assert summary["top_savings"] == []
