"""
Tests for DuplicateScanner - duplicate file finder backend.

TDD: Tests written before implementation.
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

from upkeep.core.duplicate_scanner import (
    DuplicateGroup,
    DuplicateScanner,
    FileInfo,
    HashAlgorithm,
    ScanConfig,
    ScanResult,
)


class TestDataClasses:
    """Test dataclass structures."""

    def test_file_info_creation(self):
        """FileInfo holds file metadata."""
        info = FileInfo(path=Path("/test/file.txt"), size_bytes=1000)
        assert info.path == Path("/test/file.txt")
        assert info.size_bytes == 1000
        assert info.partial_hash is None
        assert info.full_hash is None

    def test_duplicate_group_potential_savings(self):
        """DuplicateGroup calculates potential space savings."""
        files = [
            FileInfo(path=Path("/a/file.txt"), size_bytes=1000),
            FileInfo(path=Path("/b/file.txt"), size_bytes=1000),
            FileInfo(path=Path("/c/file.txt"), size_bytes=1000),
        ]
        group = DuplicateGroup(hash="abc123", size_bytes=1000, files=files)

        # 3 files @ 1000 bytes each = 2000 bytes recoverable (keep 1)
        assert group.potential_savings == 2000

    def test_scan_config_defaults(self):
        """ScanConfig has sensible defaults."""
        config = ScanConfig(paths=[Path("/test")])
        assert config.min_size_bytes == 1024  # 1KB
        assert config.max_size_bytes is None
        assert config.include_hidden is False
        assert config.follow_symlinks is False
        assert config.hash_algorithm == HashAlgorithm.SHA256


class TestDuplicateScannerInit:
    """Test scanner initialization."""

    def test_scanner_init_with_config(self):
        """Scanner initializes with ScanConfig."""
        config = ScanConfig(
            paths=[Path("/test")],
            min_size_bytes=2048,
            include_hidden=True,
        )
        scanner = DuplicateScanner(config)
        assert scanner.config.min_size_bytes == 2048
        assert scanner.config.include_hidden is True


class TestSizeGrouping:
    """Test Stage 1: Size grouping."""

    def test_groups_files_by_size(self):
        """Scanner groups files with identical sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with same size
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file3 = Path(tmpdir) / "unique.txt"

            file1.write_text("hello")  # 5 bytes
            file2.write_text("world")  # 5 bytes
            file3.write_text("different content here")  # different size

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            size_groups = scanner._group_by_size()

            # Should have at least one group with 2 files (5-byte files)
            five_byte_group = size_groups.get(5, [])
            assert len(five_byte_group) == 2

    def test_skips_files_below_min_size(self):
        """Scanner ignores files smaller than min_size_bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            small_file = Path(tmpdir) / "small.txt"
            small_file.write_text("hi")  # 2 bytes

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=100)
            scanner = DuplicateScanner(config)
            size_groups = scanner._group_by_size()

            # 2-byte file should be excluded
            assert 2 not in size_groups


class TestPartialHashing:
    """Test Stage 2: Partial hash (first 64KB)."""

    def test_partial_hash_groups_same_prefix(self):
        """Files with same first 64KB get grouped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Two files with same content
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            content = "x" * 1000  # 1KB of x's
            file1.write_text(content)
            file2.write_text(content)

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)

            # Mock size groups
            files = [
                FileInfo(path=file1, size_bytes=1000),
                FileInfo(path=file2, size_bytes=1000),
            ]
            partial_groups = scanner._group_by_partial_hash({1000: files})

            # Both files should be in the same partial hash group
            assert len(partial_groups) == 1
            group_files = list(partial_groups.values())[0]
            assert len(group_files) == 2

    def test_partial_hash_filters_different_content(self):
        """Files with different content get filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("x" * 1000)
            file2.write_text("y" * 1000)  # Same size, different content

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)

            files = [
                FileInfo(path=file1, size_bytes=1000),
                FileInfo(path=file2, size_bytes=1000),
            ]
            partial_groups = scanner._group_by_partial_hash({1000: files})

            # Each file should have unique partial hash, so no groups
            # (groups with only 1 file are filtered out)
            groups_with_multiples = {k: v for k, v in partial_groups.items() if len(v) > 1}
            assert len(groups_with_multiples) == 0


class TestFullHashing:
    """Test Stage 3: Full hash verification."""

    def test_full_hash_confirms_duplicates(self):
        """Full hash confirms files are truly identical."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            content = "identical content here"
            file1.write_text(content)
            file2.write_text(content)

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)

            files = [
                FileInfo(path=file1, size_bytes=len(content)),
                FileInfo(path=file2, size_bytes=len(content)),
            ]
            full_groups = scanner._group_by_full_hash({"partial": files})

            # Should have 1 group with 2 confirmed duplicates
            assert len(full_groups) == 1
            group = list(full_groups.values())[0]
            assert len(group) == 2


