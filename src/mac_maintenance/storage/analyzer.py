"""
Storage analysis module.

Provides tools for analyzing disk usage, identifying large files,
and categorizing storage by file type.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
import fnmatch


@dataclass
class FileEntry:
    """Represents a single file or directory."""

    path: Path
    size: int  # Size in bytes
    is_dir: bool
    depth: int = 0  # Depth from root

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size / (1024 * 1024 * 1024)


@dataclass
class AnalysisResult:
    """Results from storage analysis."""

    root_path: Path
    total_size: int  # Total size in bytes
    file_count: int
    dir_count: int
    entries: List[FileEntry] = field(default_factory=list)
    category_sizes: Dict[str, int] = field(default_factory=dict)

    @property
    def total_size_gb(self) -> float:
        """Total size in gigabytes."""
        return self.total_size / (1024 * 1024 * 1024)

    def get_largest_entries(self, n: int = 10) -> List[FileEntry]:
        """
        Get the N largest entries.

        Args:
            n: Number of entries to return

        Returns:
            List of largest entries sorted by size descending
        """
        return sorted(self.entries, key=lambda e: e.size, reverse=True)[:n]

    def get_entries_by_category(self, category: str) -> List[FileEntry]:
        """
        Get all entries for a specific category.

        Args:
            category: Category name (e.g., "images", "videos")

        Returns:
            List of entries in that category
        """
        patterns = CATEGORY_PATTERNS.get(category, [])
        if not patterns:
            return []

        result = []
        for entry in self.entries:
            if any(fnmatch.fnmatch(entry.path.name.lower(), pattern) for pattern in patterns):
                result.append(entry)
        return result


# File categorization patterns
CATEGORY_PATTERNS = {
    "images": ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.svg", "*.webp"],
    "videos": ["*.mp4", "*.mov", "*.avi", "*.mkv", "*.flv", "*.wmv", "*.m4v"],
    "audio": ["*.mp3", "*.m4a", "*.flac", "*.wav", "*.aac", "*.ogg", "*.wma"],
    "documents": [
        "*.pdf",
        "*.doc",
        "*.docx",
        "*.xls",
        "*.xlsx",
        "*.ppt",
        "*.pptx",
        "*.pages",
        "*.numbers",
        "*.key",
    ],
    "archives": ["*.zip", "*.tar", "*.gz", "*.bz2", "*.7z", "*.rar", "*.dmg", "*.pkg"],
    "code": [
        "*.py",
        "*.js",
        "*.ts",
        "*.java",
        "*.c",
        "*.cpp",
        "*.h",
        "*.sh",
        "*.go",
        "*.rs",
    ],
}


class DiskAnalyzer:
    """
    Analyzes disk usage for a given path.

    Example:
        >>> analyzer = DiskAnalyzer(Path.home())
        >>> result = analyzer.analyze()
        >>> print(f"Total size: {result.total_size_gb:.2f} GB")
    """

    def __init__(
        self,
        root_path: Path,
        exclude_patterns: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            root_path: Path to analyze
            exclude_patterns: List of glob patterns to exclude
            max_depth: Maximum depth to traverse (None = unlimited)
        """
        self.root_path = Path(root_path).resolve()
        self.exclude_patterns = exclude_patterns or []
        self.max_depth = max_depth

        # Add common exclusions
        self.exclude_patterns.extend(
            [
                ".git",
                ".venv",
                "venv",
                "node_modules",
                "__pycache__",
                ".cache",
                ".Trash",
            ]
        )

    def analyze(self) -> AnalysisResult:
        """
        Perform the storage analysis.

        Returns:
            AnalysisResult with findings

        Raises:
            FileNotFoundError: If root_path doesn't exist
            PermissionError: If root_path is not readable
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Path does not exist: {self.root_path}")

        if not os.access(self.root_path, os.R_OK):
            raise PermissionError(f"Path is not readable: {self.root_path}")

        entries: List[FileEntry] = []
        total_size = 0
        file_count = 0
        dir_count = 0
        category_sizes: Dict[str, int] = {cat: 0 for cat in CATEGORY_PATTERNS.keys()}

        for entry in self._walk_directory(self.root_path, 0):
            entries.append(entry)
            total_size += entry.size

            if entry.is_dir:
                dir_count += 1
            else:
                file_count += 1

                # Categorize files
                for category, patterns in CATEGORY_PATTERNS.items():
                    if any(
                        fnmatch.fnmatch(entry.path.name.lower(), pattern)
                        for pattern in patterns
                    ):
                        category_sizes[category] += entry.size
                        break

        return AnalysisResult(
            root_path=self.root_path,
            total_size=total_size,
            file_count=file_count,
            dir_count=dir_count,
            entries=entries,
            category_sizes=category_sizes,
        )

    def _walk_directory(self, path: Path, depth: int):
        """
        Recursively walk directory tree.

        Args:
            path: Current path to walk
            depth: Current depth from root

        Yields:
            FileEntry objects for each file/directory
        """
        if self.max_depth is not None and depth > self.max_depth:
            return

        try:
            for item in path.iterdir():
                # Check exclusions
                if self._is_excluded(item):
                    continue

                try:
                    if item.is_symlink():
                        # Skip symlinks to avoid loops
                        continue

                    size = self._get_size(item)

                    entry = FileEntry(
                        path=item,
                        size=size,
                        is_dir=item.is_dir(),
                        depth=depth,
                    )

                    yield entry

                    # Recurse into directories
                    if item.is_dir():
                        yield from self._walk_directory(item, depth + 1)

                except (PermissionError, OSError):
                    # Skip files/dirs we can't access
                    continue

        except (PermissionError, OSError):
            # Can't read directory
            return

    def _get_size(self, path: Path) -> int:
        """
        Get size of a file or directory.

        For directories, this returns the size of the directory entry itself,
        not the total size of contents (that's calculated during traversal).

        Args:
            path: Path to check

        Returns:
            Size in bytes
        """
        try:
            return path.stat().st_size
        except (OSError, PermissionError):
            return 0

    def _is_excluded(self, path: Path) -> bool:
        """
        Check if path matches any exclusion pattern.

        Args:
            path: Path to check

        Returns:
            True if should be excluded
        """
        name = path.name
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.exclude_patterns)
