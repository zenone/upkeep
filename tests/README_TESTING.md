# Testing Guide - Mac Maintenance

## Overview

This project uses **pytest** for automated testing. Tests are organized to catch bugs early and ensure code quality.

**Key Benefit:** These tests would have prevented 3+ bugs from the 2026-01-30 session!

---

## Quick Start

### Install Test Dependencies

```bash
# Install development dependencies (includes pytest)
pip install -e ".[dev]"

# Or using uv (faster)
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with detailed coverage report
pytest --cov --cov-report=html
```

---

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_api/                      # API tests
│   ├── test_maintenance_api.py    # Maintenance API tests (CRITICAL)
│   ├── test_storage_api.py        # Storage API tests
│   └── test_schedule_api.py       # Schedule API tests
├── test_core/                     # Core functionality tests
├── test_commands.py               # Command execution tests
├── test_edge_cases.py             # Edge case handling
└── test_integration.py            # Integration tests
```

---

## Running Specific Tests

### By Category

```bash
# Run only API tests
pytest tests/test_api/ -v

# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### By Test Name

```bash
# Run specific test file
pytest tests/test_api/test_maintenance_api.py

# Run specific test class
pytest tests/test_api/test_maintenance_api.py::TestGetOperations

# Run specific test method
pytest tests/test_api/test_maintenance_api.py::TestGetOperations::test_get_operations_merges_why_what_data
```

### By Pattern

```bash
# Run all tests matching pattern
pytest -k "pydantic"

# Run all tests NOT matching pattern
pytest -k "not slow"
```

---

## Test Markers

Tests are marked with categories for easy filtering:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast, isolated tests | `@pytest.mark.unit` |
| `integration` | Tests requiring real files/services | `@pytest.mark.integration` |
| `slow` | Long-running tests | `@pytest.mark.slow` |
| `api` | API endpoint tests | `@pytest.mark.api` |

**Usage:**
```python
@pytest.mark.unit
def test_something_fast():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_something_comprehensive():
    pass
```

---

## Coverage Reports

### Terminal Report

```bash
pytest --cov --cov-report=term-missing
```

Shows coverage percentage and missing lines.

### HTML Report

```bash
pytest --cov --cov-report=html
```

Generates detailed HTML report in `htmlcov/index.html`.

### XML Report (for CI/CD)

```bash
pytest --cov --cov-report=xml
```

Generates `coverage.xml` for integration with CI systems.

---

## Critical Tests

### Tests That Would Have Caught Recent Bugs

**1. test_get_operations_merges_why_what_data** (Pydantic Bug)
```bash
pytest tests/test_api/test_maintenance_api.py::TestGetOperations::test_get_operations_merges_why_what_data -v
```

**What it catches:** Missing Pydantic fields (why/what data lost)

