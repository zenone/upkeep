"""
Tests for TUI application.

Basic smoke tests to ensure TUI components can be imported and instantiated.
"""

import pytest
from mac_maintenance.tui import MacMaintenanceTUI
from mac_maintenance.tui.dashboard import DashboardView, DiskUsageWidget, MetricBox
from mac_maintenance.tui.storage import StorageView
from mac_maintenance.tui.about import AboutView


class TestTUIImports:
    """Test that TUI components can be imported."""

    def test_import_main_app(self) -> None:
        """Test importing main TUI app."""
        assert MacMaintenanceTUI is not None
        assert hasattr(MacMaintenanceTUI, "run")

    def test_import_dashboard(self) -> None:
        """Test importing dashboard components."""
        assert DashboardView is not None
        assert DiskUsageWidget is not None
        assert MetricBox is not None

    def test_import_storage(self) -> None:
        """Test importing storage view."""
        assert StorageView is not None

    def test_import_about(self) -> None:
        """Test importing about view."""
        assert AboutView is not None


class TestTUIInstantiation:
    """Test that TUI components can be instantiated."""

    def test_create_app(self) -> None:
        """Test creating TUI app instance."""
        app = MacMaintenanceTUI()
        assert app is not None
        assert app.TITLE == "macOS Maintenance Toolkit"
        assert "3.0.0" in app.SUB_TITLE

    def test_app_has_bindings(self) -> None:
        """Test that app has keyboard bindings."""
        app = MacMaintenanceTUI()
        assert len(app.BINDINGS) > 0

        # Check for key bindings
        binding_keys = [b.key for b in app.BINDINGS]
        assert "q" in binding_keys  # Quit
        assert "r" in binding_keys  # Refresh
        assert "?" in binding_keys  # Help

    def test_metric_box_creation(self) -> None:
        """Test creating metric box widget."""
        box = MetricBox("Test Label", "Test Value", status="normal")
        assert box.metric_label == "Test Label"
        assert box.metric_value == "Test Value"
        assert box.status == "normal"

    def test_metric_box_statuses(self) -> None:
        """Test metric box with different statuses."""
        normal = MetricBox("Label", "Value", status="normal")
        warning = MetricBox("Label", "Value", status="warning")
        error = MetricBox("Label", "Value", status="error")

        assert normal.status == "normal"
        assert warning.status == "warning"
        assert error.status == "error"


class TestDashboardView:
    """Test dashboard view components."""

    def test_create_dashboard(self) -> None:
        """Test creating dashboard view."""
        dashboard = DashboardView()
        assert dashboard is not None

    def test_health_score_calculation(self) -> None:
        """Test health score calculation."""
        dashboard = DashboardView()
        score = dashboard.calculate_health_score()

        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, int)

    def test_health_status_messages(self) -> None:
        """Test health status messages."""
        dashboard = DashboardView()

        # Test different score ranges
        excellent = dashboard.get_health_status(95)
        assert excellent[0] == "Excellent"
        assert excellent[1] == "green"

        good = dashboard.get_health_status(75)
        assert good[0] == "Good"
        assert good[1] == "cyan"

        fair = dashboard.get_health_status(55)
        assert fair[0] == "Fair"
        assert fair[1] == "yellow"

        poor = dashboard.get_health_status(30)
        assert poor[0] == "Poor"
        assert poor[1] == "red"


class TestStorageView:
    """Test storage view components."""

    def test_create_storage_view(self) -> None:
        """Test creating storage view."""
        storage = StorageView()
        assert storage is not None
        assert hasattr(storage, "analyze_path")

    def test_storage_view_defaults(self) -> None:
        """Test storage view default values."""
        storage = StorageView()
        assert storage.analyzing is False


class TestAboutView:
    """Test about view."""

    def test_create_about_view(self) -> None:
        """Test creating about view."""
        about = AboutView()
        assert about is not None
