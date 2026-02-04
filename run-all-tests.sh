#!/bin/bash
# Comprehensive test runner for Mac Maintenance
# Tests Tasks #46, #47, and general system health

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Mac Maintenance - Comprehensive Test Suite          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${BLUE}▶ Running: ${test_name}${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}  ✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Prerequisites Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check virtual environment
run_test "Virtual environment exists" "[ -d .venv ]"

# Check Python package source exists
run_test "Python package source exists" "[ -d src/upkeep ]"

# Check scripts exist
run_test "run-web.sh exists" "[ -f ./run-web.sh ]"
run_test "upkeep.sh exists" "[ -f ./upkeep.sh ]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: Server Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if server is running
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running on localhost:8080${NC}"
    SERVER_RUNNING=true
else
    echo -e "${YELLOW}⚠ Server not running on localhost:8080${NC}"
    echo -e "${YELLOW}  Some tests will be skipped${NC}"
    echo -e "${YELLOW}  Start server with: ./run-web.sh${NC}"
    SERVER_RUNNING=false
fi

echo ""

if [ "$SERVER_RUNNING" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Phase 3: Task #46 - API WHY/WHAT Data Test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [ -f ./test-api-whywhat.sh ]; then
        ./test-api-whywhat.sh
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ Task #46: VERIFIED - API returns WHY/WHAT correctly${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo ""
            echo -e "${RED}❌ Task #46: FAILED - API issue detected${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TESTS_RUN=$((TESTS_RUN + 1))
    else
        echo -e "${YELLOW}⚠ test-api-whywhat.sh not found, skipping${NC}"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Phase 4: Task #47 - Frontend Accordion Test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    echo -e "${BLUE}This test requires manual browser verification:${NC}"
    echo ""
    echo "1. Open http://localhost:8080 in browser"
    echo "2. Click 'Maintenance' tab"
    echo "3. Click ℹ️ icon next to any operation"
    echo "4. Verify WHY/WHAT accordion displays"
    echo ""
    echo "See detailed instructions: test-frontend-accordion.md"
    echo ""

    read -p "Did frontend accordion test PASS? (y/n): " -n 1 -r
    echo ""
    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Task #47: VERIFIED - Frontend accordion works${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ Task #47: FAILED - Frontend accordion issue${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Phase 3-4: SKIPPED (server not running)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}To run Tasks #46 and #47:${NC}"
    echo "  1. Start server: ./run-web.sh"
    echo "  2. Run this script again: ./run-all-tests.sh"
    echo ""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 5: Wizard Preset Test (Task #53)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$SERVER_RUNNING" = true ]; then
    echo -e "${BLUE}This test requires manual browser verification:${NC}"
    echo ""
    echo "1. Refresh browser (Cmd+R)"
    echo "2. Click 'Start Guide →' button on Maintenance tab"
    echo "3. Verify counts match:"
    echo "   - Quick Clean: 2 operations"
    echo "   - Weekly Routine: 7 operations"
    echo "   - Full Checkup: 10 operations"
    echo "4. Click each option and verify correct operations selected"
    echo ""

    read -p "Did wizard preset test PASS? (y/n): " -n 1 -r
    echo ""
    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Task #53: VERIFIED - Wizard presets correct${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ Task #53: FAILED - Wizard preset issue${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ Server not running, skipping wizard test${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 6: Documentation Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "README.md exists" "[ -f README.md ]"
run_test "Documentation directory exists" "[ -d .claude ]"
run_test "CURRENT_STATUS.md exists" "[ -f .claude/CURRENT_STATUS.md ]"
run_test "WIZARD_PRESET_FIX.md exists" "[ -f .claude/WIZARD_PRESET_FIX.md ]"
run_test "REBRAND_IMPLEMENTATION_PLAN.md exists" "[ -f .claude/REBRAND_IMPLEMENTATION_PLAN.md ]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Final Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                       ✓ ALL TESTS PASSED                     ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                      ✗ SOME TESTS FAILED                     ║${NC}"
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

# Calculate percentage
if [ $TESTS_RUN -gt 0 ]; then
    PASS_RATE=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo "Pass Rate:    ${PASS_RATE}%"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Task Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$SERVER_RUNNING" = true ]; then
    echo "Task #46 (API WHY/WHAT): See Phase 3 results above"
    echo "Task #47 (Frontend Accordion): See Phase 4 results above"
    echo "Task #53 (Wizard Presets): See Phase 5 results above"
else
    echo -e "${YELLOW}Tasks #46, #47, #53: Require server to test${NC}"
    echo "  Start server: ./run-web.sh"
    echo "  Then run: ./run-all-tests.sh"
fi

echo ""
echo "Next Steps:"
echo "  1. Review test results above"
echo "  2. If all pass: All open tasks complete! 🎉"
echo "  3. If failures: Review error messages"
echo "  4. Check documentation: .claude/CURRENT_STATUS.md"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