**Bug prevented:** WHY/WHAT accordion not displaying (Task #99)

---

**2. test_maintenance_operation_model_has_why_what_fields** (Model Validation)
```bash
pytest tests/test_api/test_maintenance_api.py::TestPydanticModels::test_maintenance_operation_model_has_why_what_fields -v
```

**What it catches:** Missing fields in Pydantic models

**Bug prevented:** API returning data without expected fields

---

**3. test_load_operation_details_handles_missing_file** (Error Handling)
```bash
pytest tests/test_api/test_maintenance_api.py::TestOperationDetailsLoading::test_load_operation_details_handles_missing_file -v
```

**What it catches:** Crashes when operation_details.json is missing

**Bug prevented:** Graceful degradation failures

---

## Writing New Tests

### Test Structure

```python
"""
Module docstring explaining what this tests
"""

import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """Test class for specific feature"""

    def test_happy_path(self):
        """Test normal, expected behavior"""
        # Arrange
        data = {'key': 'value'}

        # Act
        result = function_under_test(data)

        # Assert
        assert result is not None

    def test_error_handling(self):
        """Test error paths and edge cases"""
        # Test with invalid input
        result = function_under_test(None)

        # Should handle gracefully
        assert result == default_value
```

### Using Fixtures

```python
def test_with_fixture(sample_operation_details):
    """Use shared fixture from conftest.py"""
    assert 'brew-update' in sample_operation_details
```

### Mocking External Dependencies

```python
@patch('module.external_function')
def test_with_mock(mock_function):
    """Mock external dependencies"""
    mock_function.return_value = 'mocked result'

    result = function_that_calls_external()

    assert result == 'mocked result'
    mock_function.assert_called_once()
```

---

## Defensive Testing Principles

Following the project's defensive coding standards:

### 1. Test Happy Path AND Error Paths

```python
def test_happy_path():
    """Test normal operation"""
    pass

def test_with_invalid_input():
    """Test error handling"""
    pass

def test_with_missing_data():
    """Test edge case"""
    pass
```

### 2. Test Business Logic

```python
def test_recommended_operations_are_safe():
    """Verify business rule: Only safe ops are recommended"""
    for op in operations:
        if op['recommended']:
            assert op['safe'], "Recommended op must be safe!"
```

### 3. Test Graceful Degradation

```python
def test_continues_on_error():
    """Verify system continues even if component fails"""
    with mock_error():
        result = system_function()

    # Should return fallback, not crash
    assert result is not None
```

---

## Continuous Integration

### Pre-commit Testing

```bash
# Run fast tests before committing
pytest -m "unit and not slow" --maxfail=1
```

### Pre-push Testing

```bash
# Run all tests before pushing
pytest --cov --cov-report=term-missing
```

### CI Pipeline

```bash
# Full test suite with coverage
pytest --cov --cov-report=xml --cov-report=html
```

---

## Debugging Failed Tests

### Show Detailed Output

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

### Show Warnings

```bash
# Show all warnings
pytest -W all
```

### Verbose Logging

```bash
# Show all log output
pytest --log-cli-level=DEBUG
```

---

## Performance Testing

### Time Tests

```bash
# Show test durations
pytest --durations=10

# Show only slow tests
pytest --durations=0 --durations-min=1.0
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

---

## Common Issues & Solutions

### Issue: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'mac_maintenance'`

**Solution:**
```bash
# Install package in editable mode
pip install -e .
```

---

### Issue: Tests Pass Locally But Fail in CI

**Problem:** Environment differences

**Solution:**
- Check Python version consistency
- Verify all dependencies installed
- Check for hardcoded paths (use tmp_path fixture)
- Ensure tests don't depend on local files

---

### Issue: Flaky Tests

**Problem:** Tests pass/fail inconsistently

**Solution:**
- Avoid time-based assertions (use mocks)
- Ensure tests are independent (no shared state)
- Use fixtures to reset environment
- Mock external dependencies

---

## Best Practices

### DO ✅

- Test one thing per test
- Use descriptive test names
- Test error paths, not just happy paths
- Use fixtures for shared setup
- Mock external dependencies
- Keep tests fast (unit tests < 100ms)
- Document what bug the test prevents

### DON'T ❌

- Don't test implementation details
- Don't share state between tests
- Don't skip tests without good reason
- Don't use time.sleep() (use mocks)
- Don't hardcode paths (use tmp_path)
- Don't ignore warnings

---

## Resources

### Pytest Documentation
- Official docs: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Markers: https://docs.pytest.org/en/stable/how-to/mark.html

### Project Documentation
- Defensive Coding Standards: `.claude/DEFENSIVE_CODING_STANDARDS.md`
- Lessons Learned: `.claude/LESSONS_LEARNED_UPDATE_2026-01-30.md`
- Current State: `.claude/CURRENT_STATE_2026-01-30_FINAL.md`

---

## Summary

**Why We Test:**
> "pytest would have prevented 3+ bugs this session"
> - User feedback, 2026-01-30

**What We Test:**
1. API endpoints (catch Pydantic bugs)
2. Error handling (ensure graceful degradation)
3. Data validation (prevent bad data)
4. Business logic (verify rules are followed)
5. Edge cases (handle unusual scenarios)

**How We Test:**
- Fast unit tests (run on every save)
- Integration tests (run before commit)
- Coverage reports (aim for 80%+)
- Defensive mindset (test failures, not just success)

---

**Created:** 2026-01-30
**Status:** Active - pytest framework implemented
**Next Steps:** Add more tests, aim for 80% coverage
**Goal:** Prevent bugs before they reach production
