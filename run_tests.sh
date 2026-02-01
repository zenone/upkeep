#!/usr/bin/env bash
# Run pytest tests with common configurations
# Usage: ./run_tests.sh [option]
#
# Options:
#   all      - Run all tests with coverage (default)
#   fast     - Run only fast unit tests
#   api      - Run only API tests
#   verbose  - Run with verbose output
#   coverage - Run with HTML coverage report
#   watch    - Run tests on file changes (requires pytest-watch)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    warning "pytest not found. Installing development dependencies..."
    pip install -e ".[dev]"
fi

# Parse command line argument
COMMAND="${1:-all}"

case "$COMMAND" in
    all)
        info "Running all tests with coverage..."
        pytest --cov --cov-report=term-missing --cov-report=html -v
        success "Tests complete! Coverage report: htmlcov/index.html"
        ;;

    fast)
        info "Running fast unit tests only..."
        pytest -m "unit and not slow" -v
        success "Fast tests complete!"
        ;;

    api)
        info "Running API tests..."
        pytest tests/test_api/ -v
        success "API tests complete!"
        ;;

    verbose)
        info "Running all tests with verbose output..."
        pytest -vv -s
        ;;

    coverage)
        info "Running tests with HTML coverage report..."
        pytest --cov --cov-report=html
        success "Coverage report generated: htmlcov/index.html"

        # Try to open coverage report
        if command -v open &> /dev/null; then
            info "Opening coverage report..."
            open htmlcov/index.html
        fi
        ;;

    watch)
        if ! command -v ptw &> /dev/null; then
            warning "pytest-watch not found. Installing..."
            pip install pytest-watch
        fi
        info "Watching for changes... (Ctrl+C to stop)"
        ptw -- -v
        ;;

    critical)
        info "Running critical tests that prevent bugs..."
        info "These tests would have caught the Pydantic bug!"
        pytest tests/test_api/test_maintenance_api.py::TestGetOperations::test_get_operations_merges_why_what_data -v
        pytest tests/test_api/test_maintenance_api.py::TestPydanticModels::test_maintenance_operation_model_has_why_what_fields -v
        pytest tests/test_api/test_maintenance_api.py::TestOperationDetailsLoading -v
        success "Critical tests complete!"
        ;;

    quick)
        info "Running quick smoke test..."
        pytest tests/test_api/test_maintenance_api.py::TestMaintenanceAPIBasics -v
        success "Smoke test complete!"
        ;;

    *)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  all       - Run all tests with coverage (default)"
        echo "  fast      - Run only fast unit tests"
        echo "  api       - Run only API tests"
        echo "  verbose   - Run with verbose output"
        echo "  coverage  - Run with HTML coverage report"
        echo "  watch     - Run tests on file changes"
        echo "  critical  - Run critical bug-prevention tests"
        echo "  quick     - Quick smoke test"
        echo ""
        echo "Examples:"
        echo "  $0              # Run all tests"
        echo "  $0 fast         # Quick test before commit"
        echo "  $0 coverage     # Generate coverage report"
        exit 1
        ;;
esac
