"""
Tests for storage.analyzer module.
"""

from pathlib import Path

import pytest

from upkeep.storage.analyzer import (
    CATEGORY_PATTERNS,
    AnalysisResult,
    DiskAnalyzer,
    FileEntry,
)


class TestFileEntry:
    """Tests for FileEntry dataclass."""

    def test_file_entry_creation(self) -> None:
        """Test creating a FileEntry."""
        entry = FileEntry(
            path=Path("/test/file.txt"),
            size=1024 * 1024,  # 1 MB
            is_dir=False,
            depth=1,
        )

        assert entry.path == Path("/test/file.txt")
        assert entry.size == 1024 * 1024
        assert entry.is_dir is False
        assert entry.depth == 1
        assert entry.size_mb == 1.0
        assert entry.size_gb == pytest.approx(0.0009765625, abs=0.0001)


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_creation(self, temp_dir: Path) -> None:
        """Test creating an AnalysisResult."""
        entries = [
            FileEntry(temp_dir / "file1.txt", 1000, False, 0),
            FileEntry(temp_dir / "file2.txt", 2000, False, 0),
            FileEntry(temp_dir / "subdir", 500, True, 0),
        ]

        result = AnalysisResult(
            root_path=temp_dir,
            total_size=3500,
            file_count=2,
            dir_count=1,
            entries=entries,
        )

        assert result.root_path == temp_dir
        assert result.total_size == 3500
        assert result.file_count == 2
        assert result.dir_count == 1
        assert len(result.entries) == 3

    def test_get_largest_entries(self, temp_dir: Path) -> None:
        """Test getting largest entries."""
        entries = [
            FileEntry(temp_dir / "small.txt", 100, False, 0),
            FileEntry(temp_dir / "large.txt", 1000, False, 0),
            FileEntry(temp_dir / "medium.txt", 500, False, 0),
        ]

        result = AnalysisResult(
            root_path=temp_dir,
            total_size=1600,
            file_count=3,
            dir_count=0,
            entries=entries,
        )

        largest = result.get_largest_entries(2)
        assert len(largest) == 2
        assert largest[0].size == 1000
        assert largest[1].size == 500


class TestDiskAnalyzer:
    """Tests for DiskAnalyzer class."""

    def test_analyzer_initialization(self, temp_dir: Path) -> None:
        """Test creating a DiskAnalyzer."""
        analyzer = DiskAnalyzer(temp_dir)

        # resolve() is used internally, so compare resolved paths
        assert analyzer.root_path == temp_dir.resolve()
        assert isinstance(analyzer.exclude_patterns, list)
        assert analyzer.max_depth is None

    def test_analyzer_with_options(self, temp_dir: Path) -> None:
        """Test analyzer with custom options."""
        analyzer = DiskAnalyzer(
            temp_dir,
            exclude_patterns=["*.tmp"],
            max_depth=2,
        )

        assert "*.tmp" in analyzer.exclude_patterns
        assert analyzer.max_depth == 2

    def test_analyze_sample_directory(self, sample_directory: Path) -> None:
        """Test analyzing a sample directory structure."""
        analyzer = DiskAnalyzer(sample_directory)
        result = analyzer.analyze()

        assert result.root_path == sample_directory.resolve()
        assert result.total_size > 0
        assert result.file_count >= 4  # 4 files in sample_directory fixture
        assert result.dir_count >= 2  # 2 subdirs in sample_directory fixture
        assert len(result.entries) > 0

    def test_analyze_nonexistent_path(self, temp_dir: Path) -> None:
        """Test analyzing a path that doesn't exist."""
        nonexistent = temp_dir / "does_not_exist"
        analyzer = DiskAnalyzer(nonexistent)

        with pytest.raises(FileNotFoundError):
            analyzer.analyze()

    def test_exclusion_patterns(self, temp_dir: Path) -> None:
        """Test that exclusion patterns work."""
        # Create test files
        (temp_dir / "keep.txt").write_text("keep this")
        (temp_dir / "exclude.tmp").write_text("exclude this")

        analyzer = DiskAnalyzer(temp_dir, exclude_patterns=["*.tmp"])
        result = analyzer.analyze()

        # Check that .tmp file was excluded
        paths = [e.path.name for e in result.entries]
        assert "keep.txt" in paths
        assert "exclude.tmp" not in paths

    def test_max_depth_limit(self, temp_dir: Path) -> None:
        """Test max_depth limiting."""
        # Create nested structure
        (temp_dir / "level1").mkdir()
        (temp_dir / "level1" / "level2").mkdir()
        (temp_dir / "level1" / "level2" / "deep.txt").write_text("deep")

        analyzer = DiskAnalyzer(temp_dir, max_depth=0)
        result = analyzer.analyze()

        # At depth 0, should see level1 directory but not recurse into it
        paths = [str(e.path) for e in result.entries]
        assert any("level1" in p for p in paths)
        # Should not see level2 or deep.txt (they're at depth >= 1)
        assert not any("level2" in p for p in paths)
        assert not any("deep.txt" in p for p in paths)

    def test_categorization(self, temp_dir: Path) -> None:
        """Test file categorization."""
        # Create files of different categories
        (temp_dir / "photo.jpg").write_text("image data")
        (temp_dir / "video.mp4").write_text("video data")
        (temp_dir / "document.pdf").write_text("doc data")

        analyzer = DiskAnalyzer(temp_dir)
        result = analyzer.analyze()

        # Check categories are populated
        assert result.category_sizes["images"] > 0
        assert result.category_sizes["videos"] > 0
        assert result.category_sizes["documents"] > 0

    def test_category_patterns_defined(self) -> None:
        """Test that category patterns are properly defined."""
        assert "images" in CATEGORY_PATTERNS
        assert "videos" in CATEGORY_PATTERNS
        assert "audio" in CATEGORY_PATTERNS
        assert "documents" in CATEGORY_PATTERNS
        assert "archives" in CATEGORY_PATTERNS
        assert "code" in CATEGORY_PATTERNS

        # Check some patterns
        assert "*.jpg" in CATEGORY_PATTERNS["images"]
        assert "*.mp4" in CATEGORY_PATTERNS["videos"]
        assert "*.pdf" in CATEGORY_PATTERNS["documents"]
