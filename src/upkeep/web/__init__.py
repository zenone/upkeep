"""Web interface for upkeep toolkit.

Provides FastAPI-based REST API and web UI for system maintenance operations.
"""

from upkeep.web.server import app

__all__ = ["app"]
