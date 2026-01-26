"""
Storage analysis view for TUI.

Displays storage breakdown and analysis with beautiful visualizations.
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, DataTable, Button, Input, Label, ProgressBar
from textual.reactive import reactive

from ..storage.analyzer import DiskAnalyzer, CATEGORY_PATTERNS


class CategoryChart(Static):
    """Visual chart for category breakdown."""

    def __init__(self, categories: dict[str, int], total_size: int, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories
        self.total_size = total_size

    def compose(self) -> ComposeResult:
        """Compose the category chart."""
        yield Static("[bold]Storage by Category[/bold]", classes="metric-label")

        # Sort categories by size
        sorted_cats = sorted(
            [(cat, size) for cat, size in self.categories.items() if size > 0],
            key=lambda x: x[1],
            reverse=True,
        )

        for category, size in sorted_cats:
            percentage = (size / self.total_size * 100) if self.total_size > 0 else 0
            size_gb = size / (1024**3)

            # Create visual bar
            bar_width = int(percentage / 2)  # Scale to fit
            bar = "█" * bar_width + "░" * (50 - bar_width)

            color = self._get_category_color(category)
            yield Static(
                f"[{color}]{category.title():15}[/{color}] "
                f"[{color}]{bar}[/{color}] "
                f"{percentage:5.1f}% ({size_gb:.2f} GB)"
            )

    def _get_category_color(self, category: str) -> str:
        """Get color for category."""
        colors = {
            "images": "cyan",
            "videos": "magenta",
            "audio": "yellow",
            "documents": "blue",
            "archives": "red",
            "code": "green",
        }
        return colors.get(category, "white")


class LargestFilesTable(Static):
    """Table showing largest files."""

    def __init__(self, entries: list, **kwargs):
        super().__init__(**kwargs)
        self.entries = entries

    def compose(self) -> ComposeResult:
        """Compose the largest files table."""
        yield Static("[bold]Largest Items[/bold]", classes="metric-label")

        table = DataTable()
        table.add_columns("Path", "Size", "Type")

        for entry in self.entries[:15]:  # Top 15
            size_str = self._format_size(entry.size)
            type_str = "DIR" if entry.is_dir else "FILE"
            path_str = str(entry.path.name)  # Just filename for brevity

            # Color code by type
            if entry.is_dir:
                path_display = f"[cyan]{path_str}[/cyan]"
            else:
                path_display = path_str

            table.add_row(path_display, size_str, type_str)

        yield table

    def _format_size(self, size: int) -> str:
        """Format size to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class StorageView(Container):
    """Storage analysis view."""

    analysis_path = reactive(str(Path.home()))
    analyzing = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose the storage view."""
        yield Static("[bold]Storage Analysis[/bold]", classes="metric-label")

        # Path input and analyze button
        with Horizontal():
            yield Input(
                placeholder="Enter path to analyze...",
                value=str(Path.home()),
                id="path-input",
            )
            yield Button("Analyze", variant="success", id="analyze-button")

        # Results container
        yield ScrollableContainer(id="results-container")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Run initial analysis of home directory
        self.analyze_path(Path.home())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle analyze button press."""
        if event.button.id == "analyze-button":
            path_input = self.query_one("#path-input", Input)
            path = Path(path_input.value)
            self.analyze_path(path)

    def analyze_path(self, path: Path) -> None:
        """Analyze the given path."""
        if self.analyzing:
            return

        self.analyzing = True
        self.app.notify(f"Analyzing: {path}", severity="information")

        try:
            # Run analysis
            analyzer = DiskAnalyzer(path, max_depth=3)  # Limit depth for speed
            result = analyzer.analyze()

            # Clear and update results
            results = self.query_one("#results-container", ScrollableContainer)
            results.remove_children()

            # Add summary
            total_gb = result.total_size / (1024**3)
            with results:
                with Vertical(classes="box"):
                    yield Static(f"[bold]Analysis Results: {path}[/bold]")
                    yield Static(f"Total Size: [green]{total_gb:.2f} GB[/green]")
                    yield Static(f"Files: [cyan]{result.file_count:,}[/cyan]")
                    yield Static(f"Directories: [cyan]{result.dir_count:,}[/cyan]")

                # Category breakdown
                if any(size > 0 for size in result.category_sizes.values()):
                    with Vertical(classes="box"):
                        yield CategoryChart(result.category_sizes, result.total_size)

                # Largest files
                if result.entries:
                    with Vertical(classes="box"):
                        yield LargestFilesTable(result.get_largest_entries(15))

            self.app.notify("Analysis complete!", severity="information")

        except FileNotFoundError:
            self.app.notify(f"Path not found: {path}", severity="error")
        except PermissionError:
            self.app.notify(f"Permission denied: {path}", severity="error")
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
        finally:
            self.analyzing = False

    def refresh_data(self) -> None:
        """Refresh storage analysis."""
        path_input = self.query_one("#path-input", Input)
        path = Path(path_input.value)
        self.analyze_path(path)


StorageView.DEFAULT_CSS = """
StorageView {
    height: 100%;
}

#results-container {
    height: 1fr;
    margin: 1 0;
}

Input {
    width: 1fr;
}

Button {
    width: auto;
    min-width: 15;
}

DataTable {
    height: auto;
    max-height: 20;
}
"""
