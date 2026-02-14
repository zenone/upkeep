"""
Tests for DiskScanner - disk usage visualization backend.
"""

import subprocess
from unittest.mock import MagicMock, patch

from upkeep.core.disk_scanner import DiskScanner


class TestDiskScanner:
    """Test suite for DiskScanner class."""

    def test_scanner_init(self):
        """Scanner initializes with default settings."""
        scanner = DiskScanner()
        assert scanner.max_depth == 3
        assert scanner.min_size_kb == 1024  # 1MB minimum

    def test_scanner_custom_settings(self):
        """Scanner accepts custom depth and min size."""
        scanner = DiskScanner(max_depth=5, min_size_kb=512)
        assert scanner.max_depth == 5
        assert scanner.min_size_kb == 512

    @patch("subprocess.run")
    def test_scan_parses_du_output(self, mock_run):
        """Scanner parses du output into hierarchical structure."""
        # Simulate du -k -d 2 output (kilobytes, depth 2)
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""1000\t/test/a
2000\t/test/b
500\t/test/a/sub1
300\t/test/a/sub2
3500\t/test
""",
            stderr="",
        )

        scanner = DiskScanner(max_depth=2, min_size_kb=0)
        result = scanner.scan("/test")

        assert result["name"] == "test"
        assert "children" in result
        # Should have 2 top-level children (a and b)
        names = [c["name"] for c in result["children"]]
        assert "a" in names
        assert "b" in names

    @patch("subprocess.run")
    def test_scan_filters_small_items(self, mock_run):
        """Scanner filters out items below min_size_kb."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""100\t/test/tiny
5000\t/test/big
5100\t/test
""",
            stderr="",
        )

        scanner = DiskScanner(max_depth=2, min_size_kb=1000)
        result = scanner.scan("/test")

        # Only "big" should be included (tiny is < 1000KB)
        child_names = [c["name"] for c in result.get("children", [])]
        assert "big" in child_names
        assert "tiny" not in child_names

    @patch("subprocess.run")
    def test_scan_handles_permission_denied(self, mock_run):
        """Scanner handles permission denied gracefully."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1000\t/test\n",
            stderr="du: /test/restricted: Permission denied\n",
        )

        scanner = DiskScanner()
        result = scanner.scan("/test")

        # Should still return valid result
        assert result["name"] == "test"
        # Should include warnings
        assert "warnings" in result
        assert len(result["warnings"]) > 0

    @patch("subprocess.run")
    def test_scan_error_returns_error_structure(self, mock_run):
        """Scanner returns error structure on complete failure."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        scanner = DiskScanner()
        result = scanner.scan("/nonexistent")

        assert "error" in result
        assert result["error"] is not None

    def test_format_size_human_readable(self):
        """Scanner formats sizes for human display."""
        scanner = DiskScanner()

        assert scanner.format_size(500) == "500 KB"
        assert scanner.format_size(1024) == "1.0 MB"
        assert scanner.format_size(1536) == "1.5 MB"
        assert scanner.format_size(1048576) == "1.0 GB"
        assert scanner.format_size(1572864) == "1.5 GB"

    @patch("subprocess.run")
    def test_scan_includes_metadata(self, mock_run):
        """Scanner includes useful metadata in response."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="5000\t/test\n",
            stderr="",
        )

        scanner = DiskScanner()
        result = scanner.scan("/test")

        assert "totalSize" in result
        assert "totalSizeFormatted" in result
        assert "path" in result
        assert result["path"] == "/test"

    @patch("subprocess.run")
    def test_scan_calculates_percentages(self, mock_run):
        """Scanner calculates percentage of parent for each item."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""2500\t/test/a
2500\t/test/b
5000\t/test
""",
            stderr="",
        )

        scanner = DiskScanner(max_depth=2, min_size_kb=0)
        result = scanner.scan("/test")

        # Each child should be ~50%
        for child in result.get("children", []):
            assert "percentage" in child
            assert 45 <= child["percentage"] <= 55  # Allow some rounding

    def test_build_tree_from_paths(self):
        """Internal tree builder creates proper hierarchy."""
        # Use min_size_kb=0 to include all entries
        scanner = DiskScanner(min_size_kb=0)

        entries = [
            ("/test/a/x", 100),
            ("/test/a/y", 200),
            ("/test/b", 300),
            ("/test/a", 300),
            ("/test", 600),
        ]

        tree = scanner._build_tree(entries, "/test")

        assert tree["name"] == "test"
        assert len(tree["children"]) == 2  # a and b
