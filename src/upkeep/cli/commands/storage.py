"""
Storage-related CLI commands using StorageAPI.

All commands use the API layer for consistency.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ...api.storage import StorageAPI
from ...core.exceptions import PathNotFoundError, PathNotReadableError


def analyze_command(path: Path) -> None:
    """
    Analyze storage for given path.

    Uses StorageAPI for disk analysis (API-first architecture).

    Args:
        path: Path to analyze
    """
    console = Console()
    api = StorageAPI()

    try:
        # Use API layer instead of direct DiskAnalyzer
        with console.status(f"[bold green]Analyzing {path}..."):
            result = api.analyze_path(str(path), max_depth=3, max_entries=10)

        # Display results (maintain existing output format)
        console.print(f"\n[bold]Storage Analysis: {path}[/bold]\n")
        console.print(f"Total: [green]{result.total_size_gb:.2f} GB[/green]")
        console.print(f"Files: {result.file_count:,}")
        console.print(f"Directories: {result.dir_count:,}\n")

        # Largest items (use data from API result)
        if result.largest_entries:
            table = Table(title="Largest Items")
            table.add_column("Path", style="cyan")
            table.add_column("Size", justify="right", style="green")

            for entry in result.largest_entries:
                # Calculate size display
                size_bytes = entry['size_bytes']
                size_mb = size_bytes / (1024**2)
                size_gb = size_bytes / (1024**3)

                size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_gb:.2f} GB"

                # Extract filename from path
                path_obj = Path(entry['path'])
                table.add_row(path_obj.name, size_str)

            console.print(table)

        console.print("\n[dim]Run 'upkeep web' or './run-web.sh' for detailed analysis[/dim]\n")

    except PathNotFoundError as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
    except PathNotReadableError as e:
        console.print(f"\n[red]Permission denied: {e}[/red]\n")
    except Exception as e:
        console.print(f"\n[red]Error analyzing path: {e}[/red]\n")
