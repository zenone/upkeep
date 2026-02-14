"""
Duplicate Reporter - Generate reports from duplicate scan results.

Supports JSON, text, and CSV output formats.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upkeep.core.duplicate_scanner import DuplicateGroup, ScanResult


def format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class DuplicateReporter:
    """Generates reports from duplicate scan results."""

    def to_json(self, result: ScanResult, pretty: bool = True) -> str:
        """
        Generate JSON output for API/UI consumption.

        Args:
            result: Scan result to serialize.
            pretty: If True, format with indentation.

        Returns:
            JSON string representation.
        """
        data = {
            "scan_summary": {
                "total_files_scanned": result.total_files_scanned,
                "total_duplicates": result.total_duplicates,
                "total_wasted_bytes": result.total_wasted_bytes,
                "total_wasted_formatted": format_bytes(result.total_wasted_bytes),
                "duplicate_groups_count": len(result.duplicate_groups),
                "scan_duration_seconds": round(result.scan_duration_seconds, 2),
                "errors_count": len(result.errors),
            },
            "duplicate_groups": [self._group_to_dict(group) for group in result.duplicate_groups],
            "errors": result.errors,
        }

        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def _group_to_dict(self, group: DuplicateGroup) -> dict:
        """Convert a DuplicateGroup to a dictionary."""
        return {
            "hash": group.hash[:16],  # Truncate for readability
            "full_hash": group.hash,
            "size_bytes": group.size_bytes,
            "size_formatted": format_bytes(group.size_bytes),
            "file_count": len(group.files),
            "potential_savings_bytes": group.potential_savings,
            "potential_savings_formatted": format_bytes(group.potential_savings),
            "files": [
                {
                    "path": str(f.path),
                    "mtime": datetime.fromtimestamp(f.mtime).isoformat() if f.mtime else None,
                }
                for f in group.files
            ],
        }

    def to_text(self, result: ScanResult) -> str:
        """
        Generate human-readable text report.

        Args:
            result: Scan result to format.

        Returns:
            Text report string.
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("DUPLICATE FILE REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append("SCAN SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Files scanned:     {result.total_files_scanned:,}")
        lines.append(f"Duplicate files:   {result.total_duplicates:,}")
        lines.append(f"Duplicate groups:  {len(result.duplicate_groups):,}")
        lines.append(f"Wasted space:      {format_bytes(result.total_wasted_bytes)}")
        lines.append(f"Scan duration:     {result.scan_duration_seconds:.2f}s")
        lines.append("")

        if not result.duplicate_groups:
            lines.append("No duplicates found! 🎉")
            lines.append("")
            return "\n".join(lines)

        # Duplicate groups
        lines.append("DUPLICATE GROUPS (sorted by wasted space)")
        lines.append("-" * 40)
        lines.append("")

        for i, group in enumerate(result.duplicate_groups, 1):
            lines.append(
                f"Group {i}: {len(group.files)} files, {format_bytes(group.size_bytes)} each"
            )
            lines.append(f"  Potential savings: {format_bytes(group.potential_savings)}")
            lines.append(f"  Hash: {group.hash[:16]}...")
            lines.append("  Files:")
            for file_info in group.files:
                mtime_str = ""
                if file_info.mtime:
                    mtime = datetime.fromtimestamp(file_info.mtime)
                    mtime_str = f" (modified: {mtime.strftime('%Y-%m-%d %H:%M')})"
                lines.append(f"    - {file_info.path}{mtime_str}")
            lines.append("")

        # Errors
        if result.errors:
            lines.append("ERRORS")
            lines.append("-" * 40)
            for error in result.errors[:10]:  # Limit to first 10
                lines.append(f"  ! {error}")
            if len(result.errors) > 10:
                lines.append(f"  ... and {len(result.errors) - 10} more errors")
            lines.append("")

        # Footer
        lines.append("=" * 60)
        lines.append("To remove duplicates, manually select which copies to delete.")
        lines.append("Recommendation: Keep the file in the most sensible location.")
        lines.append("=" * 60)

        return "\n".join(lines)

    def to_csv(self, result: ScanResult) -> str:
        """
        Generate CSV export for spreadsheet analysis.

        Args:
            result: Scan result to export.

        Returns:
            CSV string with all duplicate files.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Group",
                "Hash",
                "Size (bytes)",
                "Size",
                "File Path",
                "Modified",
                "Potential Savings",
            ]
        )

        # Data rows
        for i, group in enumerate(result.duplicate_groups, 1):
            for j, file_info in enumerate(group.files):
                # Only show potential savings on first row of group
                savings = format_bytes(group.potential_savings) if j == 0 else ""

                mtime_str = ""
                if file_info.mtime:
                    mtime = datetime.fromtimestamp(file_info.mtime)
                    mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")

                writer.writerow(
                    [
                        i,
                        group.hash[:16],
                        group.size_bytes,
                        format_bytes(group.size_bytes),
                        str(file_info.path),
                        mtime_str,
                        savings,
                    ]
                )

        return output.getvalue()

    def summary(self, result: ScanResult) -> dict:
        """
        Generate a brief summary for quick overview.

        Args:
            result: Scan result to summarize.

        Returns:
            Dict with key metrics.
        """
        return {
            "files_scanned": result.total_files_scanned,
            "duplicates_found": result.total_duplicates,
            "groups": len(result.duplicate_groups),
            "wasted_bytes": result.total_wasted_bytes,
            "wasted_formatted": format_bytes(result.total_wasted_bytes),
            "duration_seconds": round(result.scan_duration_seconds, 2),
            "top_savings": [
                {
                    "hash": g.hash[:8],
                    "files": len(g.files),
                    "savings": format_bytes(g.potential_savings),
                }
                for g in result.duplicate_groups[:5]  # Top 5
            ],
        }
