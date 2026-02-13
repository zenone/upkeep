"""
CLI interface for storage analysis.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .analyzer import AnalysisResult, DiskAnalyzer

console = Console()


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def display_results(result: AnalysisResult) -> None:
    """Display analysis results in a nice format."""
    console.print(f"\n[bold]Storage Analysis: {result.root_path}[/bold]\n")

    # Summary
    console.print(f"Total size: [green]{format_size(result.total_size)}[/green]")
    console.print(f"Files: {result.file_count:,}")
    console.print(f"Directories: {result.dir_count:,}\n")

    # Top 10 largest entries
    console.print("[bold]Largest Items:[/bold]")
    table = Table(show_header=True)
    table.add_column("Path", style="cyan", no_wrap=True)
    table.add_column("Size", justify="right", style="green")
    table.add_column("Type", justify="center")

    for entry in result.get_largest_entries(10):
        rel_path = (
            entry.path.relative_to(result.root_path)
            if entry.path != result.root_path
            else entry.path.name
        )
        table.add_row(
            str(rel_path),
            format_size(entry.size),
            "DIR" if entry.is_dir else "FILE",
        )

    console.print(table)
    console.print()

    # Category breakdown
    if any(size > 0 for size in result.category_sizes.values()):
        console.print("[bold]Storage by Category:[/bold]")
        cat_table = Table(show_header=True)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Size", justify="right", style="green")
        cat_table.add_column("Percentage", justify="right", style="yellow")

        sorted_categories = sorted(
            result.category_sizes.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for category, size in sorted_categories:
            if size > 0:
                percentage = (size / result.total_size) * 100
                cat_table.add_row(
                    category.title(),
                    format_size(size),
                    f"{percentage:.1f}%",
                )

        console.print(cat_table)
        console.print()


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--max-depth",
    "-d",
    type=int,
    help="Maximum directory depth to scan",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Patterns to exclude (can specify multiple times)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON",
)
def main(
    path: Path,
    max_depth: int | None,
    exclude: tuple,
    output_json: bool,
) -> None:
    """
    Analyze disk usage for a given PATH.

    Example:
        upkeep-analyze ~/Documents
        upkeep-analyze --max-depth 3 /
        upkeep-analyze --exclude "*.log" --exclude "*.tmp" ~/
    """
    console.print(f"[yellow]Analyzing: {path}[/yellow]\n")

    try:
        analyzer = DiskAnalyzer(
            root_path=path,
            exclude_patterns=list(exclude) if exclude else None,
            max_depth=max_depth,
        )

        with console.status("[bold green]Scanning...[/bold green]"):
            result = analyzer.analyze()

        if output_json:

            data = {
                "root_path": str(result.root_path),
                "total_size": result.total_size,
                "total_size_gb": round(result.total_size_gb, 2),
                "file_count": result.file_count,
                "dir_count": result.dir_count,
                "largest_entries": [
                    {
                        "path": str(e.path),
                        "size": e.size,
                        "size_mb": round(e.size_mb, 2),
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
            console.print_json(data=data)
        else:
            display_results(result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    main()
