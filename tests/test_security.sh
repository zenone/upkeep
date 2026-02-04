#!/usr/bin/env bash
# Security Function Tests
# Tests for security-related functions in upkeep.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Define the functions we're testing (copied from upkeep.sh)
version_compare() {
  local ver1="$1"
  local ver2="$2"
  local sorted
  sorted="$(printf '%s\n%s\n' "$ver1" "$ver2" | sort -V | head -n1)"
  [[ "$sorted" == "$ver2" ]]
}

validate_numeric() {
  local value="$1"
  local name="$2"
  local min="${3:-0}"
  local max="${4:-}"

  if ! [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "Invalid $name: must be a positive integer (got: '$value')" >&2
    return 1
  fi

  if (( value < min )); then
    echo "Invalid $name: must be at least $min (got: $value)" >&2
    return 1
  fi

  if [[ -n "$max" ]] && (( value > max )); then
    echo "Invalid $name: must be at most $max (got: $value)" >&2
    return 1
  fi

  return 0
}

validate_safe_path() {
  local actual="$1"
  local expected="$2"
  local description="$3"

  if [[ ! -d "$actual" ]]; then
    echo "Directory does not exist: $actual" >&2
    return 1
  fi

  local resolved
  resolved="$(cd "$actual" && pwd -P 2>/dev/null)" || {
    echo "Failed to resolve path: $actual" >&2
    return 1
  }

  if [[ "$resolved" != "$expected" ]]; then
    echo "Path resolution mismatch for $description" >&2
    echo "  Expected: $expected" >&2
    echo "  Got:      $resolved" >&2
    return 1
  fi

  return 0
}

start_test_suite "Security Functions"

## version_compare() tests

assert_success "version_compare: 1.9.17 >= 1.9.16" \
  version_compare "1.9.17" "1.9.16"

assert_success "version_compare: 2.0.0 >= 1.9.17" \
  version_compare "2.0.0" "1.9.17"

assert_success "version_compare: 1.9.17 >= 1.9.17 (equal)" \
  version_compare "1.9.17" "1.9.17"

assert_failure "version_compare: 1.9.16 < 1.9.17" \
  version_compare "1.9.16" "1.9.17"

assert_failure "version_compare: 1.0.0 < 2.0.0" \
  version_compare "1.0.0" "2.0.0"

## validate_numeric() tests

# Valid inputs
assert_success "validate_numeric: accepts valid number 50" \
  validate_numeric 50 "test-param" 0 100

assert_success "validate_numeric: accepts min boundary" \
  validate_numeric 0 "test-param" 0 100

assert_success "validate_numeric: accepts max boundary" \
  validate_numeric 100 "test-param" 0 100

# Invalid inputs (these will call die, so we catch the exit)
test_validate_numeric_rejects_non_numeric() {
  local output
  output=$(validate_numeric "abc" "test-param" 0 100 2>&1) && return 1 || return 0
}
assert_success "validate_numeric: rejects non-numeric input" \
  test_validate_numeric_rejects_non_numeric

test_validate_numeric_rejects_below_min() {
  # Note: The regex ^[0-9]+$ actually catches negatives as non-numeric
  # So validate_numeric(-5) will fail on the regex check, not the min check
  local output
  output=$(validate_numeric -5 "test-param" 0 100 2>&1) && return 1 || return 0
}
# This test expects the function to fail (which it does, on regex not min check)
assert_success "validate_numeric: rejects negative numbers (via regex)" \
  test_validate_numeric_rejects_below_min

## validate_safe_path() tests

# Setup test directories
setup_test_env
mkdir -p "$TEST_HOME/Library/Logs"
mkdir -p "$TEST_HOME/Library/Caches"

# Create a symlink attack scenario
ln -s /tmp "$TEST_HOME/Library/BadLink"

test_validate_safe_path_valid() {
  # The function resolves paths with pwd -P, so we need to pass the resolved path
  local resolved
  resolved="$(cd "$TEST_HOME/Library/Logs" && pwd -P)"
  validate_safe_path "$TEST_HOME/Library/Logs" "$resolved" "test logs"
}
assert_success "validate_safe_path: accepts valid path (after resolution)" \
  test_validate_safe_path_valid

test_validate_safe_path_rejects_symlink() {
  local output
  output=$(validate_safe_path "$TEST_HOME/Library/BadLink" "$TEST_HOME/Library/Caches" "test" 2>&1)
  local result=$?
  # Should fail validation
  [[ $result -ne 0 ]]
}
assert_success "validate_safe_path: rejects symlink mismatch" \
  test_validate_safe_path_rejects_symlink

finish_test_suite
