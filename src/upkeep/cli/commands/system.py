"""
System-related CLI commands using SystemAPI.

All commands use the API layer for consistency.
"""

import psutil
from rich.console import Console

from ...api.system import SystemAPI


def status_command() -> None:
    """
    Show system status (quick check).

    Uses SystemAPI for system information.
    Uses psutil directly for disk/memory (standard library, not core).
    """
    console = Console()
    api = SystemAPI()

    console.print("\n[bold cyan]System Status[/bold cyan]\n")

    # Disk usage (psutil is fine - standard library)
    disk = psutil.disk_usage("/")
    disk_color = "green" if disk.percent < 75 else "yellow" if disk.percent < 90 else "red"
    console.print(f"[bold]Disk Usage:[/bold] [{disk_color}]{disk.percent:.1f}%[/{disk_color}]")
    console.print(f"  Free: {disk.free / (1024**3):.1f} GB")
    console.print(f"  Total: {disk.total / (1024**3):.1f} GB\n")

    # System info (using API layer)
    try:
        info = api.get_info()
        console.print(f"[bold]System:[/bold] macOS {info.version} ({info.architecture})")
        console.print(f"[bold]User:[/bold] {info.username}@{info.hostname}\n")
    except Exception as e:
        console.print(f"[yellow]Could not get system info: {e}[/yellow]\n")

    # Memory (psutil is fine - standard library)
    memory = psutil.virtual_memory()
    mem_color = "green" if memory.percent < 75 else "yellow" if memory.percent < 90 else "red"
    console.print(f"[bold]Memory:[/bold] [{mem_color}]{memory.percent:.1f}% used[/{mem_color}]")
    console.print(f"  Available: {memory.available / (1024**3):.1f} GB\n")

    console.print("[dim]Run 'upkeep web' or './run-web.sh' for detailed analysis[/dim]\n")
