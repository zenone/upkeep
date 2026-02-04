"""
Custom exceptions for Mac Maintenance.

Following API-First principles, all exceptions are specific and actionable.
"""


class MacMaintenanceError(Exception):
    """Base exception for all Mac Maintenance errors.

    All custom exceptions should inherit from this to allow
    catching all application-specific errors.
    """

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


# Storage-related exceptions
class PathNotFoundError(MacMaintenanceError):
    """Path does not exist."""
    pass


class PathNotReadableError(MacMaintenanceError):
    """Path exists but cannot be read (permission denied)."""
    pass


class PathProtectedError(MacMaintenanceError):
    """Path is protected and cannot be modified (system directory)."""
    pass


class PathNotWritableError(MacMaintenanceError):
    """Path exists but cannot be written to."""
    pass


# Maintenance operation exceptions
class OperationNotFoundError(MacMaintenanceError):
    """Requested maintenance operation does not exist."""
    pass


class OperationFailedError(MacMaintenanceError):
    """Maintenance operation failed during execution."""

    def __init__(self, message: str, exit_code: int | None = None, output: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.output = output


class DaemonNotAvailableError(MacMaintenanceError):
    """Privileged daemon is not running or not accessible."""
    pass


class OperationTimeoutError(MacMaintenanceError):
    """Operation exceeded timeout limit."""
    pass


# System exceptions
class SystemMetricsError(MacMaintenanceError):
    """Failed to retrieve system metrics."""
    pass


# API-level exceptions
class APIError(MacMaintenanceError):
    """General API error wrapper.

    Used to wrap unexpected exceptions from lower layers.
    """

    def __init__(self, message: str, original_exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = original_exception

    @classmethod
    def from_exception(cls, e: Exception) -> "APIError":
        """Convert any exception to APIError.

        Args:
            e: Original exception

        Returns:
            APIError wrapping the original exception
        """
        return cls(
            message=f"API error: {type(e).__name__}: {str(e)}",
            original_exception=e
        )


class ValidationError(MacMaintenanceError):
    """Input validation failed."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class NotFoundError(MacMaintenanceError):
    """Requested resource not found."""
    pass


class ConflictError(MacMaintenanceError):
    """Resource conflict detected."""
    pass
