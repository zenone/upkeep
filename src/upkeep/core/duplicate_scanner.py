"""
Duplicate Scanner - Find duplicate files safely and efficiently.

Uses a multi-stage filtering pipeline to minimize I/O:
1. Size grouping (eliminates ~80-90% of files)
2. Partial hash (first 64KB)
3. Full hash (SHA-256 confirmation)

Safe by default: identifies duplicates, never auto-deletes.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class HashAlgorithm(Enum):
    """Supported hash algorithms."""

    SHA256 = "sha256"
    XXHASH = "xxhash64"  # Not implemented yet, fallback to SHA256


# Size of partial hash read (64KB)
PARTIAL_HASH_SIZE = 65536


@dataclass
class FileInfo:
    """Metadata for a scanned file."""

    path: Path
    size_bytes: int
    partial_hash: str | None = None
    full_hash: str | None = None
    mtime: float = 0.0


@dataclass
class DuplicateGroup:
    """A group of duplicate files."""

    hash: str
    size_bytes: int
    files: list[FileInfo]

    @property
    def potential_savings(self) -> int:
        """Calculate space recoverable if all but one copy removed."""
        return self.size_bytes * (len(self.files) - 1)


@dataclass
class ScanConfig:
    """Configuration for duplicate scanning."""

    paths: list[Path]
    min_size_bytes: int = 1024  # 1KB minimum
    max_size_bytes: int | None = None
    include_hidden: bool = False
    follow_symlinks: bool = False
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "*.app/*",
            "node_modules/*",
            ".git/*",
            "*.vmdk",
            "*.iso",
        ]
    )
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256


@dataclass
class ScanResult:
    """Result of a duplicate scan."""

    duplicate_groups: list[DuplicateGroup]
    total_files_scanned: int
    total_duplicates: int
    total_wasted_bytes: int
    scan_duration_seconds: float
    errors: list[str]


class DuplicateScanner:
    """
    Scans directories for duplicate files using multi-stage filtering.

    Pipeline:
    1. Size grouping - files must have identical sizes
    2. Partial hash - first 64KB must match
    3. Full hash - entire file content must match
    """

    def __init__(self, config: ScanConfig) -> None:
        """
        Initialize scanner with configuration.

        Args:
            config: Scan configuration (paths, filters, options).
        """
        self.config = config
        self._errors: list[str] = []

    def scan(
        self,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> ScanResult:
        """
        Execute full scan pipeline.

        Args:
            progress_callback: Optional callback (stage, current, total).

        Returns:
            ScanResult with duplicate groups and statistics.
        """
        start_time = time.time()
        self._errors = []

        # Stage 1: Group by size
        if progress_callback:
            progress_callback("scanning", 0, 0)

        size_groups = self._group_by_size()

        if progress_callback:
            progress_callback("size_grouping", len(size_groups), len(size_groups))

        # Filter to only groups with potential duplicates (2+ files same size)
        potential_duplicates = {
            size: files for size, files in size_groups.items() if len(files) > 1
        }

        total_files = sum(len(files) for files in size_groups.values())

        if not potential_duplicates:
            return ScanResult(
                duplicate_groups=[],
                total_files_scanned=total_files,
                total_duplicates=0,
                total_wasted_bytes=0,
                scan_duration_seconds=time.time() - start_time,
                errors=self._errors,
            )

        # Stage 2: Partial hash
        if progress_callback:
            progress_callback("partial_hashing", 0, len(potential_duplicates))

        partial_groups = self._group_by_partial_hash(potential_duplicates)

        if progress_callback:
            progress_callback("partial_hashing", len(partial_groups), len(partial_groups))

        # Filter to only groups with 2+ files
        partial_with_dupes = {k: v for k, v in partial_groups.items() if len(v) > 1}

        # Stage 3: Full hash
        if progress_callback:
            progress_callback("full_hashing", 0, len(partial_with_dupes))

        full_groups = self._group_by_full_hash(partial_with_dupes)

        if progress_callback:
            progress_callback("full_hashing", len(full_groups), len(full_groups))

        # Build DuplicateGroup objects
        duplicate_groups: list[DuplicateGroup] = []
        total_wasted = 0
        total_duplicates = 0

        for hash_key, files in full_groups.items():
            if len(files) > 1:
                size = files[0].size_bytes
                group = DuplicateGroup(hash=hash_key, size_bytes=size, files=files)
                duplicate_groups.append(group)
                total_wasted += group.potential_savings
                total_duplicates += len(files)

        # Sort by potential savings (largest first)
        duplicate_groups.sort(key=lambda g: g.potential_savings, reverse=True)

        return ScanResult(
            duplicate_groups=duplicate_groups,
            total_files_scanned=total_files,
            total_duplicates=total_duplicates,
            total_wasted_bytes=total_wasted,
            scan_duration_seconds=time.time() - start_time,
            errors=self._errors,
        )

    def _group_by_size(self) -> dict[int, list[FileInfo]]:
        """
        Stage 1: Group all files by size.

        Returns:
            Dict mapping file size to list of FileInfo objects.
        """
        size_groups: dict[int, list[FileInfo]] = defaultdict(list)

        for scan_path in self.config.paths:
            if not scan_path.exists():
                self._errors.append(f"Path does not exist: {scan_path}")
                continue

            try:
                self._scan_directory(scan_path, size_groups)
            except PermissionError as e:
                self._errors.append(f"Permission denied: {scan_path} - {e}")
            except OSError as e:
                self._errors.append(f"Error scanning {scan_path}: {e}")

        return dict(size_groups)

    def _scan_directory(
        self,
        directory: Path,
        size_groups: dict[int, list[FileInfo]],
    ) -> None:
        """
        Recursively scan a directory, adding files to size groups.

        Args:
            directory: Directory to scan.
            size_groups: Dict to populate with results.
        """
        try:
            entries = list(os.scandir(directory))
        except PermissionError:
            self._errors.append(f"Permission denied: {directory}")
            return
        except OSError as e:
            self._errors.append(f"Error reading {directory}: {e}")
            return

        for entry in entries:
            try:
                path = Path(entry.path)

                # Skip symlinks unless configured
                if entry.is_symlink() and not self.config.follow_symlinks:
                    continue

                # Skip hidden files unless configured
                if entry.name.startswith(".") and not self.config.include_hidden:
                    continue

                # Check exclude patterns
                if self._matches_exclude_pattern(path):
                    continue

                if entry.is_dir(follow_symlinks=self.config.follow_symlinks):
                    self._scan_directory(path, size_groups)
                elif entry.is_file(follow_symlinks=self.config.follow_symlinks):
                    stat = entry.stat(follow_symlinks=self.config.follow_symlinks)
                    size = stat.st_size

                    # Skip files outside size bounds
                    if size < self.config.min_size_bytes:
                        continue
                    if self.config.max_size_bytes is not None and size > self.config.max_size_bytes:
                        continue

                    file_info = FileInfo(
                        path=path,
                        size_bytes=size,
                        mtime=stat.st_mtime,
                    )
                    size_groups[size].append(file_info)

            except PermissionError:
                self._errors.append(f"Permission denied: {entry.path}")
            except OSError as e:
                self._errors.append(f"Error accessing {entry.path}: {e}")

    def _matches_exclude_pattern(self, path: Path) -> bool:
        """
        Check if path matches any exclude pattern.

        Args:
            path: File path to check.

        Returns:
            True if path should be excluded.
        """
        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(path_str, f"*/{pattern}") or fnmatch.fnmatch(path_str, pattern):
                return True
        return False

    def _group_by_partial_hash(
        self,
        size_groups: dict[int, list[FileInfo]],
    ) -> dict[str, list[FileInfo]]:
        """
        Stage 2: Group files by partial hash (first 64KB).

        Args:
            size_groups: Files grouped by size.

        Returns:
            Files grouped by partial hash.
        """
        partial_groups: dict[str, list[FileInfo]] = defaultdict(list)

        for _size, files in size_groups.items():
            for file_info in files:
                try:
                    partial_hash = self._compute_hash(file_info.path, full=False)
                    file_info.partial_hash = partial_hash
                    partial_groups[partial_hash].append(file_info)
                except (OSError, PermissionError) as e:
                    self._errors.append(f"Error hashing {file_info.path}: {e}")

        return dict(partial_groups)

    def _group_by_full_hash(
        self,
        partial_groups: dict[str, list[FileInfo]],
    ) -> dict[str, list[FileInfo]]:
        """
        Stage 3: Group files by full content hash.

        Args:
            partial_groups: Files grouped by partial hash.

        Returns:
            Files grouped by full hash (confirmed duplicates).
        """
        full_groups: dict[str, list[FileInfo]] = defaultdict(list)

        for _partial_hash, files in partial_groups.items():
            for file_info in files:
                try:
                    full_hash = self._compute_hash(file_info.path, full=True)
                    file_info.full_hash = full_hash
                    full_groups[full_hash].append(file_info)
                except (OSError, PermissionError) as e:
                    self._errors.append(f"Error hashing {file_info.path}: {e}")

        return dict(full_groups)

    def _compute_hash(self, path: Path, full: bool = False) -> str:
        """
        Compute hash of a file.

        Args:
            path: File to hash.
            full: If True, hash entire file. Otherwise, hash first 64KB.

        Returns:
            Hex digest of hash.
        """
        hasher = hashlib.sha256()

        with open(path, "rb") as f:
            if full:
                # Read in chunks to handle large files
                while chunk := f.read(65536):
                    hasher.update(chunk)
            else:
                # Only read first 64KB for partial hash
                chunk = f.read(PARTIAL_HASH_SIZE)
                hasher.update(chunk)

        return hasher.hexdigest()
