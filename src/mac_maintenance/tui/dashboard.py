"""
Dashboard view for TUI.

Displays system health, disk usage, and maintenance status.
"""

import psutil
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, ProgressBar, Label, Button
from textual.reactive import reactive

from ..core.system import get_system_info


class MetricBox(Static):
    """A styled box displaying a metric."""

    def __init__(self, label: str, value: str, status: str = "normal", **kwargs):
        """
        Initialize metric box.

        Args:
            label: Metric label
            value: Metric value
            status: Status color (normal, warning, error)
        """
        super().__init__(**kwargs)
        self.metric_label = label
        self.metric_value = value
        self.status = status

    def compose(self) -> ComposeResult:
        """Compose the metric display."""
        status_class = {
            "normal": "metric-value",
            "warning": "metric-value-warning",
            "error": "metric-value-error",
        }.get(self.status, "metric-value")

        yield Static(self.metric_label, classes="metric-label")
        yield Static(self.metric_value, classes=status_class)


class DiskUsageWidget(Static):
    """Visual disk usage display with progress bar."""

    usage_percent = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_usage()

    def compose(self) -> ComposeResult:
        """Compose the disk usage display."""
        yield Label("Disk Usage", classes="metric-label")
        yield ProgressBar(total=100, show_eta=False, show_percentage=True)
        yield Static(id="disk-usage-text")

    def update_usage(self) -> None:
        """Update disk usage data."""
        try:
            disk = psutil.disk_usage("/")
            self.usage_percent = disk.percent

            # Update progress bar
            if self.is_mounted:
                progress_bar = self.query_one(ProgressBar)
                progress_bar.update(progress=self.usage_percent)

                # Update text display
                free_gb = disk.free / (1024**3)
                total_gb = disk.total / (1024**3)
                text = self.query_one("#disk-usage-text", Static)
                text.update(f"{free_gb:.1f} GB free of {total_gb:.1f} GB total")
        except Exception:
            pass

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.update_usage()

    def refresh_data(self) -> None:
        """Refresh the disk usage data."""
        self.update_usage()


class SystemInfoWidget(Static):
    """System information display."""

    def compose(self) -> ComposeResult:
        """Compose system information."""
        try:
            info = get_system_info()
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()

            with Vertical(classes="box"):
                yield Static("System Information", classes="metric-label")
                yield Static(f"[cyan]macOS:[/cyan] {info['version']} ({info['build']})")
                yield Static(f"[cyan]Architecture:[/cyan] {info['architecture']}")
                yield Static(f"[cyan]CPU Cores:[/cyan] {cpu_count}")
                yield Static(
                    f"[cyan]Memory:[/cyan] {memory.total / (1024**3):.1f} GB "
                    f"({memory.percent}% used)"
                )
        except Exception as e:
            yield Static(f"Error loading system info: {e}", classes="metric-value-error")


class SecurityStatusWidget(Static):
    """Security status display."""

    def compose(self) -> ComposeResult:
        """Compose security status."""
        with Vertical(classes="box"):
            yield Static("Security Status", classes="metric-label")

            # Check SIP status (simplified check)
            try:
                import subprocess

                result = subprocess.run(
                    ["csrutil", "status"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                sip_enabled = "enabled" in result.stdout.lower()
                sip_status = "✓ Enabled" if sip_enabled else "✗ Disabled"
                sip_color = "green" if sip_enabled else "red"
                yield Static(f"[cyan]SIP:[/cyan] [{sip_color}]{sip_status}[/{sip_color}]")
            except Exception:
                yield Static("[cyan]SIP:[/cyan] [yellow]Unknown[/yellow]")

            # Check FileVault status
            try:
                result = subprocess.run(
                    ["fdesetup", "status"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                fv_enabled = "On" in result.stdout
                fv_status = "✓ Enabled" if fv_enabled else "✗ Disabled"
                fv_color = "green" if fv_enabled else "yellow"
                yield Static(
                    f"[cyan]FileVault:[/cyan] [{fv_color}]{fv_status}[/{fv_color}]"
                )
            except Exception:
                yield Static("[cyan]FileVault:[/cyan] [yellow]Unknown[/yellow]")


class QuickActionsWidget(Static):
    """Quick action buttons."""

    def compose(self) -> ComposeResult:
        """Compose quick actions."""
        with Vertical(classes="box"):
            yield Static("Quick Actions", classes="metric-label")
            with Horizontal():
                yield Button("Analyze Storage", variant="success", id="analyze-storage")
                yield Button("View Logs", variant="default", id="view-logs")
                yield Button("Run Maintenance", variant="warning", id="run-maintenance")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "analyze-storage":
            self.app.action_show_tab("storage")
        elif event.button.id == "view-logs":
            self.app.notify("Log viewer coming soon!", severity="information")
        elif event.button.id == "run-maintenance":
            self.app.notify(
                "Use maintain.sh for maintenance operations", severity="information"
            )


class DashboardView(Container):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        # Header
        yield Static(
            "[bold]System Health Dashboard[/bold]",
            classes="metric-label",
        )

        # Two-column layout
        with Grid(id="dashboard-grid"):
            # Left column
            with Vertical():
                yield DiskUsageWidget(classes="box")
                yield SystemInfoWidget()

            # Right column
            with Vertical():
                yield SecurityStatusWidget()
                yield QuickActionsWidget()

        # Overall status at bottom
        with Vertical(classes="box"):
            yield Static("Overall System Health", classes="metric-label")
            health_score = self.calculate_health_score()
            health_status, health_color = self.get_health_status(health_score)
            yield Static(
                f"[{health_color}]● {health_status}[/{health_color}] "
                f"(Score: {health_score}/100)"
            )

    def calculate_health_score(self) -> int:
        """Calculate overall health score."""
        score = 100

        try:
            # Disk usage penalty
            disk = psutil.disk_usage("/")
            if disk.percent >= 90:
                score -= 30
            elif disk.percent >= 75:
                score -= 10

            # Memory usage penalty
            memory = psutil.virtual_memory()
            if memory.percent >= 90:
                score -= 20
            elif memory.percent >= 75:
                score -= 10

        except Exception:
            pass

        return max(0, score)

    def get_health_status(self, score: int) -> tuple[str, str]:
        """Get health status and color based on score."""
        if score >= 90:
            return ("Excellent", "green")
        elif score >= 70:
            return ("Good", "cyan")
        elif score >= 50:
            return ("Fair", "yellow")
        else:
            return ("Poor", "red")

    def refresh_data(self) -> None:
        """Refresh dashboard data."""
        # Trigger refresh on child widgets
        for widget in self.query(DiskUsageWidget):
            widget.refresh_data()
        self.app.notify("Dashboard refreshed", severity="information")


# CSS for dashboard grid
DashboardView.DEFAULT_CSS = """
DashboardView {
    height: 100%;
}

#dashboard-grid {
    grid-size: 2 1;
    grid-columns: 1fr 1fr;
    height: auto;
    margin: 1 0;
}
"""
