#!/bin/bash
# Fully automated test runner for CI/CD
# NO MANUAL INPUT REQUIRED
#
# Usage: ./tests/run_all_tests_automated.sh
# Exit codes: 0 = all passed, 1 = failures

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Upkeep - Automated Test Suite (CI Mode)              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Change to repo root
cd "$(dirname "$0")/.."

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${BLUE}▶ ${test_name}${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command" > /tmp/upkeep_test_output.txt 2>&1; then
        echo -e "${GREEN}  ✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}  ✗ FAIL${NC}"
        cat /tmp/upkeep_test_output.txt | head -20
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "Virtual environment exists" "[ -d .venv ]"
run_test "Python package source exists" "[ -d src/upkeep ]"
run_test "upkeep.sh exists and is executable" "[ -x ./upkeep.sh ]"
run_test "Node modules installed" "[ -d node_modules ]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: Python Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d .venv ]; then
    source .venv/bin/activate 2>/dev/null || true
fi

run_test "pytest - Python unit tests" "pytest tests/python -v --tb=short -q"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: TypeScript Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "TypeScript type check" "npm run type-check"
run_test "Vitest - TypeScript tests" "npm run test:run"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4: Bash Script Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run individual bash test files
for test_file in tests/test_*.sh; do
    if [ -f "$test_file" ] && [ -x "$test_file" ]; then
        test_name=$(basename "$test_file" .sh)
        run_test "Bash: $test_name" "./$test_file" || true
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 5: Documentation Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test "README.md exists" "[ -f README.md ]"
run_test "CHANGELOG.md exists" "[ -f CHANGELOG.md ]"
run_test "docs/SECURITY.md exists" "[ -f docs/SECURITY.md ]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ✓ ALL TESTS PASSED                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                   ✗ SOME TESTS FAILED                        ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo "Tests Run:    $TESTS_RUN"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
else
    echo "Failed:       $TESTS_FAILED"
fi

if [ $TESTS_RUN -gt 0 ]; then
    PASS_RATE=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo "Pass Rate:    ${PASS_RATE}%"
fi

# Cleanup
rm -f /tmp/upkeep_test_output.txt

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
