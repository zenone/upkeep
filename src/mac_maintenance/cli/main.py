"""
Main CLI entry point for mac-maintenance.

Provides unified command-line interface for all features.
"""

import click
from pathlib import Path

from .. import __version__
from ..tui import run as run_tui


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """
    macOS Maintenance Toolkit - Michelin Star Quality

    A modern, safe-by-default maintenance toolkit for macOS.
    """
    pass


@main.command()
def tui() -> None:
    """
    Launch the Terminal User Interface (TUI).

    A beautiful, interactive terminal interface for system maintenance
    and analysis.
    """
    run_tui()


@main.command()
def status() -> None:
    """
    Show system status (quick check).

    Displays disk usage, security status, and system health.
    """
    from rich.console import Console
    from rich.table import Table
    import psutil
    from ..core.system import get_system_info

    console = Console()

    console.print("\n[bold cyan]System Status[/bold cyan]\n")

    # Disk usage
    disk = psutil.disk_usage("/")
    disk_color = "green" if disk.percent < 75 else "yellow" if disk.percent < 90 else "red"
    console.print(f"[bold]Disk Usage:[/bold] [{disk_color}]{disk.percent:.1f}%[/{disk_color}]")
    console.print(f"  Free: {disk.free / (1024**3):.1f} GB")
    console.print(f"  Total: {disk.total / (1024**3):.1f} GB\n")

    # System info
    try:
        info = get_system_info()
        console.print(f"[bold]System:[/bold] macOS {info['version']} ({info['architecture']})")
        console.print(f"[bold]Build:[/bold] {info['build']}\n")
    except Exception as e:
        console.print(f"[yellow]Could not get system info: {e}[/yellow]\n")

    # Memory
    memory = psutil.virtual_memory()
    mem_color = "green" if memory.percent < 75 else "yellow" if memory.percent < 90 else "red"
    console.print(
        f"[bold]Memory:[/bold] [{mem_color}]{memory.percent:.1f}% used[/{mem_color}]"
    )
    console.print(f"  Available: {memory.available / (1024**3):.1f} GB\n")

    console.print("[dim]Run 'mac-maintenance tui' for detailed analysis[/dim]\n")


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def analyze(path: Path) -> None:
    """
    Analyze storage for PATH.

    Quick storage analysis from the command line.
    Use --help for more options.
    """
    from ..storage.analyzer import DiskAnalyzer
    from rich.console import Console
    from rich.table import Table

    console = Console()

    with console.status(f"[bold green]Analyzing {path}..."):
        analyzer = DiskAnalyzer(path, max_depth=3)
        result = analyzer.analyze()

    console.print(f"\n[bold]Storage Analysis: {path}[/bold]\n")
    console.print(f"Total: [green]{result.total_size_gb:.2f} GB[/green]")
    console.print(f"Files: {result.file_count:,}")
    console.print(f"Directories: {result.dir_count:,}\n")

    # Largest items
    table = Table(title="Largest Items")
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for entry in result.get_largest_entries(10):
        size_str = f"{entry.size_mb:.1f} MB" if entry.size_mb < 1024 else f"{entry.size_gb:.2f} GB"
        table.add_row(entry.path.name, size_str)

    console.print(table)
    console.print("\n[dim]Run 'mac-maintenance tui' for detailed analysis[/dim]\n")


if __name__ == "__main__":
    main()
