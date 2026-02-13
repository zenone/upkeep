"""Common models used across all API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = Field(True, description="Operation succeeded")
    message: str | None = Field(None, description="Optional success message")


class ErrorResponse(BaseModel):
    """Standard error response following RFC 7807 Problem Details."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "File not found",
                "detail": "The file /Users/test/file.txt does not exist",
                "code": "FILE_NOT_FOUND",
            }
        }
    )

    success: bool = Field(False, description="Operation failed")
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")
    code: str | None = Field(None, description="Error code for programmatic handling")
