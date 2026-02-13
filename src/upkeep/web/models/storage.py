"""Storage analysis and management models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StorageEntry(BaseModel):
    """A file or directory entry in storage analysis."""

    path: str = Field(..., description="Full path to the file or directory")
    size_gb: float = Field(..., description="Size in gigabytes", ge=0)
    is_dir: bool = Field(..., description="True if directory, False if file")


class StorageAnalyzeRequest(BaseModel):
    """Request to analyze storage at a path."""

    path: str = Field(..., description="Path to analyze", min_length=1)


class StorageAnalyzeResponse(BaseModel):
    """Storage analysis results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "path": "/Users/john/Downloads",
                "total_size_gb": 25.3,
                "file_count": 279,
                "dir_count": 137,
                "largest_entries": [
                    {"path": "/Users/john/Downloads/BigFile.dmg", "size_gb": 5.2, "is_dir": False},
                    {"path": "/Users/john/Downloads/OldProject", "size_gb": 3.8, "is_dir": True},
                ],
            }
        }
    )

    success: bool = Field(True, description="Analysis succeeded")
    path: str = Field(..., description="Analyzed path")
    total_size_gb: float = Field(..., description="Total size in GB", ge=0)
    file_count: int = Field(..., description="Number of files", ge=0)
    dir_count: int = Field(..., description="Number of directories", ge=0)
    largest_entries: list[StorageEntry] = Field(
        ..., description="Largest files/directories (up to 50)", max_length=50
    )
    error: str | None = Field(None, description="Error message if analysis failed")


class DeleteRequest(BaseModel):
    """Request to delete a file or directory."""

    path: str = Field(..., description="Path to delete", min_length=1)
    mode: str = Field(
        ..., description="Delete mode: 'trash' or 'permanent'", pattern="^(trash|permanent)$"
    )


class DeleteResponse(BaseModel):
    """Result of delete operation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "path": "/Users/john/Downloads/file.txt", "error": None}
        }
    )

    success: bool = Field(..., description="Delete succeeded")
    path: str = Field(..., description="Deleted path")
    error: str | None = Field(None, description="Error message if delete failed")
