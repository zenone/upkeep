"""
Storage analysis view for TUI.

Displays storage breakdown and analysis.
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Input, DataTable
from textual.reactive import reactive
from textual.screen import ModalScreen

from ..api import StorageAPI


class DeleteConfirmDialog(ModalScreen[bool]):
    """Modal confirmation dialog for file deletion."""

    def __init__(self, path: Path, is_dir: bool, file_size: int):
        """
        Initialize the delete confirmation dialog.

        Args:
            path: Path to file/directory to delete
            is_dir: True if path is a directory
            file_size: Size in bytes
        """
        super().__init__()
        self.file_path = path
        self.file_is_dir = is_dir
        self.file_size = file_size

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        size_gb = self.file_size / (1024**3)
        item_type = "Directory" if self.file_is_dir else "File"

        with Vertical(id="dialog"):
            yield Static("[bold red]Confirm Deletion[/bold red]")
            yield Static(f"\n{item_type}: [cyan]{self.file_path}[/cyan]")
            yield Static(f"Size: [yellow]{size_gb:.2f} GB[/yellow]")
            yield Static("\n[red]This action cannot be undone![/red]")
            with Horizontal(id="dialog-buttons"):
                yield Button("Delete", variant="error", id="confirm")
                yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class StorageView(VerticalScroll):
    """Storage analysis view."""

    analyzing = reactive(False)
    current_entries = []
    _button_id_counter = 0  # Counter for unique button IDs (fixes Textual duplicate ID issue)

    def __init__(self, *args, **kwargs):
        """Initialize storage view with API."""
        super().__init__(*args, **kwargs)
        self.storage_api = StorageAPI()

    def compose(self) -> ComposeResult:
        """Compose the storage view."""
        yield Static("[bold]Storage Analysis[/bold]\n")

        # Path input and analyze button
        with Horizontal():
            yield Input(
                placeholder="Enter path to analyze...",
                value=str(Path.home()),
                id="path-input",
            )
            yield Button("Analyze", variant="success", id="analyze-button")

        # Results container
        yield Vertical(id="results-container")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.analyze_path(Path.home())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "analyze-button":
            path_input = self.query_one("#path-input", Input)
            path = Path(path_input.value)
            self.analyze_path(path)
        elif event.button.id and event.button.id.startswith("delete-selected"):
            # Get selected row from table
            try:
                # Query for DataTable within results container
                tables = self.query_one("#results-container").query(DataTable)
                if not tables:
                    self.app.notify("No table found. Please analyze a path first.", severity="warning")
                    return

                table = tables.first()

                # Check if table has focus and a valid cursor
                if table.cursor_row is None or table.cursor_row < 0:
                    self.app.notify("No item selected. Use arrow keys to select an item first.", severity="warning")
                    return

                cursor_idx = table.cursor_row
                if cursor_idx >= len(self.current_entries):
                    self.app.notify("Invalid selection. Please try again.", severity="error")
                    return

                entry = self.current_entries[cursor_idx]
                self.confirm_delete(entry)
            except Exception as e:
                self.app.notify(f"Error: {e}", severity="error")

    def confirm_delete(self, entry) -> None:
        """Show confirmation dialog and delete if confirmed."""
        def handle_confirm(confirmed: bool) -> None:
            if confirmed:
                self.delete_item(entry)

        self.app.push_screen(
            DeleteConfirmDialog(entry.path, entry.is_dir, entry.size),
            handle_confirm
        )

    def delete_item(self, entry) -> None:
        """Delete a file or directory using StorageAPI."""
        path = entry.path

        # Use API to delete
        result = self.storage_api.delete_path(path)

        if result['success']:
            item_type = "directory" if entry.is_dir else "file"
            self.app.notify(f"Deleted {item_type}: {path.name}", severity="information")
            self.refresh_data()
        else:
            self.app.notify(f"Error: {result['error']}", severity="error")

    def analyze_path(self, path: Path) -> None:
        """Analyze the given path."""
        if self.analyzing:
            return

        self.analyzing = True
        self.app.update_status(f"⟳ Analyzing: {path}")
        self.app.notify(f"Analyzing: {path}", severity="information")

        try:
            # Run analysis using StorageAPI
            result = self.storage_api.analyze_path(path, max_depth=3, max_entries=15)

            # Handle errors
            if not result.success:
                self.app.notify(result.error, severity="error")
                self.app.update_status(f"✗ {result.error}")
                return

            # Store entries for deletion (convert API result dicts back to simple objects)
            from collections import namedtuple
            Entry = namedtuple('Entry', ['path', 'size', 'is_dir'])
            self.current_entries = [
                Entry(Path(e['path']), e['size_bytes'], e['is_dir'])
                for e in result.largest_entries
            ]

            # Clear results
            results = self.query_one("#results-container", Vertical)
            results.remove_children()

            # Add summary
            results.mount(Static(f"\n[bold]Analysis Results: {path}[/bold]"))
            results.mount(Static(f"Total Size: [green]{result.total_size_gb:.2f} GB[/green]"))
            results.mount(Static(f"Files: [cyan]{result.file_count:,}[/cyan]"))
            results.mount(Static(f"Directories: [cyan]{result.dir_count:,}[/cyan]\n"))

            # Category breakdown
            if any(size > 0 for size in result.category_sizes.values()):
                results.mount(Static("[bold]Storage by Category[/bold]"))

                sorted_cats = sorted(
                    [(cat, size) for cat, size in result.category_sizes.items() if size > 0],
                    key=lambda x: x[1],
                    reverse=True,
                )

                for category, size in sorted_cats:
                    percentage = (size / result.total_size_bytes * 100) if result.total_size_bytes > 0 else 0
                    size_gb = size / (1024**3)
                    bar_width = int(percentage / 2)
                    bar = "█" * bar_width + "░" * (50 - bar_width)

                    colors = {
                        "images": "cyan", "videos": "magenta", "audio": "yellow",
                        "documents": "blue", "archives": "red", "code": "green",
                    }
                    color = colors.get(category, "white")

                    results.mount(Static(
                        f"[{color}]{category.title():15}[/{color}] "
                        f"[{color}]{bar}[/{color}] "
                        f"{percentage:5.1f}% ({size_gb:.2f} GB)"
                    ))

                results.mount(Static(""))

            # Largest files table
            if self.current_entries:
                results.mount(Static("[bold]Largest Items[/bold]"))
                results.mount(Static("[dim]Use arrow keys to navigate, press Delete button below[/dim]\n"))

                # Create table (no fixed ID to avoid conflicts on refresh)
                table = DataTable(zebra_stripes=True, cursor_type="row")
                table.add_column("Path")
                table.add_column("Size")
                table.add_column("Type")

                for entry in self.current_entries:
                    size_str = self._format_size(entry.size)
                    type_str = "DIR" if entry.is_dir else "FILE"
                    path_str = str(entry.path)

                    # Add row to table
                    table.add_row(path_str, size_str, type_str)

                results.mount(table)

                # Add delete button below table
                # FIX: Use unique ID each time to avoid Textual duplicate ID registry issue
                # See: https://github.com/Textualize/textual/issues/5215
                # Textual's ID registry doesn't clear immediately when widgets are removed
                # Using incrementing counter ensures each mount gets unique ID
                self._button_id_counter += 1
                button_id = f"delete-selected-{self._button_id_counter}"

                delete_btn = Button("Delete Selected Item", variant="error", id=button_id)
                results.mount(delete_btn)

            self.app.notify("Analysis complete!", severity="information")
            self.app.update_status("✓ Analysis complete")

        except FileNotFoundError:
            self.app.notify(f"Path not found: {path}", severity="error")
            self.app.update_status("✗ Path not found")
        except PermissionError:
            self.app.notify(f"Permission denied: {path}", severity="error")
            self.app.update_status("✗ Permission denied")
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")
            self.app.update_status("✗ Analysis error")
        finally:
            self.analyzing = False

    def _format_size(self, size: int) -> str:
        """Format size to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def refresh_data(self) -> None:
        """Refresh storage analysis."""
        path_input = self.query_one("#path-input", Input)
        path = Path(path_input.value)
        self.analyze_path(path)


StorageView.DEFAULT_CSS = """
StorageView {
    height: 1fr;
}

StorageView Input {
    width: 1fr;
}

StorageView Button {
    width: auto;
    min-width: 10;
    margin-left: 1;
}

#analyze-button {
    min-width: 15;
}

#results-container {
    height: auto;
    margin-top: 2;
}

#results-container DataTable {
    height: auto;
    max-height: 20;
    margin: 1 0;
}

#delete-selected {
    width: auto;
    min-width: 25;
    margin: 1 0;
}

DeleteConfirmDialog {
    align: center middle;
}

#dialog {
    width: 70;
    height: auto;
    border: thick $primary;
    background: $panel;
    padding: 2;
}

#dialog-buttons {
    width: 100%;
    align: center middle;
    margin-top: 1;
}

#dialog-buttons Button {
    margin: 0 1;
}
"""
