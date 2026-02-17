"""
Disk Scanner - Backend for disk usage visualization.

Scans directory structure using `du` and produces hierarchical JSON
compatible with D3.js treemap/sunburst visualizations.
"""

from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


class DiskScanner:
    """Scans disk usage and produces visualization-ready hierarchical data."""

    def __init__(self, max_depth: int = 3, min_size_kb: int = 1024) -> None:
        """
        Initialize scanner.

        Args:
            max_depth: Maximum directory depth to scan (default 3).
            min_size_kb: Minimum size in KB to include in results (default 1024 = 1MB).
        """
        self.max_depth = max_depth
        self.min_size_kb = min_size_kb

    def scan(self, path: str) -> dict[str, Any]:
        """
        Scan directory and return hierarchical usage data.

        Args:
            path: Directory path to scan.

        Returns:
            Hierarchical dict with name, value (size), children, metadata.
        """
        try:
            result = subprocess.run(
                ["du", "-k", "-d", str(self.max_depth), path],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
            )
        except subprocess.SubprocessError as e:
            return {"name": Path(path).name, "error": str(e), "path": path}
        except OSError as e:
            return {"name": Path(path).name, "error": str(e), "path": path}

        # Parse warnings from stderr
        warnings = []
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                if line.strip():
                    warnings.append(line.strip())

        # Parse du output
        entries = self._parse_du_output(result.stdout)

        if not entries:
            return {
                "name": Path(path).name,
                "value": 0,
                "path": path,
                "error": "No data returned",
                "warnings": warnings,
            }

        # Build tree structure
        tree = self._build_tree(entries, path)

        # Add metadata
        total_size = entries[-1][1] if entries else 0  # Last entry is root total
        tree["totalSize"] = total_size
        tree["totalSizeFormatted"] = self.format_size(total_size)
        tree["path"] = path
        if warnings:
            tree["warnings"] = warnings

        # Calculate percentages
        self._add_percentages(tree, total_size)

        return tree

    def _parse_du_output(self, output: str) -> list[tuple[str, int]]:
        """
        Parse du output into list of (path, size_kb) tuples.

        Args:
            output: Raw stdout from du command.

        Returns:
            List of (path, size_kb) tuples.
        """
        entries = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                try:
                    size_kb = int(parts[0])
                    path = parts[1]
                    entries.append((path, size_kb))
                except ValueError:
                    continue
        return entries

    def _build_tree(self, entries: list[tuple[str, int]], root_path: str) -> dict[str, Any]:
        """
        Build hierarchical tree from flat du entries.

        Args:
            entries: List of (path, size_kb) tuples.
            root_path: The root path being scanned.

        Returns:
            Hierarchical dict structure.
        """
        # Create lookup for sizes
        size_lookup = dict(entries)

        # Normalize root path
        root_path = root_path.rstrip("/")
        root_name = Path(root_path).name or root_path

        # Find root size
        root_size = size_lookup.get(root_path, 0)

        # Build children map (parent -> children)
        children_map: dict[str, list[str]] = defaultdict(list)
        for path, _size in entries:
            if path == root_path:
                continue
            parent = str(Path(path).parent)
            children_map[parent].append(path)

        def build_node(path: str) -> dict[str, Any] | None:
            """Recursively build a node and its children."""
            size = size_lookup.get(path, 0)

            # Filter by min size
            if size < self.min_size_kb and path != root_path:
                return None

            name = Path(path).name or path

            node: dict[str, Any] = {
                "name": name,
                "path": path,  # Full path for drill-down navigation
                "value": size,
                "sizeFormatted": self.format_size(size),
            }

            # Build children
            child_paths = children_map.get(path, [])
            if child_paths:
                children = []
                for child_path in child_paths:
                    child_node = build_node(child_path)
                    if child_node:
                        children.append(child_node)

                if children:
                    # Sort by size descending
                    children.sort(key=lambda x: x["value"], reverse=True)
                    node["children"] = children

            return node

        # Build from root
        tree = build_node(root_path)
        if tree is None:
            tree = {"name": root_name, "value": root_size}

        return tree

    def _add_percentages(self, node: dict[str, Any], parent_size: int) -> None:
        """
        Recursively add percentage of parent to each node.

        Args:
            node: Tree node to process.
            parent_size: Size of parent node for percentage calculation.
        """
        if parent_size > 0:
            node["percentage"] = round((node.get("value", 0) / parent_size) * 100, 1)
        else:
            node["percentage"] = 0

        for child in node.get("children", []):
            # Children percentage relative to this node
            self._add_percentages(child, node.get("value", 1))

    def format_size(self, size_kb: int) -> str:
        """
        Format size in KB to human-readable string.

        Args:
            size_kb: Size in kilobytes.

        Returns:
            Human-readable string (e.g., "1.5 GB").
        """
        if size_kb >= 1048576:  # 1 GB in KB
            return f"{size_kb / 1048576:.1f} GB"
        elif size_kb >= 1024:  # 1 MB in KB
            return f"{size_kb / 1024:.1f} MB"
        else:
            return f"{size_kb} KB"
