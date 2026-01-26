#!/usr/bin/env bash
# Input Validation Tests
# Tests for parameter validation and input sanitization

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Define the function we're testing (copied from maintain.sh)
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

start_test_suite "Input Validation"

## Test valid numeric ranges

assert_success "validate_numeric: space threshold 50 (min boundary)" \
  validate_numeric 50 "space-threshold" 50 99

assert_success "validate_numeric: space threshold 75 (mid-range)" \
  validate_numeric 75 "space-threshold" 50 99

assert_success "validate_numeric: space threshold 99 (max boundary)" \
  validate_numeric 99 "space-threshold" 50 99

assert_success "validate_numeric: trim days 1 (min boundary)" \
  validate_numeric 1 "trim-days" 1 3650

assert_success "validate_numeric: trim days 30 (common value)" \
  validate_numeric 30 "trim-days" 1 3650

assert_success "validate_numeric: trim days 3650 (max boundary)" \
  validate_numeric 3650 "trim-days" 1 3650

## Test invalid inputs that should be rejected

test_rejects_below_min() {
  validate_numeric 49 "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects below minimum (49 < 50)" \
  test_rejects_below_min

test_rejects_above_max() {
  validate_numeric 100 "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects above maximum (100 > 99)" \
  test_rejects_above_max

test_rejects_negative() {
  validate_numeric -10 "trim-days" 1 3650 2>&1 && return 1 || return 0
}
# Note: regex ^[0-9]+$ DOES catch negatives (dash is not a digit)
# The test name was misleading - it actually works correctly
assert_success "validate_numeric: rejects negative (-10)" \
  test_rejects_negative

test_rejects_float() {
  validate_numeric 75.5 "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects float (75.5)" \
  test_rejects_float

test_rejects_string() {
  validate_numeric "high" "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects string ('high')" \
  test_rejects_string

test_rejects_empty() {
  validate_numeric "" "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects empty string" \
  test_rejects_empty

test_rejects_special_chars() {
  validate_numeric "50; rm -rf /" "space-threshold" 50 99 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects injection attempt" \
  test_rejects_special_chars

## Test tm-thin-bytes validation (large numbers)

assert_success "validate_numeric: tm-thin-bytes 1GB (min)" \
  validate_numeric 1000000000 "tm-thin-bytes" 1000000000 100000000000

assert_success "validate_numeric: tm-thin-bytes 20GB (default)" \
  validate_numeric 20000000000 "tm-thin-bytes" 1000000000 100000000000

assert_success "validate_numeric: tm-thin-bytes 100GB (max)" \
  validate_numeric 100000000000 "tm-thin-bytes" 1000000000 100000000000

test_rejects_tm_thin_too_small() {
  validate_numeric 999999999 "tm-thin-bytes" 1000000000 100000000000 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects tm-thin-bytes < 1GB" \
  test_rejects_tm_thin_too_small

test_rejects_tm_thin_too_large() {
  validate_numeric 100000000001 "tm-thin-bytes" 1000000000 100000000000 2>&1 && return 1 || return 0
}
assert_success "validate_numeric: rejects tm-thin-bytes > 100GB" \
  test_rejects_tm_thin_too_large

finish_test_suite
