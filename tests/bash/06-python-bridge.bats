#!/usr/bin/env bats
# Tests for bash-Python bridge integration

load test_helper

@test "Python bridge check command works" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  # Test the bridge check command
  run python3 -m mac_maintenance.bridge check
  echo "Output: $output" >&3

  # Should output PYTHON_AVAILABLE=1 if working
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"
  [[ "$output" =~ VERSION= ]]
}

@test "Python bridge system-info command works" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  run python3 -m mac_maintenance.bridge check
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"

  # Test system-info command
  run python3 -m mac_maintenance.bridge system-info
  echo "Output: $output" >&3
  [ "$status" -eq 0 ]
  [[ "$output" =~ PLATFORM= ]]
  [[ "$output" =~ VERSION= ]]
}

@test "Python bridge analyze command works" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  run python3 -m mac_maintenance.bridge check
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"

  # Create test directory
  local test_dir="${BATS_TMPDIR}/bridge-test-$$"
  mkdir -p "$test_dir"
  echo "test content" > "$test_dir/file1.txt"
  echo "more test content" > "$test_dir/file2.txt"

  # Test analyze command
  run python3 -m mac_maintenance.bridge analyze "$test_dir"
  echo "Output: $output" >&3
  [ "$status" -eq 0 ]
  [[ "$output" =~ TOTAL_SIZE_GB= ]]
  [[ "$output" =~ FILE_COUNT= ]]
  [[ "$output" =~ DIR_COUNT= ]]

  # Cleanup
  rm -rf "$test_dir"
}

@test "Python bridge analyze JSON output works" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  run python3 -m mac_maintenance.bridge check
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"

  # Create test directory
  local test_dir="${BATS_TMPDIR}/bridge-json-test-$$"
  mkdir -p "$test_dir"
  echo "test content" > "$test_dir/file1.txt"

  # Test JSON output
  run python3 -m mac_maintenance.bridge analyze "$test_dir" --json
  echo "Output: $output" >&3
  [ "$status" -eq 0 ]
  [[ "$output" =~ "\"status\":" ]]
  [[ "$output" =~ "\"total_size\":" ]]

  # Cleanup
  rm -rf "$test_dir"
}

@test "maintain.sh detects Python availability" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  run python3 -m mac_maintenance.bridge check
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"

  # Run maintain.sh and check if it detects Python
  run timeout 5s "${SCRIPT}" --status
  echo "Output: $output" >&3
  [ "$status" -eq 0 ]

  # Should mention Python features if available
  [[ "$output" =~ "Python features available" ]] || [[ "$output" =~ "System Health Dashboard" ]]
}

@test "maintain.sh --tui flag exists" {
  # Check that --tui is documented in help
  run "${SCRIPT}" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "--tui" ]]
}

@test "Python-enhanced storage analysis works when available" {
  if ! command -v python3 >/dev/null 2>&1; then
    skip "Python3 not available"
  fi

  run python3 -m mac_maintenance.bridge check
  [[ "$output" =~ PYTHON_AVAILABLE=1 ]] || skip "Python package not installed"

  # Run space report - should use Python analyzer if available
  run timeout 30s "${SCRIPT}" --space-report --quiet
  echo "Output: $output" >&3
  [ "$status" -eq 0 ]

  # Should complete without errors
  [[ "$output" =~ "complete" ]] || [[ "$output" =~ "Python" ]]
}
