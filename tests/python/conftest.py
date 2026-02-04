"""
Pytest configuration and fixtures for upkeep tests.

This module provides shared fixtures and configuration for all Python tests.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    dirpath = tempfile.mkdtemp()
    yield Path(dirpath)
    shutil.rmtree(dirpath)


@pytest.fixture
def sample_directory(temp_dir):
    """Create a sample directory structure for testing."""
    # Create some test files and directories
    (temp_dir / "subdir1").mkdir()
    (temp_dir / "subdir2").mkdir()
    (temp_dir / "subdir1" / "file1.txt").write_text("test content 1")
    (temp_dir / "subdir1" / "file2.txt").write_text("test content 2")
    (temp_dir / "subdir2" / "file3.txt").write_text("test content 3")
    (temp_dir / "root_file.txt").write_text("root content")

    return temp_dir


@pytest.fixture
def mock_system_info():
    """Mock system information for testing."""
    return {
        "platform": "Darwin",
        "version": "26.2.0",
        "build": "25C56",
        "hostname": "test-mac",
    }
