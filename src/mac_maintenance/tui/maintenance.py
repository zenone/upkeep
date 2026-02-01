"""
Maintenance operations view with checkbox selection.

Enhanced UX: Select multiple operations, run as batch with progress tracking.
"""

import asyncio
from pathlib import Path
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Checkbox
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.worker import Worker, WorkerState


class BatchConfirmDialog(ModalScreen[bool]):
    """Confirmation dialog showing all selected operations."""

    def __init__(self, operations: list[tuple[str, str]]):
        """
        Initialize the confirmation dialog.

        Args:
            operations: List of (name, command) tuples for operations to confirm
        """
        super().__init__()
        self.operations = operations

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Vertical(id="dialog"):
            yield Static(f"[bold cyan]Run {len(self.operations)} Maintenance Operations?[/bold cyan]")
            yield Static("\n[bold]Selected Operations:[/bold]")

            for name, _ in self.operations:
                yield Static(f"  • {name}")

            yield Static("\n[yellow]⚠ This will run all operations sequentially.[/yellow]")
            yield Static("[dim]You can cancel anytime with Ctrl+C[/dim]\n")

            with Horizontal(id="dialog-buttons"):
                yield Button("Run All", variant="success", id="confirm")
                yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events in the confirmation dialog.

        Args:
            event: Button pressed event containing button ID
        """
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class MaintenanceView(VerticalScroll):
    """Enhanced maintenance view with checkbox selection."""

    running_batch = reactive(False)
    operations_run = reactive(0)
    operations_total = reactive(0)
    skip_requested = False

    # Define all operations with metadata
    OPERATIONS = {
        # System Updates
        "macos-check": {
            "name": "Check macOS Updates",
            "category": "System Updates",
            "command": ["./maintain.sh", "--list-macos-updates"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "macos-install": {
            "name": "Install macOS Updates",
            "category": "System Updates",
            "command": ["./maintain.sh", "--install-macos-updates", "--assume-yes"],
            "safe": False,
            "regular": False,
            "deep": True,
        },
        "brew-update": {
            "name": "Update Homebrew",
            "category": "System Updates",
            "command": ["./maintain.sh", "--brew", "--assume-yes"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "mas-update": {
            "name": "Update App Store Apps",
            "category": "System Updates",
            "command": ["./maintain.sh", "--mas", "--assume-yes"],
            "safe": True,
            "regular": True,
            "deep": True,
        },

        # Disk Operations
        "disk-verify": {
            "name": "Verify Disk",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--verify-disk"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "disk-repair": {
            "name": "Repair Disk",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--repair-disk", "--assume-yes"],
            "safe": False,
            "regular": False,
            "deep": True,
        },
        "smart-check": {
            "name": "Check SMART Status",
            "category": "Disk Operations",
            "command": ["./maintain.sh", "--smart"],
            "safe": True,
            "regular": True,
            "deep": True,
        },

        # Cleanup Operations
        "trim-logs": {
            "name": "Trim User Logs (30+ days)",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--trim-logs", "30", "--assume-yes"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "trim-caches": {
            "name": "Trim User Caches (30+ days)",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--trim-caches", "30", "--assume-yes"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "thin-tm": {
            "name": "Thin Time Machine Snapshots",
            "category": "Cleanup Operations",
            "command": ["./maintain.sh", "--thin-tm-snapshots", "--assume-yes"],
            "safe": False,
            "regular": False,
            "deep": True,
        },

        # System Operations
        "spotlight-status": {
            "name": "Check Spotlight Status",
            "category": "System Operations",
            "command": ["./maintain.sh", "--spotlight-status"],
            "safe": True,
            "regular": False,
            "deep": True,
        },
        "spotlight-reindex": {
            "name": "Rebuild Spotlight Index",
            "category": "System Operations",
            "command": ["./maintain.sh", "--spotlight-reindex", "--assume-yes"],
            "safe": False,
            "regular": False,
            "deep": True,
        },
        "dns-flush": {
            "name": "Flush DNS Cache",
            "category": "System Operations",
            "command": ["./maintain.sh", "--flush-dns", "--assume-yes"],
            "safe": True,
            "regular": True,
            "deep": True,
        },
        "periodic": {
            "name": "Run Periodic Scripts",
            "category": "System Operations",
            "command": ["./maintain.sh", "--periodic", "--assume-yes"],
            "safe": True,
            "regular": False,
            "deep": True,
        },

        # Reports
        "space-report": {
            "name": "Disk Space Report",
            "category": "Reports & Analysis",
            "command": ["./maintain.sh", "--space-report"],
            "safe": True,
            "regular": False,
            "deep": False,
        },
        "security-audit": {
            "name": "Security Audit",
            "category": "Reports & Analysis",
            "command": ["./maintain.sh", "--security-audit"],
            "safe": True,
            "regular": False,
            "deep": False,
        },
    }

    def compose(self) -> ComposeResult:
        """Compose the maintenance view."""
        yield Static("[bold cyan]Maintenance Operations[/bold cyan]", id="header")
        yield Static(
            "[yellow]⚠[/yellow] Select operations to run. "
            "[green]Regular Maintenance[/green] is pre-selected.\n",
            id="description"
        )

        # Quick preset buttons
        yield Static("[bold]Quick Presets:[/bold]")
        with Horizontal(id="preset-buttons"):
            yield Button("Regular Maintenance", variant="success", id="preset-regular")
            yield Button("Deep Clean", variant="warning", id="preset-deep")
            yield Button("Clear All", variant="default", id="preset-clear")

        # Group operations by category
        categories = {}
        for op_id, op_data in self.OPERATIONS.items():
            cat = op_data["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((op_id, op_data))

        # Render each category
        for category in ["System Updates", "Disk Operations", "Cleanup Operations", "System Operations", "Reports & Analysis"]:
            if category in categories:
                yield Static(f"\n[bold]{category}[/bold]")
                for op_id, op_data in categories[category]:
                    # Check by default if it's in "regular" maintenance
                    yield Checkbox(
                        op_data["name"],
                        value=op_data["regular"],
                        id=f"cb-{op_id}"
                    )

        # Action buttons - prominently placed
        yield Static("\n[bold cyan]Actions[/bold cyan]")
        yield Button("✓ Run Selected Operations", variant="success", id="run-selected")
        yield Button("⏭ Skip Current Task", variant="warning", id="skip-current", disabled=True)
        yield Button("✖ Cancel All", variant="error", id="cancel-queue", disabled=True)

        # Output area
        yield Static("\n[bold]Progress & Output[/bold]")
        yield Static("[dim]Operation output will appear here[/dim]", id="progress-summary")
        with VerticalScroll(id="operation-output"):
            yield Static("[dim]Ready to run operations[/dim]")

    def on_mount(self) -> None:
        """Apply regular maintenance preset on mount."""
        # Regular preset is already set via value=op_data["regular"] in compose
        self.update_summary()
        # Initialize subprocess tracking for cancellation
        self._current_proc = None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "preset-regular":
            self.apply_preset("regular")
        elif event.button.id == "preset-deep":
            self.apply_preset("deep")
        elif event.button.id == "preset-clear":
            self.apply_preset("clear")
        elif event.button.id == "run-selected":
            self.start_batch()
        elif event.button.id == "skip-current":
            self.skip_current_task()
        elif event.button.id == "cancel-queue":
            self.cancel_batch()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Update summary when checkboxes change."""
        self.update_summary()

    def apply_preset(self, preset: str) -> None:
        """Apply a preset selection."""
        for op_id, op_data in self.OPERATIONS.items():
            checkbox = self.query_one(f"#cb-{op_id}", Checkbox)

            if preset == "regular":
                checkbox.value = op_data["regular"]
            elif preset == "deep":
                checkbox.value = op_data["deep"]
            elif preset == "clear":
                checkbox.value = False

        self.update_summary()
        self.app.notify(f"Applied preset: {preset.title()}", severity="information")

    def update_summary(self) -> None:
        """Update the summary of selected operations."""
        selected = self.get_selected_operations()
        count = len(selected)

        summary = self.query_one("#progress-summary", Static)
        if count == 0:
            summary.update("[dim]No operations selected[/dim]")
        else:
            summary.update(f"[cyan]{count} operation{'s' if count != 1 else ''} selected[/cyan]")

    def get_selected_operations(self) -> list[tuple[str, str, list[str]]]:
        """Get list of selected operations."""
        selected = []
        for op_id, op_data in self.OPERATIONS.items():
            try:
                checkbox = self.query_one(f"#cb-{op_id}", Checkbox)
                if checkbox.value:
                    selected.append((op_id, op_data["name"], op_data["command"]))
            except Exception as e:
                # Log specific error for debugging (widget may not be mounted yet)
                # Only log if app context is available
                try:
                    self.log.warning(f"Could not query checkbox for {op_id}: {e}")
                except Exception:
                    # App context not available (e.g., in unit tests)
                    pass
        return selected

    def start_batch(self) -> None:
        """Start batch execution of selected operations."""
        if self.running_batch:
            self.app.notify("Operations already running", severity="warning")
            return

        selected = self.get_selected_operations()
        if not selected:
            self.app.notify("No operations selected", severity="warning")
            return

        # Show confirmation dialog
        def handle_confirm(confirmed: bool) -> None:
            if confirmed:
                self.execute_batch(selected)

        # Prepare operation list for dialog (name, command_str)
        op_list = [(name, ' '.join(cmd)) for _, name, cmd in selected]
        self.app.push_screen(BatchConfirmDialog(op_list), handle_confirm)

    def execute_batch(self, operations: list[tuple[str, str, list[str]]]) -> None:
        """Execute operations sequentially."""
        if self.running_batch:
            return

        self.running_batch = True
        self.operations_total = len(operations)
        self.operations_run = 0
        self.skip_requested = False

        # Enable cancel and skip buttons
        cancel_btn = self.query_one("#cancel-queue", Button)
        cancel_btn.disabled = False
        skip_btn = self.query_one("#skip-current", Button)
        skip_btn.disabled = False

        # Clear output
        output_area = self.query_one("#operation-output", VerticalScroll)
        output_area.remove_children()

        # Update status
        self.app.update_status(f"⟳ Running {len(operations)} operations")

        # Add batch header to output
        output_area.mount(Static("[bold cyan]" + "=" * 70 + "[/bold cyan]"))
        output_area.mount(Static(f"[bold cyan]MAINTENANCE BATCH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]"))
        output_area.mount(Static(f"[bold cyan]Running {len(operations)} operations sequentially[/bold cyan]"))
        output_area.mount(Static("[bold cyan]" + "=" * 70 + "[/bold cyan]\n"))

        # Run worker
        self.run_worker(self._run_batch_async(operations), exclusive=True)

    async def _run_batch_async(self, operations: list[tuple[str, str, list[str]]]) -> dict:
        """Run operations sequentially with progress tracking."""
        results = []
        output_area = self.query_one("#operation-output", VerticalScroll)

        for idx, (op_id, op_name, command) in enumerate(operations, 1):
            self.operations_run = idx

            # Update progress
            progress_summary = self.query_one("#progress-summary", Static)
            progress_summary.update(
                f"[cyan]Running {idx}/{len(operations)}: {op_name}[/cyan]"
            )
            self.app.update_status(f"⟳ [{idx}/{len(operations)}] {op_name}")

            # Add operation header
            output_area.mount(Static(f"\n[bold yellow]{'─' * 70}[/bold yellow]"))
            output_area.mount(Static(f"[bold yellow][{idx}/{len(operations)}] {op_name}[/bold yellow]"))
            output_area.mount(Static(f"[dim]Command: {' '.join(command)}[/dim]"))
            output_area.mount(Static(f"[bold yellow]{'─' * 70}[/bold yellow]\n"))

            # Execute operation
            result = await self._run_single_operation(op_name, command, output_area)

            # Check if skip was requested
            if self.skip_requested:
                self.skip_requested = False
                result = {"success": False, "error": "Skipped by user", "skipped": True}

            results.append((op_name, result))

            # Add result indicator
            if result.get("skipped"):
                output_area.mount(Static(f"\n[yellow]⏭ {op_name} skipped[/yellow]\n"))
            elif result.get("success"):
                output_area.mount(Static(f"\n[green]✓ {op_name} completed successfully[/green]\n"))
            else:
                error = result.get("error", "Unknown error")
                output_area.mount(Static(f"\n[red]✗ {op_name} failed: {error}[/red]\n"))

            output_area.scroll_end(animate=False)

        # Add summary
        await self._add_batch_summary(operations, results, output_area)

        return {"operations": len(operations), "results": results}

    async def _run_single_operation(self, name: str, command: list, output_area) -> dict:
        """Run a single operation and stream output."""
        # Find maintain.sh
        script_path = Path(__file__).parent.parent.parent.parent / "maintain.sh"
        if not script_path.exists():
            script_path = Path.cwd() / "maintain.sh"

        if not script_path.exists():
            return {"success": False, "error": f"Cannot find maintain.sh at {script_path}"}

        # Update command with resolved path
        if command[0] == "./maintain.sh":
            command[0] = str(script_path)

        try:
            # Run command directly without sudo refresh attempt
            # The parent shell's keep-alive (run-tui.sh) maintains sudo timestamp
            # maintain.sh will handle sudo internally with -n flag
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=script_path.parent,
            )

            # Track subprocess for cancellation
            self._current_proc = proc

            # Stream output
            stdout_lines = []
            stderr_lines = []

            async def read_stdout():
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    stdout_lines.append(decoded)
                    output_area.mount(Static(decoded))
                    output_area.scroll_end(animate=False)  # Auto-scroll to show new output

            async def read_stderr():
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    stderr_lines.append(decoded)
                    output_area.mount(Static(f"[yellow]{decoded}[/yellow]"))
                    output_area.scroll_end(animate=False)  # Auto-scroll to show new output

            await asyncio.gather(read_stdout(), read_stderr())
            await asyncio.wait_for(proc.wait(), timeout=1800)

            # Clear subprocess tracking
            self._current_proc = None

            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": "\n".join(stdout_lines),
                "stderr": "\n".join(stderr_lines),
            }

        except asyncio.TimeoutError:
            # Clear subprocess tracking
            self._current_proc = None
            return {"success": False, "error": "Operation timed out (30 minute limit)"}
        except Exception as e:
            # Clear subprocess tracking
            self._current_proc = None
            return {"success": False, "error": str(e)}

    async def _add_batch_summary(self, operations, results, output_area) -> None:
        """Add summary at the end of batch execution."""
        output_area.mount(Static("\n"))
        output_area.mount(Static("[bold cyan]" + "=" * 70 + "[/bold cyan]"))
        output_area.mount(Static("[bold cyan]BATCH EXECUTION SUMMARY[/bold cyan]"))
        output_area.mount(Static("[bold cyan]" + "=" * 70 + "[/bold cyan]\n"))

        successful = sum(1 for _, result in results if result.get("success"))
        skipped = sum(1 for _, result in results if result.get("skipped"))
        failed = len(results) - successful - skipped

        output_area.mount(Static(f"[bold]Total Operations:[/bold] {len(results)}"))
        output_area.mount(Static(f"[green]✓ Successful:[/green] {successful}"))
        if skipped > 0:
            output_area.mount(Static(f"[yellow]⏭ Skipped:[/yellow] {skipped}"))
        output_area.mount(Static(f"[red]✗ Failed:[/red] {failed}\n"))

        if failed > 0:
            output_area.mount(Static("[bold]Failed Operations:[/bold]"))
            for op_name, result in results:
                if not result.get("success") and not result.get("skipped"):
                    error = result.get("error", "Unknown error")
                    output_area.mount(Static(f"  • {op_name}: {error}"))

        output_area.mount(Static("\n[bold cyan]" + "=" * 70 + "[/bold cyan]"))
        output_area.mount(Static(f"[bold cyan]Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]"))
        output_area.mount(Static("[bold cyan]" + "=" * 70 + "[/bold cyan]"))

        # Save log file
        await self._save_log_file(operations, results)

    async def _save_log_file(self, operations, results) -> None:
        """Save batch execution log to file."""
        try:
            log_dir = Path.home() / "Library" / "Logs" / "mac-maintenance"
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = log_dir / f"mac-maintenance-{timestamp}.log"

            with open(log_file, 'w') as f:
                f.write(f"MAC MAINTENANCE BATCH LOG\n")
                f.write(f"{'=' * 70}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Operations: {len(operations)}\n")
                f.write(f"{'=' * 70}\n\n")

                for op_name, result in results:
                    f.write(f"\n{'─' * 70}\n")
                    f.write(f"Operation: {op_name}\n")
                    f.write(f"Status: {'✓ Success' if result.get('success') else '✗ Failed'}\n")
                    f.write(f"{'─' * 70}\n")

                    if result.get("stdout"):
                        f.write(f"\nOutput:\n{result['stdout']}\n")

                    if result.get("stderr"):
                        f.write(f"\nErrors:\n{result['stderr']}\n")

                    if result.get("error"):
                        f.write(f"\nError: {result['error']}\n")

                # Summary
                successful = sum(1 for _, result in results if result.get("success"))
                failed = len(results) - successful

                f.write(f"\n{'=' * 70}\n")
                f.write(f"SUMMARY\n")
                f.write(f"{'=' * 70}\n")
                f.write(f"Total: {len(results)}\n")
                f.write(f"Successful: {successful}\n")
                f.write(f"Failed: {failed}\n")
                f.write(f"{'=' * 70}\n")

            output_area = self.query_one("#operation-output", VerticalScroll)
            output_area.mount(Static(f"\n[dim]Log saved: {log_file}[/dim]"))

        except Exception as e:
            self.app.notify(f"Could not save log: {e}", severity="warning")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion."""
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result

            # Update UI
            progress_summary = self.query_one("#progress-summary", Static)
            progress_summary.update(
                f"[green]✓ Batch complete: {result['operations']} operations[/green]"
            )

            self.app.update_status("✓ Batch execution complete")
            self.app.notify("All operations completed", severity="information")

            # Disable cancel and skip buttons
            cancel_btn = self.query_one("#cancel-queue", Button)
            cancel_btn.disabled = True
            skip_btn = self.query_one("#skip-current", Button)
            skip_btn.disabled = True

            self.running_batch = False

        elif event.state in (WorkerState.ERROR, WorkerState.CANCELLED):
            progress_summary = self.query_one("#progress-summary", Static)
            progress_summary.update("[red]✗ Batch cancelled or failed[/red]")

            self.app.update_status("✗ Batch execution stopped")
            self.app.notify("Operations cancelled", severity="warning")

            cancel_btn = self.query_one("#cancel-queue", Button)
            cancel_btn.disabled = True
            skip_btn = self.query_one("#skip-current", Button)
            skip_btn.disabled = True

            self.running_batch = False

    def cancel_batch(self) -> None:
        """Cancel the running batch."""
        # Kill current subprocess if running
        if hasattr(self, '_current_proc') and self._current_proc:
            try:
                self._current_proc.kill()
                self.app.notify("Killing current operation...", severity="warning")
            except ProcessLookupError:
                # Process already terminated
                pass
            except Exception as e:
                # Log error but continue with worker cancellation
                self.app.notify(f"Could not kill process: {e}", severity="warning")
            finally:
                self._current_proc = None

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        self.app.notify("Cancelling operations...", severity="warning")

    def skip_current_task(self) -> None:
        """Skip the current task and continue with remaining tasks."""
        self.skip_requested = True

        # Kill current subprocess if running
        if hasattr(self, '_current_proc') and self._current_proc:
            try:
                self._current_proc.kill()
                self.app.notify("Skipping current task...", severity="information")
            except ProcessLookupError:
                pass
            except Exception as e:
                self.app.notify(f"Could not kill process: {e}", severity="warning")
            finally:
                self._current_proc = None

    def refresh_data(self) -> None:
        """Refresh maintenance view."""
        self.app.notify("Maintenance view refreshed", severity="information")


# CSS
MaintenanceView.DEFAULT_CSS = """
MaintenanceView {
    height: 1fr;
}

#header {
    margin: 0 0 1 0;
}

#description {
    margin: 0 0 1 0;
}

#preset-buttons {
    margin: 1 0 2 0;
}

#preset-buttons Button {
    margin: 0 1 0 0;
    min-width: 20;
}

MaintenanceView Checkbox {
    margin: 0 0 1 2;
}

/* Make checkbox states highly distinguishable */
MaintenanceView Checkbox:focus {
    border: tall $accent;
}

MaintenanceView Checkbox:hover {
    border: tall $accent;
}

#run-selected, #skip-current, #cancel-queue {
    margin: 1 0;
    min-width: 25;
}

#progress-summary {
    margin: 1 0 1 0;
}

#operation-output {
    height: 25;
    border: solid $primary;
    background: $surface;
    padding: 1;
    margin: 1 0;
}

BatchConfirmDialog {
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
