"""
Terminal User Interface (TUI) for upkeep.

A professional, world-class TUI for system maintenance.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, TabbedContent, TabPane
from textual.binding import Binding

from .dashboard import DashboardView
from .storage import StorageView
from .maintenance import MaintenanceView
from .about import AboutView


class StatusBar(Static):
    """Status bar showing current operation state."""

    def __init__(self, **kwargs):
        """
        Initialize the status bar widget.

        Args:
            **kwargs: Additional widget arguments
        """
        super().__init__()
        self.status = "Ready"

    def update_status(self, message: str) -> None:
        """Update status message."""
        self.status = message
        self.update(f"[bold]Status:[/bold] {message}")


class MacMaintenanceTUI(App):
    """
    upkeep Terminal User Interface.

    A professional, world-class TUI for system maintenance.
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

    StatusBar {
        dock: top;
        height: 1;
        background: $boost;
        padding: 0 1;
        color: $text;
    }

    #main-container {
        height: 100%;
        background: $surface;
    }

    TabbedContent {
        height: 100%;
    }

    TabbedContent ContentSwitcher {
        height: 1fr;
    }

    TabPane {
        padding: 1 2;
        height: 1fr;
    }

    .box {
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        margin: 1 0;
        min-height: 3;
    }

    .metric-label {
        color: $text-muted;
        text-style: bold;
    }

    .metric-value {
        color: $success;
        text-style: bold;
    }

    Button {
        margin: 1 1;
    }
    """

    TITLE = "Upkeep"
    SUB_TITLE = "v2.0.0 | Mac Maintenance Made Simple"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "show_tab('dashboard')", "Dashboard", show=True),
        Binding("m", "show_tab('maintenance')", "Maintenance", show=True),
        Binding("s", "show_tab('storage')", "Storage", show=True),
        Binding("a", "show_tab('about')", "About", show=True),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("?", "show_help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield StatusBar()

        with Container(id="main-container"):
            with TabbedContent(initial="dashboard"):
                with TabPane("📊 Dashboard", id="dashboard"):
                    yield DashboardView()

                with TabPane("🔧 Maintenance", id="maintenance"):
                    yield MaintenanceView()

                with TabPane("💾 Storage", id="storage"):
                    yield StorageView()

                with TabPane("ℹ️  About", id="about"):
                    yield AboutView()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize app on mount."""
        self.update_status("Ready")

    def update_status(self, message: str) -> None:
        """Update status bar message."""
        try:
            status_bar = self.query_one(StatusBar)
            status_bar.update_status(message)
        except Exception:
            pass

    def action_show_tab(self, tab: str) -> None:
        """Switch to a specific tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = tab

            tab_names = {
                "dashboard": "Dashboard",
                "maintenance": "Maintenance Operations",
                "storage": "Storage Analysis",
                "about": "About"
            }
            self.update_status(f"Viewing: {tab_names.get(tab, tab)}")
        except Exception as e:
            self.notify(f"Error switching tabs: {e}", severity="error")

    def action_refresh_data(self) -> None:
        """Refresh data in current view."""
        self.update_status("Refreshing...")
        try:
            tabs = self.query_one(TabbedContent)
            active_pane = tabs.get_pane(tabs.active)

            # Find the actual view widget inside the pane
            views = active_pane.query("DashboardView, MaintenanceView, StorageView")
            if views:
                view = views.first()
                if hasattr(view, "refresh_data"):
                    view.refresh_data()
                    self.update_status("Refreshed")
                    self.notify("Data refreshed", severity="information")
                else:
                    self.update_status("Ready")
            else:
                self.update_status("Ready")
        except Exception as e:
            self.update_status("Refresh failed")
            self.notify(f"Error refreshing: {e}", severity="error")

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold cyan]Keyboard Shortcuts:[/bold cyan]

[bold]Navigation:[/bold]
  [cyan]d[/cyan] - Dashboard view
  [cyan]m[/cyan] - Maintenance operations
  [cyan]s[/cyan] - Storage analysis
  [cyan]a[/cyan] - About
  [cyan]r[/cyan] - Refresh current view
  [cyan]?[/cyan] - Show this help
  [cyan]q[/cyan] - Quit

[bold]Tips:[/bold]
  • Use Tab to navigate between widgets
  • Use arrow keys in tables and lists
  • Operations show real-time output
  • Press Ctrl+C to cancel running operation
        """
        self.notify(help_text, title="Help", timeout=15, severity="information")
        self.update_status("Help displayed")


def run() -> None:
    """Launch the TUI application."""
    app = MacMaintenanceTUI()
    app.run()


if __name__ == "__main__":
    run()
