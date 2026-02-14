"""
Base API class for Upkeep.

All API classes inherit from BaseAPI to ensure consistent
logging, error handling, and behavior.
"""

import logging
from typing import Any

from upkeep.core.exceptions import APIError, MacMaintenanceError


class BaseAPI:
    """Base class for all API classes.

    Provides common functionality:
    - Structured logging
    - Consistent error handling
    - Result validation

    API-First Design:
    - All API methods are synchronous by default
    - Async methods use 'async def' explicitly
    - All methods have type hints
    - All methods return typed objects (not dicts)
    """

    def __init__(self):
        """Initialize the API with logger."""
        self.logger = logging.getLogger(f"api.{self.__class__.__name__}")
        self.logger.debug(f"{self.__class__.__name__} initialized")

    def _handle_error(self, e: Exception) -> MacMaintenanceError:
        """Convert exceptions to API errors.

        Args:
            e: Original exception

        Returns:
            MacMaintenanceError (or subclass) to raise
        """
        # If already a MacMaintenanceError, return as-is
        if isinstance(e, MacMaintenanceError):
            self.logger.warning(f"{e.__class__.__name__}: {e.message}")
            return e

        # Otherwise, wrap in APIError
        self.logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        return APIError.from_exception(e)

    def _log_call(self, method: str, **kwargs: Any) -> None:
        """Log an API method call.

        Args:
            method: Method name being called
            **kwargs: Arguments passed to method (for debugging)
        """
        # Sanitize kwargs for logging (remove sensitive data if any)
        safe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        self.logger.info(f"{method} called", extra={"call_args": safe_kwargs})

    def _log_error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message to log
        """
        self.logger.error(message)

    def _validate_path(self, path: str | Any) -> None:
        """Validate that a path is a string.

        Args:
            path: Path to validate

        Raises:
            ValidationError: If path is not a string
        """
        from upkeep.core.exceptions import ValidationError

        if not isinstance(path, (str, type(None))):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}", field="path")
