"""
Common models used across all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = Field(True, description="Operation succeeded")
    message: Optional[str] = Field(None, description="Optional success message")


class ErrorResponse(BaseModel):
    """Standard error response following RFC 7807 Problem Details."""

    success: bool = Field(False, description="Operation failed")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "File not found",
                "detail": "The file /Users/test/file.txt does not exist",
                "code": "FILE_NOT_FOUND"
            }
        }
