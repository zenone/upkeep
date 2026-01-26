"""
Terminal User Interface (TUI) for mac-maintenance.

A beautiful, Netflix-quality TUI using Textual framework.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    TabbedContent,
    TabPane,
    DataTable,
    ProgressBar,
    Label,
)
from textual.binding import Binding
from textual.reactive import reactive

from .dashboard import DashboardView
from .storage import StorageView
from .about import AboutView


class MacMaintenanceTUI(App):
    """
    mac-maintenance Terminal User Interface.

    A professional, beautiful TUI for system maintenance and analysis.
    """

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    Footer {
        background: $panel;
    }

    #main-container {
        height: 100%;
        background: $surface;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1 2;
    }

    .box {
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        margin: 1 0;
    }

    .metric-label {
        color: $text-muted;
        text-style: bold;
    }

    .metric-value {
        color: $success;
        text-style: bold;
    }

    .metric-value-warning {
        color: $warning;
        text-style: bold;
    }

    .metric-value-error {
        color: $error;
        text-style: bold;
    }

    Button {
        margin: 1 1;
    }

    Button.success {
        background: $success;
        color: $text;
    }

    Button.warning {
        background: $warning;
        color: $text;
    }

    Button.error {
        background: $error;
        color: $text;
    }
    """

    TITLE = "macOS Maintenance Toolkit"
    SUB_TITLE = "v3.0.0-alpha | Michelin Star Quality"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "show_tab('dashboard')", "Dashboard", show=False),
        Binding("s", "show_tab('storage')", "Storage", show=False),
        Binding("a", "show_tab('about')", "About", show=False),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("?", "show_help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with Container(id="main-container"):
            with TabbedContent(initial="dashboard"):
                with TabPane("Dashboard", id="dashboard"):
                    yield DashboardView()

                with TabPane("Storage Analysis", id="storage"):
                    yield StorageView()

                with TabPane("About", id="about"):
                    yield AboutView()

        yield Footer()

    def action_show_tab(self, tab: str) -> None:
        """Switch to a specific tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = tab

    def action_refresh_data(self) -> None:
        """Refresh data in current view."""
        self.notify("Refreshing data...", severity="information")
        # Trigger refresh on active pane
        tabs = self.query_one(TabbedContent)
        active_pane = tabs.get_pane(tabs.active)
        if hasattr(active_pane, "refresh_data"):
            active_pane.refresh_data()

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold]Keyboard Shortcuts:[/bold]

• [cyan]d[/cyan] - Dashboard view
• [cyan]s[/cyan] - Storage analysis
• [cyan]a[/cyan] - About
• [cyan]r[/cyan] - Refresh current view
• [cyan]?[/cyan] - Show this help
• [cyan]q[/cyan] - Quit

[bold]Navigation:[/bold]
• [cyan]Tab[/cyan] - Next tab
• [cyan]Shift+Tab[/cyan] - Previous tab
• [cyan]Arrow keys[/cyan] - Navigate within views
        """
        self.notify(help_text, title="Help", timeout=10, severity="information")


def run() -> None:
    """Launch the TUI application."""
    app = MacMaintenanceTUI()
    app.run()


if __name__ == "__main__":
    run()
