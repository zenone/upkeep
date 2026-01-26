#!/usr/bin/env bash
# Test Helpers - Common utilities for test scripts
set -euo pipefail

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors for output
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; BLUE=''; NC=''
fi

# Test assertion functions
assert_equals() {
  local expected="$1"
  local actual="$2"
  local description="$3"

  ((TESTS_RUN++))

  if [[ "$expected" == "$actual" ]]; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓${NC} $description"
    return 0
  else
    ((TESTS_FAILED++))
    echo -e "${RED}✗${NC} $description"
    echo -e "  Expected: ${YELLOW}$expected${NC}"
    echo -e "  Got:      ${RED}$actual${NC}"
    return 1
  fi
}

assert_success() {
  local description="$1"
  shift

  ((TESTS_RUN++))

  if "$@" >/dev/null 2>&1; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓${NC} $description"
    return 0
  else
    ((TESTS_FAILED++))
    echo -e "${RED}✗${NC} $description"
    echo -e "  Command failed: ${YELLOW}$*${NC}"
    return 1
  fi
}

assert_failure() {
  local description="$1"
  shift

  ((TESTS_RUN++))

  if ! "$@" >/dev/null 2>&1; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓${NC} $description"
    return 0
  else
    ((TESTS_FAILED++))
    echo -e "${RED}✗${NC} $description"
    echo -e "  Command should have failed: ${YELLOW}$*${NC}"
    return 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local description="$3"

  ((TESTS_RUN++))

  if [[ "$haystack" == *"$needle"* ]]; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓${NC} $description"
    return 0
  else
    ((TESTS_FAILED++))
    echo -e "${RED}✗${NC} $description"
    echo -e "  Expected to find: ${YELLOW}$needle${NC}"
    echo -e "  In: ${RED}$haystack${NC}"
    return 1
  fi
}

# Test suite management
start_test_suite() {
  local suite_name="$1"
  echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
  echo -e "${BLUE}  $suite_name${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════${NC}\n"
}

finish_test_suite() {
  echo -e "\n${BLUE}───────────────────────────────────────────${NC}"
  echo -e "Tests run: $TESTS_RUN"
  echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
  if (( TESTS_FAILED > 0 )); then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${BLUE}───────────────────────────────────────────${NC}\n"
    return 1
  else
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${BLUE}───────────────────────────────────────────${NC}\n"
    return 0
  fi
}

# Setup/teardown helpers
setup_test_env() {
  # Create temporary test directory
  export TEST_DIR
  TEST_DIR="$(mktemp -d)"
  export TEST_HOME="$TEST_DIR/home"
  mkdir -p "$TEST_HOME"
}

teardown_test_env() {
  # Cleanup temporary test directory
  if [[ -n "${TEST_DIR:-}" && -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
  fi
}

# Trap cleanup on exit
trap teardown_test_env EXIT INT TERM
