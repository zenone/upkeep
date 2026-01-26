# Python Development Guide

## Overview

The mac-maintenance toolkit includes Python components for advanced features:
- Storage analysis and visualization
- Terminal User Interface (TUI)
- Duplicate file detection
- Advanced reporting

The bash script (`maintain.sh`) remains the primary interface. Python extends functionality for complex analysis and interactive features.

---

## Setup

### Requirements

- **Python 3.10+** (tested with 3.10-3.14)
- **macOS** (Tahoe/26.0+ recommended)
- **uv** package manager (automatically installed)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone git@github.com:zenone/mac-maintenance.git
   cd mac-maintenance
   ```

2. **Create virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```

---

## Development Tools

### uv (Package Manager)

**Why uv?**
- 10-100x faster than pip
- Rust-based, modern architecture
- Better dependency resolution
- Excellent caching
- Industry standard (2024+)

**Common commands:**
```bash
# Create virtual environment
uv venv

# Install project
uv pip install -e ".[dev]"

# Add dependency
uv pip install <package>

# Update dependencies
uv pip install --upgrade -e ".[dev]"

# Check outdated packages
uv pip list --outdated
```

### Testing with pytest

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=mac_maintenance --cov-report=html
open htmlcov/index.html
```

**Run specific test file:**
```bash
pytest tests/python/storage/test_analyzer.py
```

**Run tests matching pattern:**
```bash
pytest -k "test_storage"
```

### Code Quality

**Type checking with mypy:**
```bash
mypy src/mac_maintenance
```

**Linting with ruff:**
```bash
ruff check src tests
```

**Auto-fix with ruff:**
```bash
ruff check --fix src tests
```

**Formatting with black:**
```bash
black src tests
```

**All quality checks:**
```bash
# Run everything
black src tests && ruff check src tests && mypy src && pytest
```

---

## Project Structure

```
mac-maintenance/
├── maintain.sh                  # Bash script (primary interface)
├── src/
│   └── mac_maintenance/
│       ├── __init__.py
│       ├── core/                # Core utilities
│       │   ├── __init__.py
│       │   ├── system.py        # System info
│       │   └── config.py        # Configuration
│       ├── storage/             # Storage analysis
│       │   ├── __init__.py
│       │   ├── analyzer.py      # Disk usage analysis
│       │   └── cli.py           # Storage CLI
│       ├── tui/                 # Terminal UI
│       │   ├── __init__.py
│       │   ├── app.py           # TUI application
│       │   └── widgets.py       # UI components
│       └── cli/                 # CLI interface
│           ├── __init__.py
│           └── main.py          # Main entry point
├── tests/
│   ├── bash/                    # Bash tests (existing)
│   │   ├── test_security.sh
│   │   ├── test_validation.sh
│   │   └── ...
│   └── python/                  # Python tests (new)
│       ├── conftest.py
│       ├── core/
│       ├── storage/
│       ├── tui/
│       └── cli/
└── pyproject.toml              # Python project config
```

---

## CLI Entry Points

### mac-maintenance
Main CLI interface (integrates with bash script):
```bash
mac-maintenance --help
mac-maintenance status
```

### mac-maintenance-analyze
Storage analysis tool:
```bash
mac-maintenance-analyze /path/to/analyze
mac-maintenance-analyze --format=json ~/
```

### mac-maintenance-tui
Launch TUI interface:
```bash
mac-maintenance-tui
```

---

## Writing Tests

### Test Structure

Place tests in `tests/python/` mirroring the source structure:
```
src/mac_maintenance/storage/analyzer.py
→ tests/python/storage/test_analyzer.py
```

### Example Test

```python
import pytest
from mac_maintenance.storage.analyzer import DiskAnalyzer


def test_analyzer_basic(temp_dir):
    """Test basic disk analysis."""
    analyzer = DiskAnalyzer(temp_dir)
    result = analyzer.analyze()

    assert result.total_size > 0
    assert len(result.entries) > 0


def test_analyzer_filters(sample_directory):
    """Test directory filtering."""
    analyzer = DiskAnalyzer(
        sample_directory,
        exclude_patterns=["*.txt"]
    )
    result = analyzer.analyze()

    # Should exclude .txt files
    for entry in result.entries:
        assert not entry.path.endswith('.txt')
```

### Fixtures

Use pytest fixtures from `conftest.py`:
- `temp_dir`: Temporary directory for tests
- `sample_directory`: Pre-populated test directory
- `mock_system_info`: Mock system information

---

## Integration with Bash Script

The Python components integrate seamlessly with the bash script:

### Bash Detection
```bash
# In maintain.sh
if command -v mac-maintenance >/dev/null 2>&1; then
  # Python available, use advanced features
  mac-maintenance analyze /
else
  # Fallback to bash-only features
  echo "Python components not available"
fi
```

### Calling Python from Bash
```bash
# Storage analysis
python -m mac_maintenance.storage.cli ~/Library/Caches

# TUI launch
python -m mac_maintenance.tui.app
```

---

## Continuous Integration

### Pre-commit Checks

Before committing:
```bash
# Format code
black src tests

# Fix linting issues
ruff check --fix src tests

# Type check
mypy src

# Run tests
pytest

# Run bash tests
./tests/run_all_tests.sh
```

### GitHub Actions (Future)

Will include:
- Python tests (pytest)
- Bash tests (existing suite)
- Type checking (mypy)
- Linting (ruff)
- Code coverage reports

---

## Troubleshooting

### Virtual Environment Issues

**Problem:** Module not found after install
```bash
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Import Errors

**Problem:** Cannot import mac_maintenance
```bash
# Solution: Install in editable mode
uv pip install -e .
```

### Test Discovery Issues

**Problem:** pytest not finding tests
```bash
# Solution: Run from project root
cd /Users/szenone/Documents/CODE/BASH/mac-maintenance
pytest
```

---

## Performance Tips

### uv Caching

uv caches packages for fast reinstalls:
```bash
# Cache location
ls ~/.cache/uv

# Clear cache if needed
rm -rf ~/.cache/uv
```

### Fast Test Runs

```bash
# Run only failed tests from last run
pytest --lf

# Run tests in parallel (with pytest-xdist)
pytest -n auto
```

---

## Contributing

### Code Style

- **Python:** Follow PEP 8, use black formatting
- **Type hints:** Required for all functions
- **Docstrings:** Google style for all public APIs
- **Tests:** Required for all new features

### Pull Request Checklist

- [ ] All tests pass (bash + Python)
- [ ] Code formatted with black
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG entry added

---

## Resources

- **uv documentation:** https://github.com/astral-sh/uv
- **Textual framework:** https://textual.textualize.io/
- **pytest guide:** https://docs.pytest.org/
- **mypy handbook:** https://mypy.readthedocs.io/

---

**Status:** Phase 3 - Python Infrastructure Setup
**Version:** 3.0.0-alpha
