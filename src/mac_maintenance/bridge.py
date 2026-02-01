"""
Bash-to-Python bridge module.

This module provides a command-line interface that can be called from bash scripts
to access Python functionality.
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict

from .storage.analyzer import DiskAnalyzer
from .core.system import get_system_info


def storage_analyze(path: str, max_depth: int = 3, output_json: bool = False) -> int:
    """
    Analyze storage for a given path.

    Args:
        path: Path to analyze
        max_depth: Maximum directory depth
        output_json: Output as JSON

    Returns:
        Exit code (0 for success)
    """
    try:
        analyzer = DiskAnalyzer(Path(path), max_depth=max_depth)
        result = analyzer.analyze()

        if output_json:
            data = {
                "status": "success",
                "root_path": str(result.root_path),
                "total_size": result.total_size,
                "total_size_gb": round(result.total_size_gb, 2),
                "file_count": result.file_count,
                "dir_count": result.dir_count,
                "largest_entries": [
                    {
                        "path": str(e.path),
                        "size": e.size,
                        "is_dir": e.is_dir,
                    }
                    for e in result.get_largest_entries(10)
                ],
                "category_sizes": {
                    cat: {"size": size, "size_gb": round(size / (1024**3), 2)}
                    for cat, size in result.category_sizes.items()
                    if size > 0
                },
            }
            print(json.dumps(data, indent=2))
        else:
            # Simple text output for bash consumption
            print(f"TOTAL_SIZE_GB={result.total_size_gb:.2f}")
            print(f"FILE_COUNT={result.file_count}")
            print(f"DIR_COUNT={result.dir_count}")

        return 0

    except Exception as e:
        if output_json:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            print(f"ERROR={e}", file=sys.stderr)
        return 1


def system_info(output_json: bool = False) -> int:
    """
    Get system information.

    Args:
        output_json: Output as JSON

    Returns:
        Exit code (0 for success)
    """
    try:
        info = get_system_info()

        if output_json:
            print(json.dumps(info, indent=2))
        else:
            # Simple text output for bash consumption
            for key, value in info.items():
                print(f"{key.upper()}={value}")

        return 0

    except Exception as e:
        if output_json:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            print(f"ERROR={e}", file=sys.stderr)
        return 1


def check_python_available() -> int:
    """
    Check if Python environment is properly set up.

    Returns:
        Exit code (0 if available)
    """
    try:
        # Try to import key modules
        from . import __version__
        from .storage.analyzer import DiskAnalyzer
        from .core.system import get_system_info

        print("PYTHON_AVAILABLE=1")
        print(f"VERSION={__version__}")
        return 0
    except Exception as e:
        print(f"PYTHON_AVAILABLE=0")
        print(f"ERROR={e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for bash bridge.

    Usage:
        python -m mac_maintenance.bridge <command> [args...]

    Commands:
        check - Check if Python is available
        system-info [--json] - Get system information
        analyze <path> [--max-depth N] [--json] - Analyze storage
    """
    if len(sys.argv) < 2:
        print("Usage: python -m mac_maintenance.bridge <command> [args...]", file=sys.stderr)
        return 1

    command = sys.argv[1]

    if command == "check":
        return check_python_available()

    elif command == "system-info":
        output_json = "--json" in sys.argv
        return system_info(output_json)

    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: python -m mac_maintenance.bridge analyze <path> [--max-depth N] [--json]", file=sys.stderr)
            return 1

        path = sys.argv[2]
        max_depth = 3
        output_json = False

        # Parse optional arguments
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == "--max-depth" and i + 1 < len(sys.argv):
                try:
                    max_depth = int(sys.argv[i + 1])
                except ValueError:
                    print(f"Invalid max-depth: {sys.argv[i + 1]}", file=sys.stderr)
                    return 1
            elif arg == "--json":
                output_json = True

        return storage_analyze(path, max_depth, output_json)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
