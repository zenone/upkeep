"""
Main CLI entry point for upkeep.

API-First Architecture:
- All commands use the API layer (SystemAPI, StorageAPI, MaintenanceAPI)
- No direct imports from core/ or storage/ modules
- Command implementations in cli/commands/ modules

Provides unified command-line interface for all features.
"""

import click
from pathlib import Path

from .. import __version__
from ..tui import run as run_tui
from .commands import status_command, analyze_command


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
    # Simply launch TUI - sudo is handled by run-tui.sh wrapper script
    # or users can run 'sudo -v' before running 'upkeep tui' directly
    run_tui()


@main.command()
def web() -> None:
    """
    Launch the Web Interface.

    Starts a local web server (default port 8080, auto-fallback to 8081-8089).
    Best way to use: ./run-web.sh (handles sudo automatically)
    """
    import subprocess
    import sys
    from pathlib import Path
    from rich.console import Console

    console = Console()

    # Find run-web.sh script
    script_path = Path.cwd() / "run-web.sh"

    if script_path.exists():
        console.print("\n[yellow]Launching web interface...[/yellow]")
        console.print("[dim]Use ./run-web.sh for best experience[/dim]\n")
        try:
            subprocess.run([str(script_path)], check=True)
        except KeyboardInterrupt:
            console.print("\n[dim]Web server stopped.[/dim]")
        except subprocess.CalledProcessError:
            console.print("\n[red]Error launching web interface.[/red]")
            sys.exit(1)
    else:
        console.print("\n[yellow]Starting web server directly...[/yellow]")
        console.print("[dim]For sudo support, use: ./run-web.sh[/dim]\n")
        try:
            import uvicorn
            from upkeep.web.server import app
            from upkeep.web.port_utils import find_available_port

            # Find available port (8080-8089)
            port = find_available_port(8080, 8089)

            if port is None:
                console.print("\n[red]Error: No available ports in range 8080-8089[/red]")
                console.print("[yellow]Close other applications or specify a different port[/yellow]\n")
                sys.exit(1)

            if port != 8080:
                console.print(f"[yellow]Port 8080 in use, using port {port} instead[/yellow]")

            console.print(f"\n[bold green]Starting server on http://127.0.0.1:{port}[/bold green]\n")

            uvicorn.run(app, host="127.0.0.1", port=port)
        except KeyboardInterrupt:
            console.print("\n[dim]Web server stopped.[/dim]")
        except ImportError as e:
            if "uvicorn" in str(e):
                console.print("\n[red]Error: uvicorn not installed.[/red]")
                console.print("[yellow]Install with: pip install uvicorn[/yellow]\n")
            else:
                console.print(f"\n[red]Import error: {e}[/red]\n")
            sys.exit(1)
        except OSError as e:
            console.print(f"\n[red]Server error: {e}[/red]\n")
            sys.exit(1)


@main.command()
def status() -> None:
    """
    Show system status (quick check).

    Displays disk usage, security status, and system health.

    Uses API layer for system information (API-first architecture).
    """
    # Delegate to command module (uses SystemAPI)
    status_command()


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def analyze(path: Path) -> None:
    """
    Analyze storage for PATH.

    Quick storage analysis from the command line.
    Use --help for more options.

    Uses API layer for storage analysis (API-first architecture).
    """
    # Delegate to command module (uses StorageAPI)
    analyze_command(path)


if __name__ == "__main__":
    main()
