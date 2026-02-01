"""Web interface for mac-maintenance toolkit.

Provides FastAPI-based REST API and web UI for system maintenance operations.
"""

from mac_maintenance.web.server import app

__all__ = ["app"]
