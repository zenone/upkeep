"""System information models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CPUInfo(BaseModel):
    """CPU information."""

    percent: float = Field(..., description="CPU usage percentage", ge=0, le=100)
    count: int = Field(..., description="Number of CPU cores", gt=0)
    history: list[float] = Field(default_factory=list, description="Recent CPU usage history")


class MemoryInfo(BaseModel):
    """Memory information."""

    total_gb: float = Field(..., description="Total memory in GB", gt=0)
    used_gb: float = Field(..., description="Used memory in GB", ge=0)
    available_gb: float = Field(..., description="Available memory in GB", ge=0)
    percent: float = Field(..., description="Memory usage percentage", ge=0, le=100)
    history: list[float] = Field(default_factory=list, description="Recent memory usage history")


class DiskInfo(BaseModel):
    """Disk information."""

    total_gb: float = Field(..., description="Total disk space in GB", gt=0)
    used_gb: float = Field(..., description="Used disk space in GB", ge=0)
    free_gb: float = Field(..., description="Free disk space in GB", ge=0)
    percent: float = Field(..., description="Disk usage percentage", ge=0, le=100)
    history: list[float] = Field(default_factory=list, description="Recent disk usage history")


class SystemInfo(BaseModel):
    """System information."""

    username: str = Field(..., description="Current system username")
    hostname: str = Field(..., description="System hostname")
    version: str = Field(..., description="macOS version")
    architecture: str = Field(..., description="System architecture (e.g., arm64, x86_64)")


class SystemInfoResponse(BaseModel):
    """Complete system information response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpu": {"percent": 15.3, "count": 8, "history": [12.1, 14.5, 15.3]},
                "memory": {
                    "total_gb": 16.0,
                    "used_gb": 8.5,
                    "available_gb": 7.5,
                    "percent": 53.1,
                    "history": [50.2, 52.0, 53.1],
                },
                "disk": {
                    "total_gb": 500.0,
                    "used_gb": 350.0,
                    "free_gb": 150.0,
                    "percent": 70.0,
                    "history": [69.5, 69.8, 70.0],
                },
                "system": {
                    "username": "john",
                    "hostname": "johns-macbook",
                    "version": "14.2",
                    "architecture": "arm64",
                },
            }
        }
    )

    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    system: SystemInfo


class SystemHealthResponse(BaseModel):
    """System health assessment."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall": "warning",
                "score": 65,
                "issues": ["High disk usage (85%)", "Memory usage above 80%"],
            }
        }
    )

    overall: str = Field(
        ..., description="Overall health status", pattern="^(good|warning|critical)$"
    )
    score: int = Field(..., description="Health score 0-100", ge=0, le=100)
    issues: list[str] = Field(default_factory=list, description="List of health issues")


class SparklineResponse(BaseModel):
    """Sparkline data for dashboard charts."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpu": [10.5, 15.2, 12.8, 18.3, 14.1],
                "memory": [55.0, 56.2, 54.8, 57.1, 55.9],
                "disk": [70.0, 70.1, 70.1, 70.2, 70.2],
            }
        }
    )

    cpu: list[float] = Field(..., description="CPU usage history")
    memory: list[float] = Field(..., description="Memory usage history")
    disk: list[float] = Field(..., description="Disk usage history")


class ProcessInfo(BaseModel):
    """Information about a running process."""

    name: str = Field(..., description="Process name")
    cpu_percent: float = Field(..., description="CPU usage percentage", ge=0)
    memory_mb: float = Field(..., description="Memory usage in MB", ge=0)


class ProcessesResponse(BaseModel):
    """Top resource-consuming processes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "top_cpu": [
                    {"name": "Chrome", "cpu_percent": 25.3, "memory_mb": 1024.5},
                    {"name": "Python", "cpu_percent": 15.2, "memory_mb": 512.0},
                ],
                "top_memory": [
                    {"name": "Chrome", "cpu_percent": 25.3, "memory_mb": 2048.0},
                    {"name": "Docker", "cpu_percent": 5.0, "memory_mb": 1536.5},
                ],
            }
        }
    )

    top_cpu: list[ProcessInfo] = Field(..., description="Top CPU consumers")
    top_memory: list[ProcessInfo] = Field(..., description="Top memory consumers")
