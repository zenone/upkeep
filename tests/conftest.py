"""
Pytest configuration and shared fixtures

This file is automatically loaded by pytest and provides:
- Shared fixtures for all tests
- Test configuration
- Custom markers
"""

import pytest
import json
import logging
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(name)s - %(message)s'
)


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: Integration tests (require real files/services)"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests (isolated, fast)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "api: API tests"
    )


# Shared fixtures
@pytest.fixture
def sample_operation_details() -> Dict[str, Any]:
    """Sample operation_details.json data for testing"""
    return {
        'brew-update': {
            'why': {
                'context': 'Homebrew manages third-party software packages',
                'problems': [
                    {
                        'symptom': 'Outdated packages with security vulnerabilities',
                        'description': 'Old versions may have known security flaws'
                    }
                ]
            },
            'what': {
                'outcomes': [
                    {
                        'type': 'positive',
                        'description': 'All packages updated to latest versions'
                    }
                ],
                'timeline': '2-5 minutes depending on package count'
            },
            'when_to_run': ['Weekly', 'Before installing new software'],
            'safety': 'low-risk'
        },
        'disk-verify': {
            'why': {
                'context': 'File system health check',
                'problems': [
                    {
                        'symptom': 'Disk corruption',
                        'description': 'Bad sectors or filesystem errors'
                    }
                ]
            },
            'what': {
                'outcomes': [
                    {
                        'type': 'info',
                        'description': 'Disk health report generated'
                    }
                ],
                'timeline': '1-2 minutes'
            },
            'when_to_run': ['Monthly', 'When experiencing file access issues'],
            'safety': 'low-risk'
        }
    }


@pytest.fixture
def mock_operation_details_file(tmp_path, sample_operation_details):
    """Create a temporary operation_details.json file for testing"""
    details_file = tmp_path / "operation_details.json"
    details_file.write_text(json.dumps(sample_operation_details, indent=2))
    return details_file


@pytest.fixture
def empty_operation_details_file(tmp_path):
    """Create an empty operation_details.json file for testing"""
    details_file = tmp_path / "operation_details.json"
    details_file.write_text("")
    return details_file


@pytest.fixture
def invalid_json_file(tmp_path):
    """Create an invalid JSON file for testing error handling"""
    details_file = tmp_path / "operation_details.json"
    details_file.write_text("{ invalid json")
    return details_file


@pytest.fixture
def sample_maintenance_operation():
    """Sample maintenance operation data"""
    return {
        'id': 'test-op',
        'name': 'Test Operation',
        'description': 'A test operation for unit testing',
        'category': 'Test Category',
        'recommended': False,
        'requires_sudo': True,
        'safe': True,
        'why': {
            'context': 'Test context',
            'problems': [
                {
                    'symptom': 'Test symptom',
                    'description': 'Test description'
                }
            ]
        },
        'what': {
            'outcomes': [
                {
                    'type': 'positive',
                    'description': 'Test outcome'
                }
            ],
            'timeline': '1 minute'
        },
        'when_to_run': ['Test schedule'],
        'safety': 'low-risk'
    }


@pytest.fixture
def mock_logging():
    """Mock logging to capture log output in tests"""
    with patch('logging.getLogger') as mock_logger:
        mock_logger.return_value = Mock()
        yield mock_logger


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    import os

    # Save original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_daemon_queue(tmp_path):
    """Mock daemon job queue directory"""
    queue_dir = tmp_path / "daemon_queue"
    queue_dir.mkdir()
    return queue_dir


# Helper functions for tests
def create_test_job(job_id: str, operation_id: str, tmp_path: Path) -> Path:
    """Helper: Create a test job file"""
    job_file = tmp_path / f"{job_id}.json"
    job_data = {
        'job_id': job_id,
        'operation_id': operation_id,
        'status': 'pending',
        'created_at': '2026-01-30T00:00:00Z'
    }
    job_file.write_text(json.dumps(job_data, indent=2))
    return job_file


def create_test_result(job_id: str, success: bool, tmp_path: Path) -> Path:
    """Helper: Create a test result file"""
    result_file = tmp_path / f"{job_id}.result.json"
    result_data = {
        'job_id': job_id,
        'status': 'success' if success else 'error',
        'exit_code': 0 if success else 1,
        'stdout': 'Test output',
        'stderr': '' if success else 'Test error'
    }
    result_file.write_text(json.dumps(result_data, indent=2))
    return result_file


# Pytest hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add 'unit' marker to all tests by default
        if 'integration' not in item.keywords:
            item.add_marker(pytest.mark.unit)

        # Add 'api' marker to API tests
        if 'test_api' in str(item.fspath):
            item.add_marker(pytest.mark.api)


# Test utilities
class TestUtils:
    """Utility functions for tests"""

    @staticmethod
    def assert_valid_operation(operation: Dict[str, Any]):
        """Assert that operation has all required fields"""
        required_fields = ['id', 'name', 'description', 'category']
        for field in required_fields:
            assert field in operation, f"Missing required field: {field}"

    @staticmethod
    def assert_valid_why_what(operation: Dict[str, Any]):
        """Assert that operation has valid WHY/WHAT structure"""
        if 'why' in operation and operation['why']:
            assert isinstance(operation['why'], dict)
            if 'problems' in operation['why']:
                assert isinstance(operation['why']['problems'], list)

        if 'what' in operation and operation['what']:
            assert isinstance(operation['what'], dict)
            if 'outcomes' in operation['what']:
                assert isinstance(operation['what']['outcomes'], list)


# Export utilities
__all__ = [
    'sample_operation_details',
    'mock_operation_details_file',
    'empty_operation_details_file',
    'invalid_json_file',
    'sample_maintenance_operation',
    'mock_logging',
    'reset_environment',
    'mock_daemon_queue',
    'create_test_job',
    'create_test_result',
    'TestUtils',
]
