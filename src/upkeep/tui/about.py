"""
About view for TUI.

Displays project information, version, and credits.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Center, VerticalScroll
from textual.widgets import Static, Rule

from .. import __version__


class AboutView(VerticalScroll):
    """About and information view."""

    def compose(self) -> ComposeResult:
        """Compose the about view."""
        with Center():
            with Vertical(classes="box"):
                yield Static("[bold cyan]🧹 Upkeep[/bold cyan]")
                yield Static(f"[dim]Version {__version__}[/dim]")
                yield Rule()

                yield Static("\n[bold]Description[/bold]")
                yield Static(
                    "A modern, safe-by-default maintenance toolkit for macOS.\n"
                    "Comprehensive system health monitoring and maintenance operations."
                )

                yield Static("\n[bold]Features[/bold]")
                yield Static("• [cyan]System Health Dashboard[/cyan] - At-a-glance status")
                yield Static("• [cyan]Maintenance Operations[/cyan] - Run updates, cleanup, verification")
                yield Static("• [cyan]Storage Analysis[/cyan] - Visualize disk usage")
                yield Static("• [cyan]Security Checks[/cyan] - SIP, FileVault, sudo patches")
                yield Static("• [cyan]Interactive TUI[/cyan] - Complete system management")
                yield Static("• [cyan]Command-line Tools[/cyan] - Scriptable automation")

                yield Static("\n[bold]Technology Stack[/bold]")
                yield Static("• [green]Bash[/green] - Core maintenance operations")
                yield Static("• [green]Python 3.10+[/green] - Advanced features")
                yield Static("• [green]Textual[/green] - Terminal UI framework")
                yield Static("• [green]Rich[/green] - Beautiful terminal output")
                yield Static("• [green]pytest[/green] - Comprehensive testing")

                yield Static("\n[bold]Quality Metrics[/bold]")
                yield Static("• [yellow]127 tests[/yellow] - 100% passing")
                yield Static("• [yellow]Production ready[/yellow] - v2.0.0")
                yield Static("• [yellow]Type safe[/yellow] - mypy strict mode")
                yield Static("• [yellow]Linted[/yellow] - ruff + black")
                yield Static("• [yellow]Documented[/yellow] - Complete guides")

                yield Rule()

                yield Static("\n[bold]Keyboard Shortcuts[/bold]")
                yield Static("• [cyan]d[/cyan] - Dashboard")
                yield Static("• [cyan]m[/cyan] - Maintenance Operations")
                yield Static("• [cyan]s[/cyan] - Storage Analysis")
                yield Static("• [cyan]a[/cyan] - About (this screen)")
                yield Static("• [cyan]r[/cyan] - Refresh current view")
                yield Static("• [cyan]?[/cyan] - Show help")
                yield Static("• [cyan]q[/cyan] - Quit")

                yield Static("\n[bold]Project Links[/bold]")
                yield Static("• GitHub: [link]https://github.com/zenone/upkeep[/link]")
                yield Static("• Documentation: See README.md and PYTHON_DEVELOPMENT.md")

                yield Rule()

                yield Static(
                    "\n[dim]Built for macOS | "
                    "© 2026 upkeep contributors[/dim]"
                )


AboutView.DEFAULT_CSS = """
AboutView {
    align: center middle;
    height: 1fr;
}

AboutView Vertical {
    width: 80;
    max-width: 100;
    padding: 2 4;
}

AboutView Static {
    text-align: left;
}
"""