class TestFullScan:
    """Test complete scan pipeline."""

    def test_full_scan_finds_duplicates(self):
        """Full scan identifies duplicate files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 2 identical files
            file1 = Path(tmpdir) / "original.txt"
            file2 = Path(tmpdir) / "copy.txt"
            content = "This is duplicate content for testing"
            file1.write_text(content)
            file2.write_text(content)

            # Create 1 unique file
            unique = Path(tmpdir) / "unique.txt"
            unique.write_text("This is unique")

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            assert isinstance(result, ScanResult)
            assert len(result.duplicate_groups) == 1
            assert result.duplicate_groups[0].files[0].size_bytes == len(content)
            assert result.total_duplicates == 2

    def test_scan_returns_empty_when_no_duplicates(self):
        """Scan returns empty result when no duplicates exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                f = Path(tmpdir) / f"file{i}.txt"
                f.write_text(f"unique content {i}")

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            assert len(result.duplicate_groups) == 0
            assert result.total_duplicates == 0

    def test_scan_reports_progress(self):
        """Scan calls progress callback with stage info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file1.write_text("content")

            progress_calls = []

            def progress_callback(stage: str, current: int, total: int):
                progress_calls.append((stage, current, total))

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            scanner.scan(progress_callback=progress_callback)

            # Should have received progress updates
            assert len(progress_calls) > 0
            stages = [call[0] for call in progress_calls]
            assert "size_grouping" in stages or "scanning" in stages

    def test_scan_calculates_wasted_bytes(self):
        """Scan calculates total wasted space."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "x" * 1000  # 1000 bytes
            for name in ["a.txt", "b.txt", "c.txt"]:
                (Path(tmpdir) / name).write_text(content)

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            # 3 copies of 1000 bytes = 2000 bytes wasted (keep 1)
            assert result.total_wasted_bytes == 2000


class TestExcludePatterns:
    """Test file exclusion patterns."""

    def test_excludes_hidden_files_by_default(self):
        """Hidden files (dotfiles) excluded by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            visible = Path(tmpdir) / "visible.txt"
            hidden = Path(tmpdir) / ".hidden.txt"
            content = "duplicate"
            visible.write_text(content)
            hidden.write_text(content)

            config = ScanConfig(
                paths=[Path(tmpdir)],
                min_size_bytes=0,
                include_hidden=False,  # default
            )
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            # Should NOT find duplicates (hidden file excluded)
            assert len(result.duplicate_groups) == 0

    def test_includes_hidden_when_configured(self):
        """Hidden files included when include_hidden=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            visible = Path(tmpdir) / "visible.txt"
            hidden = Path(tmpdir) / ".hidden.txt"
            content = "duplicate content"
            visible.write_text(content)
            hidden.write_text(content)

            config = ScanConfig(
                paths=[Path(tmpdir)],
                min_size_bytes=0,
                include_hidden=True,
            )
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            # Should find duplicates (hidden file included)
            assert len(result.duplicate_groups) == 1

    def test_excludes_patterns(self):
        """Files matching exclude patterns are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normal = Path(tmpdir) / "normal.txt"
            git_file = Path(tmpdir) / ".git" / "objects" / "abc"
            git_file.parent.mkdir(parents=True)
            content = "duplicate"
            normal.write_text(content)
            git_file.write_text(content)

            config = ScanConfig(
                paths=[Path(tmpdir)],
                min_size_bytes=0,
                include_hidden=True,  # Include hidden, but exclude .git/*
                exclude_patterns=[".git/*"],
            )
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            # .git file should be excluded even though include_hidden=True
            assert len(result.duplicate_groups) == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_handles_permission_errors(self):
        """Scanner gracefully handles permission denied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "readable.txt"
            file1.write_text("content")

            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)

            # Mock a permission error during hash computation
            with patch.object(scanner, "_compute_hash", side_effect=PermissionError("denied")):
                # First need files with same size to trigger hashing
                file2 = Path(tmpdir) / "file2.txt"
                file2.write_text("content")  # Same size as file1

                result = scanner.scan()
                # Should complete without crashing
                assert isinstance(result, ScanResult)
                assert len(result.errors) > 0

    def test_handles_missing_paths(self):
        """Scanner handles non-existent paths gracefully."""
        config = ScanConfig(paths=[Path("/nonexistent/path")], min_size_bytes=0)
        scanner = DuplicateScanner(config)
        result = scanner.scan()

        assert isinstance(result, ScanResult)
        assert len(result.errors) > 0 or result.total_files_scanned == 0

    def test_handles_empty_directory(self):
        """Scanner handles empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScanConfig(paths=[Path(tmpdir)], min_size_bytes=0)
            scanner = DuplicateScanner(config)
            result = scanner.scan()

            assert result.total_files_scanned == 0
            assert len(result.duplicate_groups) == 0


class TestHashAlgorithm:
    """Test different hash algorithms."""

    def test_sha256_hash(self):
        """SHA256 produces correct hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file.txt"
            content = "test content"
            file1.write_text(content)

            config = ScanConfig(
                paths=[Path(tmpdir)],
                hash_algorithm=HashAlgorithm.SHA256,
            )
            scanner = DuplicateScanner(config)
            computed = scanner._compute_hash(file1, full=True)

            expected = hashlib.sha256(content.encode()).hexdigest()
            assert computed == expected
