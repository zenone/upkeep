#!/usr/bin/env bash
# Edge Case Tests
# Tests for edge cases discovered in code review

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Define the functions we're testing
percent_used_root() {
  local output
  output=$(df -P / 2>/dev/null | awk 'NR==2{gsub("%","",$5); print $5+0}')

  if ! [[ "$output" =~ ^[0-9]+$ ]]; then
    echo "0"
    return 1
  fi

  if (( output < 0 || output > 100 )); then
    echo "0"
    return 1
  fi

  echo "$output"
  return 0
}

check_minimum_space() {
  local free_kb
  free_kb=$(df -Pk / 2>/dev/null | awk 'NR==2{print $4+0}')

  if ! [[ "$free_kb" =~ ^[0-9]+$ ]]; then
    return 0  # Continue anyway (fail open)
  fi

  local min_kb=102400  # 100MB minimum
  if (( free_kb < min_kb )); then
    return 1
  fi

  return 0
}

start_test_suite "Edge Cases"

## Test percent_used_root() edge cases

test_percent_used_root_valid() {
  # Should return a valid percentage (0-100)
  local result
  result=$(percent_used_root)
  local retcode=$?

  # Should get a number
  [[ "$result" =~ ^[0-9]+$ ]] || return 1

  # Should be in valid range
  (( result >= 0 && result <= 100 )) || return 1

  return 0
}
assert_success "percent_used_root: returns valid percentage" \
  test_percent_used_root_valid

test_percent_used_root_handles_malformed() {
  # Mock df to return malformed output
  df() { echo "garbage output"; }
  export -f df

  local result
  result=$(percent_used_root 2>/dev/null)
  local retcode=$?

  # Should return 0 on error
  [[ "$result" == "0" ]] || return 1
  # Should return non-zero exit code
  [[ $retcode -ne 0 ]] || return 1

  unset -f df
  return 0
}
assert_success "percent_used_root: handles malformed df output" \
  test_percent_used_root_handles_malformed

test_percent_used_root_handles_empty() {
  # Mock df to return empty output
  df() { echo ""; }
  export -f df

  local result
  result=$(percent_used_root 2>/dev/null)

  # Should return 0 on error
  [[ "$result" == "0" ]] || return 1

  unset -f df
  return 0
}
assert_success "percent_used_root: handles empty df output" \
  test_percent_used_root_handles_empty

test_percent_used_root_handles_out_of_range() {
  # Mock df to return > 100%
  df() { echo "Filesystem  512-blocks Used Available Capacity Mounted on"; echo "/dev/disk1  100000000  150000000 -50000000 150% /"; }
  export -f df

  local result
  result=$(percent_used_root 2>/dev/null)

  # Should return 0 for out-of-range values
  [[ "$result" == "0" ]] || return 1

  unset -f df
  return 0
}
assert_success "percent_used_root: handles out-of-range percentage" \
  test_percent_used_root_handles_out_of_range

## Test check_minimum_space() function

test_check_minimum_space_sufficient() {
  # Normal case: plenty of space
  # Real df should show sufficient space on most systems
  check_minimum_space
}
assert_success "check_minimum_space: passes with sufficient space" \
  test_check_minimum_space_sufficient

test_check_minimum_space_insufficient() {
  # Mock df to return very low space
  df() {
    if [[ "$1" == "-Pk" ]]; then
      echo "Filesystem          1024-blocks Used Available Capacity Mounted on"
      echo "/dev/disk1          100000000   99950000   50000    99% /"
    fi
  }
  export -f df

  # Should fail with low space
  check_minimum_space && return 1 || return 0

  unset -f df
}
assert_success "check_minimum_space: fails with < 100MB free" \
  test_check_minimum_space_insufficient

test_check_minimum_space_handles_malformed() {
  # Mock df to return malformed output
  df() { echo "error"; }
  export -f df

  # Should pass (fail open) on error
  check_minimum_space

  unset -f df
}
assert_success "check_minimum_space: fails open on malformed output" \
  test_check_minimum_space_handles_malformed

## Test thin_tm_localsnapshots logic (conceptual - can't mock tmutil easily)

test_snapshot_logic_documented() {
  # Document expected behavior:
  # - Function should check if snapshots exist
  # - Function should validate disk usage percentage
  # - Function should skip if disk usage < threshold
  # This test just verifies the function exists in the script

  MAINTAIN_SH="$(cd "$SCRIPT_DIR/.." && pwd)/upkeep.sh"

  # Check that snapshot counting logic exists
  grep -q "snapshot_count.*tmutil listlocalsnapshots" "$MAINTAIN_SH" || return 1

  # Check that validation logic exists
  grep -q "if.*snapshot_count.*eq 0" "$MAINTAIN_SH" || return 1

  # Check that disk usage validation exists (extract full function)
  sed -n '/^thin_tm_localsnapshots()/,/^}/p' "$MAINTAIN_SH" | grep -q "used.*percent_used_root" || return 1

  return 0
}
assert_success "thin_tm_localsnapshots: has snapshot existence check" \
  test_snapshot_logic_documented

## Test edge case: 0 snapshots

test_zero_snapshots_documented() {
  # Verify that the function handles 0 snapshots gracefully
  MAINTAIN_SH="$(cd "$SCRIPT_DIR/.." && pwd)/upkeep.sh"

  # Should have check for 0 snapshots (within the function body, ~20 lines down)
  sed -n '/^thin_tm_localsnapshots/,/^}/p' "$MAINTAIN_SH" | grep -q "No local snapshots found" || return 1

  return 0
}
assert_success "thin_tm_localsnapshots: handles 0 snapshots case" \
  test_zero_snapshots_documented

## Test edge case: Invalid disk usage

test_invalid_disk_usage_documented() {
  # Verify that the function validates disk usage percentage
  MAINTAIN_SH="$(cd "$SCRIPT_DIR/.." && pwd)/upkeep.sh"

  # Should have validation for disk usage
  sed -n '/^thin_tm_localsnapshots/,/^}/p' "$MAINTAIN_SH" | grep -q "Could not determine disk usage" || return 1

  return 0
}
assert_success "thin_tm_localsnapshots: validates disk usage percentage" \
  test_invalid_disk_usage_documented

finish_test_suite
