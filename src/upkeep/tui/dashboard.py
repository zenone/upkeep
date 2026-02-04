"""
Dashboard view for TUI.

Displays system health, disk usage, and maintenance status.
"""

import psutil
from pathlib import Path
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, VerticalScroll
from textual.widgets import Static, ProgressBar, Label
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

    def compose(self) -> ComposeResult:
        """Compose the disk usage display."""
        yield Static("[bold]Disk Usage[/bold]", classes="metric-label")
        yield ProgressBar(total=100, show_eta=False, show_percentage=True, id="disk-progress")
        yield Static(id="disk-usage-text")

    def update_usage(self) -> None:
        """Update disk usage data."""
        try:
            disk = psutil.disk_usage("/")
            self.usage_percent = disk.percent

            # Update progress bar
            progress_bar = self.query_one("#disk-progress", ProgressBar)
            progress_bar.update(progress=self.usage_percent)

            # Update text display
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            text = self.query_one("#disk-usage-text", Static)
            text.update(f"{free_gb:.1f} GB free of {total_gb:.1f} GB total")
        except Exception as e:
            # Fallback display
            text = self.query_one("#disk-usage-text", Static)
            text.update(f"[yellow]Could not read disk usage[/yellow]")

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
        yield Static("[bold]System Information[/bold]", classes="metric-label")

        try:
            info = get_system_info()
            yield Static(f"[cyan]macOS:[/cyan] {info['version']} ({info['build']})")
            yield Static(f"[cyan]Architecture:[/cyan] {info['architecture']}")
        except Exception as e:
            yield Static(f"[yellow]macOS info unavailable[/yellow]")

        try:
            cpu_count = psutil.cpu_count()
            yield Static(f"[cyan]CPU Cores:[/cyan] {cpu_count}")
        except Exception:
            yield Static(f"[yellow]CPU info unavailable[/yellow]")

        try:
            memory = psutil.virtual_memory()
            yield Static(
                f"[cyan]Memory:[/cyan] {memory.total / (1024**3):.1f} GB "
                f"({memory.percent:.1f}% used)"
            )
        except Exception:
            yield Static(f"[yellow]Memory info unavailable[/yellow]")


class SecurityStatusWidget(Static):
    """Security status display."""

    def compose(self) -> ComposeResult:
        """Compose security status."""
        yield Static("[bold]Security Status[/bold]", classes="metric-label")

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
            fv_status = "✓ On" if fv_enabled else "✗ Off"
            fv_color = "green" if fv_enabled else "yellow"
            yield Static(
                f"[cyan]FileVault:[/cyan] [{fv_color}]{fv_status}[/{fv_color}]"
            )
        except Exception:
            yield Static("[cyan]FileVault:[/cyan] [yellow]Unknown[/yellow]")


class MaintenanceStatusWidget(Static):
    """Maintenance status and recommendations."""

    def compose(self) -> ComposeResult:
        """Compose maintenance status."""
        yield Static("[bold]Maintenance Status[/bold]", classes="metric-label")

        # Check for recent maintenance logs
        log_dir = Path.home() / "Library" / "Logs" / "upkeep"
        last_run = "Never"
        next_recommended = "Now"

        try:
            if log_dir.exists():
                log_files = sorted(log_dir.glob("upkeep-*.log"), reverse=True)
                if log_files:
                    # Get most recent log file modification time
                    last_log = log_files[0]
                    mtime = datetime.fromtimestamp(last_log.stat().st_mtime)
                    last_run = mtime.strftime("%Y-%m-%d %H:%M")

                    # Calculate next recommended (7 days from last run)
                    days_since = (datetime.now() - mtime).days
                    if days_since < 7:
                        next_recommended = f"{7 - days_since} days"
                    else:
                        next_recommended = "Now (overdue)"
        except Exception:
            pass

        yield Static(f"[cyan]Last Run:[/cyan] {last_run}")
        yield Static(f"[cyan]Next Recommended:[/cyan] {next_recommended}")
        yield Static("\n[dim]Use keyboard shortcuts to navigate:[/dim]")
        yield Static("[dim]  m - Maintenance operations[/dim]")
        yield Static("[dim]  s - Storage analysis[/dim]")
        yield Static("[dim]  r - Refresh dashboard[/dim]")


class DashboardView(VerticalScroll):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        # Header
        yield Static(
            "[bold cyan]System Health Dashboard[/bold cyan]\n",
            classes="section-header",
        )

        # Simplified single-column layout for reliability
        yield DiskUsageWidget(classes="box")
        yield SystemInfoWidget(classes="box")
        yield SecurityStatusWidget(classes="box")
        yield MaintenanceStatusWidget(classes="box")

        # Overall status at bottom
        health_score = self.calculate_health_score()
        health_status, health_color = self.get_health_status(health_score)
        yield Static(
            f"\n[bold]Overall System Health:[/bold] "
            f"[{health_color}]● {health_status}[/{health_color}] "
            f"(Score: {health_score}/100)",
            classes="status-box"
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
    height: 1fr;
    overflow-y: auto;
}

.section-header {
    text-style: bold;
    color: $accent;
    margin: 1 0;
}

#dashboard-grid {
    grid-size: 2 1;
    grid-columns: 1fr 1fr;
    height: auto;
    margin: 1 0;
}

.box {
    border: solid $primary;
    background: $panel;
    padding: 1 2;
    margin: 0 1 1 1;
    min-height: 5;
}

.status-box {
    margin: 1;
}

.metric-label {
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.metric-value {
    color: $text;
}

.metric-value-warning {
    color: $warning;
}

.metric-value-error {
    color: $error;
}

#quick-action-buttons {
    height: auto;
    width: 100%;
}

#quick-action-buttons Button {
    width: 1fr;
    margin: 1 1 1 0;
    min-height: 3;
}
"""
