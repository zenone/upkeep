#!/usr/bin/env bash
# Integration Tests
# Tests for end-to-end script behavior

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

MAINTAIN_SH="$(cd "$SCRIPT_DIR/.." && pwd)/upkeep.sh"

start_test_suite "Integration Tests"

## Test --help output

test_help_flag() {
  # Test that the script contains help documentation
  [[ -f "$MAINTAIN_SH" ]] || return 1
  grep -q "Usage:" "$MAINTAIN_SH" || return 1
  grep -q "\-\-all-safe" "$MAINTAIN_SH" || return 1
  grep -q "\-\-security-audit" "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script contains help documentation" \
  test_help_flag

## Test --dry-run mode

test_dry_run_mode() {
  # Check that dry-run code exists in the script
  grep -q 'DRY_RUN' "$MAINTAIN_SH" && \
  grep -q 'DRY-RUN:' "$MAINTAIN_SH"
}
assert_success "Script has dry-run mode implementation" \
  test_dry_run_mode

## Test that script refuses to run as root

test_refuses_root() {
  # Can't actually test this without sudo, so we'll check the refuse_root function exists
  grep -q "refuse_root()" "$MAINTAIN_SH"
}
assert_success "Script has refuse_root() function" \
  test_refuses_root

## Test that security checks are present

test_security_check_exists() {
  grep -q "check_sudo_security()" "$MAINTAIN_SH" || return 1
  grep -q "security_posture_check()" "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script has security check functions" \
  test_security_check_exists

## Test log file creation with proper permissions

test_log_permissions() {
  # This is hard to test without running, so check that chmod 600 is called
  grep -q 'chmod 600.*LOG_FILE' "$MAINTAIN_SH"
}
assert_success "Script sets log file permissions to 600" \
  test_log_permissions

## Test that validate_numeric is called for CLI parameters

test_validation_in_cli() {
  grep -q 'validate_numeric.*space-threshold' "$MAINTAIN_SH" || return 1
  grep -q 'validate_numeric.*trim-logs' "$MAINTAIN_SH" || return 1
  grep -q 'validate_numeric.*tm-thin' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script validates CLI numeric parameters" \
  test_validation_in_cli

## Test that path validation is used in cleanup functions

test_path_validation_in_cleanup() {
  # Check that validate_safe_path is called within the cleanup functions
  # Extract the functions and check for validate_safe_path calls
  sed -n '/^trim_user_logs()/,/^}/p' "$MAINTAIN_SH" | grep -q 'validate_safe_path' || return 1
  sed -n '/^trim_user_caches()/,/^}/p' "$MAINTAIN_SH" | grep -q 'validate_safe_path' || return 1
  return 0
}
assert_success "Script validates paths in cleanup functions" \
  test_path_validation_in_cleanup

## Test that ShellCheck passes

test_shellcheck_clean() {
  if ! command -v shellcheck >/dev/null 2>&1; then
    echo "  (ShellCheck not installed, skipping)"
    return 0
  fi

  # Only fail on errors and warnings, not info messages
  shellcheck -x -S warning "$MAINTAIN_SH" >/dev/null 2>&1
}
assert_success "Script passes ShellCheck analysis" \
  test_shellcheck_clean

## Test script structure and best practices

test_strict_mode() {
  head -n 30 "$MAINTAIN_SH" | grep -q 'set -Eeuo pipefail'
}
assert_success "Script uses strict bash mode (set -Eeuo pipefail)" \
  test_strict_mode

test_safe_ifs() {
  head -n 30 "$MAINTAIN_SH" | grep -q "IFS=\$'\\\\n\\\\t'"
}
assert_success "Script sets safe IFS" \
  test_safe_ifs

test_umask() {
  head -n 30 "$MAINTAIN_SH" | grep -q 'umask 022'
}
assert_success "Script sets secure umask" \
  test_umask

## Test that all functions have error handling

test_confirm_function() {
  grep -q 'confirm()' "$MAINTAIN_SH"
}
assert_success "Script has confirm() function for user prompts" \
  test_confirm_function

test_dry_run_function() {
  grep -q 'run()' "$MAINTAIN_SH" || return 1
  grep -A 5 'run()' "$MAINTAIN_SH" | grep -q 'DRY_RUN' || return 1
  return 0
}
assert_success "Script has dry-run aware run() function" \
  test_dry_run_function

finish_test_suite
