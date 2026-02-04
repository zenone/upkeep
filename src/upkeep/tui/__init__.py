"""
Terminal User Interface (TUI) components.

This module provides an interactive terminal interface using Textual:
- Dashboard view
- System health monitoring
- Interactive maintenance controls
- Real-time progress tracking
- Keyboard navigation
"""


def __getattr__(name: str):
    """Lazy imports to avoid circular import warnings with python -m."""
    if name == "MacMaintenanceTUI":
        from .app import MacMaintenanceTUI
        return MacMaintenanceTUI
    if name == "run":
        from .app import run
        return run
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MacMaintenanceTUI", "run"]
