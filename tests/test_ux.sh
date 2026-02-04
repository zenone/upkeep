#!/usr/bin/env bash
# UX Feature Tests
# Tests for Phase 2.5 UX improvements

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

MAINTAIN_SH="$(cd "$SCRIPT_DIR/.." && pwd)/upkeep.sh"

start_test_suite "UX Features"

## Test --status flag exists and works

test_status_flag_exists() {
  grep -q '\-\-status)' "$MAINTAIN_SH" || return 1
  grep -q 'DO_STATUS' "$MAINTAIN_SH" || return 1
  grep -q 'status_dashboard()' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script has --status flag and dashboard function" \
  test_status_flag_exists

test_status_dashboard_components() {
  # Check that dashboard includes key components
  sed -n '/^status_dashboard()/,/^}/p' "$MAINTAIN_SH" | grep -q "Disk Usage" || return 1
  sed -n '/^status_dashboard()/,/^}/p' "$MAINTAIN_SH" | grep -q "Security" || return 1
  sed -n '/^status_dashboard()/,/^}/p' "$MAINTAIN_SH" | grep -q "Overall Health" || return 1
  return 0
}
assert_success "Status dashboard includes disk, security, and health metrics" \
  test_status_dashboard_components

## Test --quiet mode

test_quiet_flag_exists() {
  grep -q '\-\-quiet)\|\-q)' "$MAINTAIN_SH" || return 1
  grep -q 'QUIET=' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script has --quiet/-q flag" \
  test_quiet_flag_exists

test_quiet_mode_logic() {
  # Check that QUIET variable is respected in log functions
  grep -q 'QUIET' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Quiet mode logic implemented" \
  test_quiet_mode_logic

## Test --no-emoji flag

test_no_emoji_flag_exists() {
  grep -q '\-\-no-emoji)' "$MAINTAIN_SH" || return 1
  grep -q 'NO_EMOJI' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Script has --no-emoji flag" \
  test_no_emoji_flag_exists

test_emoji_fallback_logic() {
  # Check that emoji symbols have text fallbacks
  grep -q 'NO_EMOJI' "$MAINTAIN_SH" || return 1
  grep -q '\[i\]' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Emoji symbols have text fallbacks" \
  test_emoji_fallback_logic

## Test progress spinner function

test_spinner_function_exists() {
  grep -q '^spinner()' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Spinner function exists" \
  test_spinner_function_exists

test_spinner_respects_quiet() {
  # Spinner should check for QUIET mode
  sed -n '/^spinner()/,/^}/p' "$MAINTAIN_SH" | grep -q 'QUIET' || return 1
  return 0
}
assert_success "Spinner respects quiet mode" \
  test_spinner_respects_quiet

test_run_with_progress_exists() {
  grep -q '^run_with_progress()' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "run_with_progress function exists" \
  test_run_with_progress_exists

## Test enhanced color system

test_extended_colors() {
  # Check that CYAN color is added (extension beyond original colors)
  grep -q 'CYAN=' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Extended color palette defined" \
  test_extended_colors

test_box_drawing_characters() {
  # Check that box drawing characters are defined
  grep -q 'BOX_H=.*BOX_V=.*BOX_TL=' "$MAINTAIN_SH" || return 1
  return 0
}
assert_success "Box drawing characters defined" \
  test_box_drawing_characters

## Test enhanced section function

test_section_uses_box_drawing() {
  # Section function should use box drawing characters
  sed -n '/^section()/,/^}/p' "$MAINTAIN_SH" | grep -q 'BOX_' || return 1
  return 0
}
assert_success "Section function uses box drawing" \
  test_section_uses_box_drawing

## Test enhanced error messages

test_error_messages_have_suggestions() {
  # Check key error messages include "Try this" or "How to fix"
  sed -n '/^refuse_root()/,/^}/p' "$MAINTAIN_SH" | grep -q "Try this" || return 1
  sed -n '/^check_sudo_security()/,/^}/p' "$MAINTAIN_SH" | grep -q "How to fix" || return 1
  sed -n '/^check_minimum_space()/,/^}/p' "$MAINTAIN_SH" | grep -q "Free up space" || return 1
  return 0
}
assert_success "Error messages include actionable suggestions" \
  test_error_messages_have_suggestions

test_validation_errors_have_examples() {
  # Check that validate_numeric includes examples
  sed -n '/^validate_numeric()/,/^}/p' "$MAINTAIN_SH" | grep -q "Examples:" || return 1
  return 0
}
assert_success "Validation errors include usage examples" \
  test_validation_errors_have_examples

## Test help output includes new flags

test_help_includes_status() {
  "$MAINTAIN_SH" --help 2>&1 | grep -q '\-\-status' || return 1
  return 0
}
assert_success "Help output includes --status flag" \
  test_help_includes_status

test_help_includes_quiet() {
  "$MAINTAIN_SH" --help 2>&1 | grep -q '\-\-quiet' || return 1
  return 0
}
assert_success "Help output includes --quiet flag" \
  test_help_includes_quiet

test_help_includes_no_emoji() {
  "$MAINTAIN_SH" --help 2>&1 | grep -q '\-\-no-emoji' || return 1
  return 0
}
assert_success "Help output includes --no-emoji flag" \
  test_help_includes_no_emoji

finish_test_suite
