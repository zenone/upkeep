#!/usr/bin/env bash
# Test Runner - Executes all test suites
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  BLUE='\033[1;34m'
  YELLOW='\033[1;33m'
  NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; BLUE=''; NC=''
fi

# Test suites to run
TEST_SUITES=(
  "test_security.sh"
  "test_validation.sh"
  "test_integration.sh"
  "test_edge_cases.sh"
  "test_ux.sh"
)

# Overall results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        macOS Maintenance Toolkit - Test Suite           ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Make all test scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Run each test suite
for suite in "${TEST_SUITES[@]}"; do
  ((TOTAL_SUITES++))

  echo -e "${YELLOW}Running: $suite${NC}"

  if bash "$SCRIPT_DIR/$suite"; then
    ((PASSED_SUITES++))
  else
    ((FAILED_SUITES++))
    echo -e "${RED}Suite failed: $suite${NC}\n"
  fi
done

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     TEST SUMMARY                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Total suites:  $TOTAL_SUITES"
echo -e "  ${GREEN}Passed:        $PASSED_SUITES${NC}"

if (( FAILED_SUITES > 0 )); then
  echo -e "  ${RED}Failed:        $FAILED_SUITES${NC}"
  echo ""
  echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║                   ✗ TESTS FAILED                        ║${NC}"
  echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
  exit 1
else
  echo ""
  echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║                 ✓ ALL TESTS PASSED                      ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
  exit 0
fi
