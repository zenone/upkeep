#!/usr/bin/env bash
# shellcheck disable=SC2155
# macOS Tahoe Maintenance Toolkit (safe-by-default, OnyX-ish but guardrailed)
#
# Philosophy:
# - Default mode: AUDIT + REPORT (no destructive actions)
# - "Maintenance" that actually matters: updates, disk health, free space, targeted fixes
# - Heavier rebuild/cleanup tasks are opt-in and confirmation-gated
#
# Usage:
#   ./upkeep.sh --help
#
# Recommended runs:
#   ./upkeep.sh --all-safe
#   ./upkeep.sh --all-safe --install-macos-updates
#   ./upkeep.sh --all-deep --install-macos-updates
#
# Notes:
# - Do NOT run as root. Script will use sudo only for specific tasks.
# - Works on macOS Tahoe (and should be compatible with recent macOS versions).
#
set -Eeuo pipefail
IFS=$'\n\t'
umask 022

# Ensure system utilities are in PATH (required for diskutil, tmutil, softwareupdate, etc.)
# Some execution contexts (sandboxed shells, certain daemons) may not include /usr/sbin
export PATH="/usr/sbin:/sbin:$PATH"

# Prevent terminal width truncation (Task #105 fix)
# In non-interactive contexts (daemon, cron, ssh without tty), COLUMNS defaults to 80
# This causes programs to truncate output at 80 characters
# Setting COLUMNS=999 prevents truncation for web UI display
# Defense in depth: daemon also sets this, but we set it here too
export COLUMNS=999
export LINES=999

# COLUMNS/LINES set above to prevent output truncation (Task #121)

########################################
# UI / Logging
########################################
if [[ -n "${NO_COLOR:-}" ]]; then
  RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; BOLD=""; NC=""
elif command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); BLUE=$(tput setaf 4)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; BOLD=""; NC=""
fi

# Status symbols with emoji fallback (use --no-emoji to disable emojis)
if [[ -n "${NO_EMOJI:-}" ]]; then
  INFO="[i]"; OK="[✓]"; WARN="[!]"; FAIL="[✗]"
else
  INFO="ℹ️ "; OK="✅"; WARN="⚠️ "; FAIL="❌"
fi

# Box drawing characters for sections
BOX_H="─"; BOX_V="│"; BOX_TL="┌"; BOX_TR="┐"; BOX_BL="└"; BOX_BR="┘"

LOG_DIR="${HOME}/Library/Logs/upkeep"
mkdir -p "${LOG_DIR}"
chmod 700 "${LOG_DIR}"  # Restrict directory access to owner only
LOG_FILE="${LOG_DIR}/upkeep-$(date +%Y%m%d-%H%M%S).log"
touch "${LOG_FILE}"
chmod 600 "${LOG_FILE}"  # Restrict log file access to owner only (security: may contain sensitive command output)

# Save original stderr BEFORE exec redirect, so we can write to it in JSON mode.
# This allows warnings/errors to go to stderr even after the exec below merges stderr→stdout.
exec 9>&2
ORIGINAL_STDERR=9

exec > >(tee -a "${LOG_FILE}") 2>&1

ts() { date +"%Y-%m-%d %H:%M:%S"; }

# 🔧 Feature Flag: FILTER_CONTROL_CHARS (easy disable if issues found)
# Default: true (filters carriage returns and other control characters that can cause truncation)
# Set to false to disable filtering
FILTER_CONTROL_CHARS="${FILTER_CONTROL_CHARS:-true}"

clean_output() {
  # Remove control characters that can cause truncation or display issues
  # Business logic:
  # - Removes carriage returns (\r) that overwrite previous text
  # - Removes backspaces (\b) that delete characters
  # - Removes ALL ANSI escape codes (colors, cursor movement, etc.)
  # - Removes other control characters that corrupt web UI output
  # - Preserves newlines (\n) for proper line breaks
  # - Critical for web interface output (prevents "diskutiir" truncation bug)
  local text="$*"

  if [[ "$FILTER_CONTROL_CHARS" == "true" ]]; then
    # Remove carriage returns (they overwrite text in terminals but cause truncation in logs)
    text="${text//$'\r'/}"

    # Remove backspaces (they delete previous characters)
    text="${text//$'\b'/}"

    # Remove all ANSI escape sequences (not just colors)
    # This includes: colors, cursor movement, clear screen, character set selection, etc.
    # Pattern explanation:
    #   \x1b\[ - ESC[ sequence start (CSI)
    #   [0-9;?]* - zero or more digits, semicolons, or question marks
    #   [a-zA-Z] - command letter (m=color, K=clear line, H=cursor pos, etc.)
    #   \x1b\][^\x07]* - OSC sequences (Operating System Command)
    #   \x07 - BEL character that ends OSC
    #   \x1b[()] - Character set selection (e.g., ESC(B from tput sgr0)
    text=$(echo "$text" | sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g; s/\x1b\][^\x07]*\x07//g; s/\x1b[()].//g' 2>/dev/null || echo "$text")

    # Remove other problematic control characters but keep newlines and tabs
    # \x00-\x08: NULL through backspace (except \x08 already removed)
    # \x0B-\x0C: vertical tab, form feed
    # \x0E-\x1F: shift out through unit separator
    text=$(echo "$text" | tr -d '\000-\010\013\014\016-\037' 2>/dev/null || echo "$text")
  fi

  echo -n "$text"
}

log()        { [[ "${QUIET:-0}" -eq 0 ]] && echo -e "$(ts) $(clean_output "$*")" || echo -e "$(ts) $(clean_output "$*")" >> "${LOG_FILE}"; }
# Always output (for errors/warnings in quiet mode).
# In JSON mode, send all human text to stderr so stdout remains machine-readable.
log_always() {
  if [[ "${OUTPUT_JSON:-0}" -eq 1 ]]; then
    # In JSON mode, send human-readable text to the ORIGINAL stderr (fd 9),
    # which was saved before the exec redirect merged stderr→stdout.
    echo -e "$(ts) $(clean_output "$*")" >&${ORIGINAL_STDERR:-2}
  else
    echo -e "$(ts) $(clean_output "$*")"
  fi
}
# Print text only in non-JSON mode (use for detail output that would corrupt machine-readable JSON).
print_human() {
  [[ "${OUTPUT_JSON:-0}" -eq 1 ]] && return 0
  echo -e "$@"
}

section() {
  local text="$*"
  local width=60
  local padding=$(( (width - ${#text} - 2) / 2 ))
  local line=""
  for ((i=0; i<width; i++)); do line+="$BOX_H"; done

  if [[ -z "${QUIET:-}" ]]; then
    echo ""
    log "${CYAN}${BOLD}${BOX_TL}${line}${BOX_TR}${NC}"
    printf "%s " "$(ts)"
    echo -e "${CYAN}${BOLD}${BOX_V}$(printf '%*s' $padding '')${text}$(printf '%*s' $padding '')${BOX_V}${NC}"
    log "${CYAN}${BOLD}${BOX_BL}${line}${BOX_BR}${NC}"
  else
    echo -e "$(ts) --- $text ---" >> "${LOG_FILE}"
  fi
}

info()       { log "${BLUE}${INFO}${NC} $*"; }
success()    { log "${GREEN}${OK} $*${NC}"; }
warning()    { log_always "${YELLOW}${WARN}${NC} $*"; }  # Always show warnings
error()      { log_always "${RED}${FAIL} $*${NC}"; }     # Always show errors

die()        { error "$*"; exit 1; }

# JSON output helpers
json_escape() {
  # Escape JSON special characters
  local str="$1"
  str="${str//\\/\\\\}"  # Backslash
  str="${str//\"/\\\"}"  # Double quote
  str="${str//$'\n'/\\n}"  # Newline
  str="${str//$'\r'/\\r}"  # Carriage return
  str="${str//$'\t'/\\t}"  # Tab
  echo -n "$str"
}

json_output() {
  # Output JSON if OUTPUT_JSON=1, otherwise skip
  [[ "${OUTPUT_JSON:-0}" -eq 1 ]] && echo "$@"
}

json_result() {
  # Format operation result as JSON
  # Usage: json_result "operation_name" "status" "message"
  local operation="$1"
  local status="$2"
  local message="$3"

  if [[ "${OUTPUT_JSON:-0}" -eq 1 ]]; then
    cat <<EOF
{
  "operation": "$(json_escape "$operation")",
  "status": "$(json_escape "$status")",
  "message": "$(json_escape "$message")",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
  fi
}

# Progress spinner for long operations
spinner() {
  local pid=$1
  local message="${2:-Working}"
  local delay=0.1
  local spinstr='|/-\\'

  # Disable spinner in non-interactive mode or if QUIET is set
  if [[ ! -t 1 ]] || [[ -n "${QUIET:-}" ]]; then
    wait "$pid"
    return $?
  fi

  while kill -0 "$pid" 2>/dev/null; do
    local temp=${spinstr#?}
    printf "\r${CYAN}%s${NC} %s " "${spinstr:0:1}" "$message"
    spinstr=$temp${spinstr%"$temp"}
    sleep $delay
  done
  printf "\r%*s\r" $((${#message} + 4)) ""  # Clear the line

  wait "$pid"
  return $?
}

on_interrupt() { error "Interrupted."; exit 1; }
trap on_interrupt SIGINT SIGTERM SIGHUP SIGQUIT

########################################
# Guards / Helpers
########################################
command_exists() { command -v "$1" >/dev/null 2>&1; }

detect_homebrew() {
  # Intelligent Homebrew detection for ARM and Intel Macs
  # Sets BREW_CMD environment variable with correct command
  # Returns 0 if found, 1 if not found

  # Method 1: Direct brew command in PATH
  if command -v brew >/dev/null 2>&1; then
    export BREW_CMD="brew"
    return 0
  fi

  # Method 2: arch --arm64 brew (ARM Mac where brew not in PATH)
  if command -v arch >/dev/null 2>&1; then
    if arch --arm64 brew --version >/dev/null 2>&1; then
      export BREW_CMD="arch --arm64 brew"
      return 0
    fi
  fi

  # Method 3: ARM64 default installation path
  if [ -x "/opt/homebrew/bin/brew" ]; then
    export BREW_CMD="/opt/homebrew/bin/brew"
    # Add to PATH for this session
    export PATH="/opt/homebrew/bin:$PATH"
    return 0
  fi

  # Method 4: Intel default installation path
  if [ -x "/usr/local/bin/brew" ]; then
    export BREW_CMD="/usr/local/bin/brew"
    export PATH="/usr/local/bin:$PATH"
    return 0
  fi

  # Not found
  export BREW_CMD=""
  return 1
}

detect_mas() {
  # Check if mas CLI is installed (cached for performance)
  # Only check once per script execution to avoid redundant "already installed" messages
  if [ -n "${MAS_CMD+x}" ]; then
    # Already detected in this session
    [ -n "$MAS_CMD" ] && return 0 || return 1
  fi

  # Try common locations (Homebrew ARM64, Homebrew Intel, system)
  local mas_paths=(
    "/opt/homebrew/bin/mas"
    "/usr/local/bin/mas"
    "$(command -v mas 2>/dev/null)"
  )

  for mas_path in "${mas_paths[@]}"; do
    if [[ -n "$mas_path" ]] && [[ -x "$mas_path" ]]; then
      export MAS_CMD="$mas_path"
      return 0
    fi
  done

  # Not found
  export MAS_CMD=""
  return 1
}

get_actual_user_home() {
  # Get actual user's home directory (not root's) when running via sudo/daemon
  # Returns the real user's home directory
  local actual_user="${SUDO_USER:-${USER}}"
  local actual_home

  if [ -n "${ACTUAL_HOME:-}" ]; then
    # Already set by caller (daemon)
    echo "${ACTUAL_HOME}"
    return 0
  elif [ "$actual_user" = "root" ] || [ -z "$actual_user" ]; then
    # Running as root without SUDO_USER, use $HOME
    echo "$HOME"
    return 0
  else
    # Get home directory for actual user
    actual_home=$(eval echo "~$actual_user" 2>/dev/null)
    if [ -d "$actual_home" ]; then
      echo "$actual_home"
      return 0
    fi
  fi

  # Fallback to $HOME
  echo "$HOME"
  return 0
}

run_as_user() {
  # Run command as actual user (not root)
  # This allows commands like brew and mas to run with correct user context
  # even when the script is running as root (daemon)
  #
  # Usage: run_as_user command args...
  # Example: run_as_user brew update
  #
  # Business logic:
  # - If running as root AND have actual user → run as that user via sudo -u
  # - Otherwise → run normally
  # - Uses -H flag to set HOME to user's home directory
  # - Preserves SUDO_ASKPASS to prevent nested sudo prompts (Task #113 fix)
  #
  # Dry-run behavior:
  # - In --dry-run mode we must NOT execute user-context commands (brew/mas/etc),
  #   because they can hang (auto-update/network) and violate the "safe" contract.
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    # In --output-json mode, stdout must remain machine-readable JSON.
    # Avoid emitting human text that may be redirected into stdout via `2>&1`.
    if [[ "${OUTPUT_JSON:-0}" -eq 1 ]]; then
      return 0
    fi
    warning "DRY-RUN: $*"
    return 0
  fi

  local actual_user="${ACTUAL_USER:-${SUDO_USER:-${USER}}}"

  # Check if we're root and have an actual user to run as
  if [ "$(id -u)" -eq 0 ] && [ -n "$actual_user" ] && [ "$actual_user" != "root" ]; then
    # Running as root with actual user - run command as that user
    # -n: Non-interactive (no password prompt - we're already root via daemon)
    # -H: Set HOME to target user's home directory
    # --preserve-env=SUDO_ASKPASS: Pass through SUDO_ASKPASS for nested sudo calls
    #     Critical for Homebrew casks that call sudo in post-install scripts
    #     Prevents "sudo: a terminal is required to read the password" errors
    # This is critical for Homebrew and mas which check user context
    sudo -n -H --preserve-env=SUDO_ASKPASS -u "$actual_user" "$@"
  else
    # Not root, or no actual user, or actual user is root - run normally
    "$@"
  fi
}

validate_numeric() {
  # Validates that a value is numeric and within an optional range
  # Usage: validate_numeric VALUE NAME [MIN] [MAX]
  local value="$1"
  local name="$2"
  local min="${3:-0}"
  local max="${4:-}"

  # Check if value is numeric
  if ! [[ "$value" =~ ^[0-9]+$ ]]; then
    error "Invalid $name: must be a positive integer (got: '$value')"
    error ""
    error "Examples:"
    error "  --space-threshold 85      (disk usage % to warn at: 50-99)"
    error "  --trim-logs 30            (days to keep: 1-3650)"
    error "  --tm-thin-bytes 20GB      (snapshot size: 1-100 GB)"
    die ""
  fi

  # Check minimum
  if (( value < min )); then
    error "Invalid $name: must be at least $min (got: $value)"
    error ""
    error "Try: $name $min"
    die ""
  fi

  # Check maximum (if provided)
  if [[ -n "$max" ]] && (( value > max )); then
    error "Invalid $name: must be at most $max (got: $value)"
    error ""
    error "Try: $name $max"
    die ""
  fi
}

validate_safe_path() {
  # Validates that a path resolves to an expected location (prevents symlink attacks)
  # Usage: validate_safe_path ACTUAL_PATH EXPECTED_PATH DESCRIPTION
  local actual="$1"
  local expected="$2"
  local description="$3"

  # Check directory exists
  if [[ ! -d "$actual" ]]; then
    warning "Directory does not exist: $actual"
    return 1
  fi

  # Resolve to absolute path (following symlinks)
  local resolved
  resolved="$(cd "$actual" && pwd -P 2>/dev/null)" || die "Failed to resolve path: $actual"

  # Also resolve the expected path (to handle macOS /var -> /private/var symlink)
  local expected_resolved
  if [[ -d "$expected" ]]; then
    expected_resolved="$(cd "$expected" && pwd -P 2>/dev/null)" || expected_resolved="$expected"
  else
    # If expected doesn't exist yet, just normalize it
    expected_resolved="$expected"
  fi

  # Verify resolved path matches expected (allow macOS /var <-> /private/var equivalence)
  if [[ "$resolved" != "$expected_resolved" ]]; then
    error "SECURITY: Path resolution mismatch for $description"
    error "  Expected: $expected_resolved"
    error "  Got:      $resolved"
    error "  Original: $actual"
    error ""
    error "This could indicate a symlink attack. Refusing to proceed."
    die "Path validation failed"
  fi

  return 0
}

# Safety Threshold Functions (Task #109)
# Business logic: Prevent operations when disk dangerously full
# Research: Industry standards (80% warn, 90% critical, 95% danger)

get_disk_usage() {
  # Get current disk usage percentage for system volume
  # Returns: Integer percentage (0-100) or empty string on failure
  #
  # Business logic:
  # - Only checks system volume (/) not external drives
  # - APFS volumes share container space, check both
  # - Graceful failure if df command unavailable
  #
  # Edge cases handled:
  # - df output format variations
  # - APFS container vs volume space reporting
  # - Symbolic links /var -> /private/var

  # Try df command (most reliable)
  local usage
  usage=$(df -H / 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//')

  if [[ -n "$usage" ]] && [[ "$usage" =~ ^[0-9]+$ ]]; then
    echo "$usage"
    return 0
  fi

  # Fallback: Try diskutil (macOS-specific)
  usage=$(diskutil info / 2>/dev/null | grep "Volume Used Space" | awk '{print $5}' | sed 's/%//' | sed 's/(//')

  if [[ -n "$usage" ]] && [[ "$usage" =~ ^[0-9]+$ ]]; then
    echo "$usage"
    return 0
  fi

  # Unable to determine disk usage
  return 1
}

get_disk_usage_details() {
  # Get detailed disk usage info for reporting
  # Returns: "45.2 GB available (78% used)" format
  #
  # Used for: Before/after reporting, dashboard display

  local available used total percent
  available=$(df -H / 2>/dev/null | awk 'NR==2 {print $4}')
  used=$(df -H / 2>/dev/null | awk 'NR==2 {print $3}')
  total=$(df -H / 2>/dev/null | awk 'NR==2 {print $2}')
  percent=$(get_disk_usage)

  if [[ -n "$available" ]] && [[ -n "$percent" ]]; then
    echo "${available} available (${percent}% used, ${used}/${total})"
  else
    echo "Unable to determine disk usage"
  fi
}

check_disk_safety_thresholds() {
  # Check if disk usage is safe for proceeding with operations
  # Returns: 0 if safe, 1 if user declined to proceed
  #
  # Thresholds (based on industry research):
  # - 80-89%: Warning (show info, proceed)
  # - 90-94%: Critical (require confirmation)
  # - 95%+:   Danger (require typing "PROCEED")
  #
  # Feature flag: USE_SAFETY_THRESHOLDS (default: true)
  # Business logic: Automation mode (ASSUME_YES) logs warnings but doesn't block

  # Feature flag check
  local USE_SAFETY_THRESHOLDS="${USE_SAFETY_THRESHOLDS:-true}"
  if [[ "$USE_SAFETY_THRESHOLDS" != "true" ]]; then
    return 0
  fi

  # Get current disk usage
  local usage
  usage=$(get_disk_usage)

  if [[ -z "$usage" ]]; then
    # Unable to check disk usage - proceed with warning
    warning "⚠️  Unable to check disk space (proceeding with caution)"
    info "Safety thresholds skipped - df command unavailable"
    return 0
  fi

  # Thresholds
  local DISK_WARNING_THRESHOLD=80
  local DISK_CRITICAL_THRESHOLD=90
  local DISK_DANGER_THRESHOLD=95

  # Under warning threshold - all clear
  if (( usage < DISK_WARNING_THRESHOLD )); then
    return 0
  fi

  # Warning level (80-89%)
  if (( usage >= DISK_WARNING_THRESHOLD && usage < DISK_CRITICAL_THRESHOLD )); then
    warning "⚠️  Disk usage: ${usage}% (WARNING threshold)"
    info "$(get_disk_usage_details)"
    info "Consider freeing space soon - operations may slow down"

    # In automation mode, log but don't block
    if [[ "${ASSUME_YES:-0}" -eq 1 ]]; then
      info "Automation mode: Proceeding despite warning"
      return 0
    fi

    # Interactive: Show warning but allow proceeding
    return 0
  fi

  # Critical level (90-94%)
  if (( usage >= DISK_CRITICAL_THRESHOLD && usage < DISK_DANGER_THRESHOLD )); then
    error "🚨 CRITICAL: Disk usage ${usage}% (>${DISK_CRITICAL_THRESHOLD}% threshold)"
    info "$(get_disk_usage_details)"
    warning "Operations may fail due to low disk space"
    info "Recommendation: Run cleanup operations or delete files"
    echo ""

    # In automation mode, log but don't block
    if [[ "${ASSUME_YES:-0}" -eq 1 ]]; then
      warning "Automation mode: Proceeding despite CRITICAL disk usage"
      return 0
    fi

    # Interactive: Require explicit confirmation
    if ! confirm "Proceed anyway? (CRITICAL disk space)"; then
      info "Operation cancelled due to low disk space"
      return 1
    fi

    return 0
  fi

  # Danger level (95%+)
  if (( usage >= DISK_DANGER_THRESHOLD )); then
    error "🔴 DANGER: Disk usage ${usage}% (>${DISK_DANGER_THRESHOLD}% threshold)"
    error "$(get_disk_usage_details)"
    error "System may become unstable at this disk usage level"
    error "Operations likely to fail or cause system issues"
    echo ""
    info "URGENT: Free disk space immediately"
    info "Safe operations: Delete large files, empty Trash, run cleanup"
    echo ""

    # In automation mode, log but don't block (user responsibility)
    if [[ "${ASSUME_YES:-0}" -eq 1 ]]; then
      error "Automation mode: Proceeding at DANGER disk usage (${usage}%)"
      error "WARNING: Operations may fail or cause system instability"
      return 0
    fi

    # Interactive: Require typing "PROCEED" to confirm
    warning "Type 'PROCEED' to continue at your own risk:"
    read -r confirmation

    if [[ "$confirmation" != "PROCEED" ]]; then
      info "Operation cancelled - wise decision given disk space"
      info "Please free space before running maintenance operations"
      return 1
    fi

    warning "User overrode ${usage}% DANGER threshold - proceeding at user's risk"
    return 0
  fi

  # Should never reach here, but default to safe
  return 0
}

get_deletion_stats() {
  # Calculate file count and total size for deletion preview (Task #111)
  # Shows users exactly what will be deleted before confirmation
  # Business logic: Users should never be surprised by deletions (DaisyDisk principle)
  #
  # Args:
  #   $1: path to scan
  #   $2: age in days (for -mtime +N)
  #   $3: file pattern (e.g., "*.log" or "*")
  #
  # Exports:
  #   DELETION_FILE_COUNT: Number of files found (or "100,000+" if limit reached)
  #   DELETION_SIZE_MB: Total size in MB (may be empty if skipped for performance)
  #
  # Feature flag: SHOW_DELETION_STATS (default: true)
  # Performance: Timeout at 30 seconds, limit to 100,000 files

  local path="$1"
  local age_days="$2"
  local pattern="${3:-*}"  # Default to all files

  # Reset exports
  export DELETION_FILE_COUNT=""
  export DELETION_SIZE_MB=""

  # Feature flag: Allow disabling if causes performance issues
  if [[ "${SHOW_DELETION_STATS:-true}" != "true" ]]; then
    return 0
  fi

  # Validate inputs
  if [[ ! -d "$path" ]]; then
    return 0
  fi

  local count=0
  local size_kb=0
  local timeout_secs=30
  local max_count=100000  # Performance limit

  # Count files with timeout (defensive: don't hang script)
  # Use timeout command if available (common on GNU/Linux, less common on macOS)
  if command_exists gtimeout; then
    # GNU timeout (brew install coreutils)
    count=$(gtimeout ${timeout_secs}s find "$path" -type f -name "$pattern" -mtime +"$age_days" 2>/dev/null | head -n ${max_count} | wc -l | tr -d ' ')
  elif command_exists timeout; then
    # BSD/GNU timeout (may not exist on stock macOS)
    count=$(timeout ${timeout_secs}s find "$path" -type f -name "$pattern" -mtime +"$age_days" 2>/dev/null | head -n ${max_count} | wc -l | tr -d ' ')
  else
    # Fallback: No timeout, but limit output to prevent hanging
    # Uses head to stop find early (doesn't scan entire filesystem)
    count=$(find "$path" -type f -name "$pattern" -mtime +"$age_days" 2>/dev/null | head -n ${max_count} | wc -l | tr -d ' ')
  fi

  # Handle count result
  if [[ -z "$count" ]] || [[ ! "$count" =~ ^[0-9]+$ ]]; then
    # Count failed or invalid
    return 0
  fi

  # Export count (with annotation if limit reached)
  if [[ $count -ge $max_count ]]; then
    export DELETION_FILE_COUNT="${max_count}+"
  else
    export DELETION_FILE_COUNT="$count"
  fi

  # Calculate total size (only for smaller counts - performance consideration)
  # Skip size for very large operations (>10,000 files) to avoid long delays
  # Business logic: For 50,000 files, users care about COUNT not exact size
  if [[ $count -gt 0 ]] && [[ $count -lt 10000 ]]; then
    # Calculate size in KB, convert to MB
    # Using find -exec du is slow but accurate
    if command_exists gtimeout; then
      size_kb=$(gtimeout ${timeout_secs}s find "$path" -type f -name "$pattern" -mtime +"$age_days" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
    elif command_exists timeout; then
      size_kb=$(timeout ${timeout_secs}s find "$path" -type f -name "$pattern" -mtime +"$age_days" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
    else
      # Fallback: Calculate size without timeout (risky for large counts, hence 10K limit)
      size_kb=$(find "$path" -type f -name "$pattern" -mtime +"$age_days" -exec du -sk {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
    fi

    # Convert KB to MB
    if [[ -n "$size_kb" ]] && [[ "$size_kb" =~ ^[0-9]+$ ]] && [[ $size_kb -gt 0 ]]; then
      export DELETION_SIZE_MB=$((size_kb / 1024))
    fi
  fi

  return 0
}

confirm() {
  local msg="$1"
  if [[ "${ASSUME_YES:-0}" -eq 1 ]]; then return 0; fi
  read -r -p "$msg [y/N]: " resp
  [[ "$resp" =~ ^([yY]([eE][sS])?)$ ]]
}

run() {
  # Print the command, then run it (or skip on dry-run)
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    # In JSON mode, stdout must remain machine-readable.
    [[ "${OUTPUT_JSON:-0}" -eq 1 ]] && return 0
    warning "DRY-RUN: $*"
    return 0
  fi
  info "RUN: $*"
  "$@"
}

run_sudo() {
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    # In JSON mode, stdout must remain machine-readable.
    [[ "${OUTPUT_JSON:-0}" -eq 1 ]] && return 0
    warning "DRY-RUN (sudo): $*"
    return 0
  fi

  # Check if we can run sudo without password prompt (non-interactive safe)
  if ! sudo -n true 2>/dev/null; then
    warning "Sudo requires password (non-interactive) - skipping: $*"
    return 0
  fi

  info "RUN (sudo): $*"
  sudo "$@"
}

run_with_progress() {
  # Run a command with a progress spinner for long operations
  # Usage: run_with_progress "Message" command args...
  local message="$1"
  shift

  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    # In JSON mode, stdout must remain machine-readable.
    [[ "${OUTPUT_JSON:-0}" -eq 1 ]] && return 0
    warning "DRY-RUN: $*"
    return 0
  fi

  info "RUN: $*"

  # Run command in background and show spinner
  if [[ -t 1 ]] && [[ -z "${QUIET:-}" ]]; then
    "$@" > /tmp/run_with_progress.$$.out 2>&1 &
    local cmd_pid=$!
    spinner $cmd_pid "$message"
    local exit_code=$?

    # Show output if command failed
    if [[ $exit_code -ne 0 ]]; then
      cat /tmp/run_with_progress.$$.out
    fi
    rm -f /tmp/run_with_progress.$$.out

    return $exit_code
  else
    # No spinner in non-interactive or quiet mode
    "$@"
  fi
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    error "This script supports macOS only."
    error "Detected OS: $(uname -s)"
    error ""
    error "Try this instead:"
    error "  - For Linux: Use apt/dnf/pacman package managers"
    error "  - For Windows: Use WSL2 or native Windows tools"
    die ""
  fi
}

refuse_root() {
  # Allow execution from daemon (set MAC_MAINTENANCE_DAEMON=1)
  if [[ ${EUID} -eq 0 ]] && [[ -z "${MAC_MAINTENANCE_DAEMON:-}" ]]; then
    error "Do not run as root. Use a normal user; script will sudo when needed."
    error ""
    error "Try this instead:"
    error "  1. Exit the root shell: exit"
    error "  2. Run as your normal user: ./upkeep.sh [options]"
    error ""
    error "Why? Running as root can cause permission issues and is a security risk."
    die "The script will request sudo when needed for specific operations."
  fi
}

check_minimum_space() {
  # Ensure minimum free disk space before running operations
  # Require ~100MB minimum to safely create logs and perform operations
  local free_kb
  free_kb=$(df -Pk / 2>/dev/null | awk 'NR==2{print $4+0}')

  # Validate we got a number
  if ! [[ "$free_kb" =~ ^[0-9]+$ ]]; then
    warning "Could not determine free disk space"
    return 0  # Continue anyway (fail open)
  fi

  local min_kb=102400  # 100MB minimum
  if (( free_kb < min_kb )); then
    local free_mb=$(( free_kb / 1024 ))
    error "Insufficient disk space: ${free_mb}MB free (need ~100MB minimum)"
    error ""
    error "Maintenance operations need temporary space for:"
    error "  - Downloading updates"
    error "  - Creating backups"
    error "  - Log rotation"
    error ""
    error "Free up space before running maintenance:"
    error "  1. Empty Trash:          Finder → Empty Trash"
    error "  2. Remove downloads:     ~/Downloads folder"
    error "  3. Clean browser caches: Safari/Chrome settings"
    error "  4. Delete old snapshots: ./upkeep.sh --thin-tm-snapshots"
    error "  5. Check large files:    du -sh ~/* | sort -h"
    error ""
    error "Or use: ./upkeep.sh --space-report  (to find what's using space)"
    die ""
  fi

  return 0
}

version_compare() {
  # Compare two version strings (e.g., "1.9.17" vs "1.9.16")
  # Returns 0 if $1 >= $2, 1 otherwise
  # Usage: version_compare "1.9.17" "1.9.16" && echo "newer or equal"
  local ver1="$1"
  local ver2="$2"

  # Use sort -V (version sort) to compare
  local sorted
  sorted="$(printf '%s\n%s\n' "$ver1" "$ver2" | sort -V | head -n1)"

  [[ "$sorted" == "$ver2" ]]
}

check_sudo_security() {
  # Check for critical sudo vulnerabilities (CVE-2025-32462, CVE-2025-32463)
  # These 12-year-old flaws allow privilege escalation
  # Fixed in sudo 1.9.17p1, included in macOS 26.1+
  local sudo_version
  sudo_version=$(sudo -V 2>/dev/null | head -n1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)

  if [[ -z "$sudo_version" ]]; then
    warning "Could not determine sudo version. Proceed with caution."
    return 0
  fi

  if ! version_compare "$sudo_version" "1.9.17"; then
    error "CRITICAL: sudo version $sudo_version has known privilege escalation vulnerabilities"
    error ""
    error "Vulnerabilities:"
    error "  - CVE-2025-32462: Policy-check flaw with -h/--host option"
    error "  - CVE-2025-32463: Chroot option flaw allowing arbitrary code as root"
    error ""
    error "Current system:"
    error "  macOS version: $(macos_version)"
    error "  sudo version:  $sudo_version (need: 1.9.17 or later)"
    error ""
    error "How to fix:"
    error "  1. Update to macOS 26.1 or later:"
    error "     System Settings → General → Software Update"
    error "  2. Or run: softwareupdate --install --all"
    error "  3. Then run this script again"
    error ""
    error "Learn more:"
    error "  https://www.sudo.ws/security/advisories/"
    die ""
  fi

  success "Sudo version $sudo_version - security checks passed"
}

macos_version() { sw_vers -productVersion 2>/dev/null || echo "unknown"; }
macos_build()   { sw_vers -buildVersion 2>/dev/null || echo "unknown"; }

percent_used_root() {
  # Returns percentage of root filesystem used (0-100)
  # Returns 0 with error message if unable to determine
  local output
  output=$(df -P / 2>/dev/null | awk 'NR==2{gsub("%","",$5); print $5+0}')

  # Validate we got a valid number
  if ! [[ "$output" =~ ^[0-9]+$ ]]; then
    warning "Could not determine disk usage percentage (invalid df output)"
    echo "0"
    return 1
  fi

  # Validate reasonable range (0-100)
  if (( output < 0 || output > 100 )); then
    warning "Disk usage percentage out of range: $output%"
    echo "0"
    return 1
  fi

  echo "$output"
  return 0
}

is_on_ac_power() {
  # pmset -g batt prints "AC Power" or "Battery Power"
  pmset -g batt 2>/dev/null | head -n 1 | grep -q "AC Power"
}

quick_net_check() {
  # Fast + timeouted
  curl -Is --max-time 3 https://cloudflare.com >/dev/null 2>&1
}

detect_apple_silicon() {
  # Multi-layer Apple Silicon detection (Task #110)
  # Business logic: Apple Silicon needs less maintenance than Intel due to:
  # - Unified memory architecture (less swap/cache pressure)
  # - More efficient CPU/GPU integration
  # - Better thermal management
  # Research: Apple Silicon handles cache/memory 30-50% more efficiently

  local arch
  local detected=false

  # Layer 1: Primary detection via uname (works 99% of the time)
  arch=$(uname -m 2>/dev/null)
  if [[ "$arch" == "arm64" ]]; then
    detected=true
  fi

  # Layer 2: Fallback detection via sysctl (handles Rosetta 2)
  # If running under Rosetta, uname reports x86_64 but hardware is arm64
  if [[ "$detected" == "false" ]]; then
    if command_exists sysctl; then
      if sysctl hw.optional.arm64 2>/dev/null | grep -q ": 1"; then
        detected=true
        info "Running under Rosetta 2 detected - using native Apple Silicon settings"
      fi
    fi
  fi

  # Layer 3: Validation - ensure genuine Apple CPU (not Hackintosh/VM edge case)
  if [[ "$detected" == "true" ]]; then
    if command_exists sysctl; then
      local brand
      brand=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "")
      if [[ -n "$brand" ]] && [[ "$brand" != *"Apple"* ]]; then
        info "Non-Apple ARM CPU detected ($brand) - disabling Apple Silicon optimizations"
        detected=false
      fi
    fi
  fi

  # Export results
  if [[ "$detected" == "true" ]]; then
    export APPLE_SILICON=true
    export CPU_ARCH="arm64"
  else
    export APPLE_SILICON=false
    export CPU_ARCH="${arch:-x86_64}"
  fi

  # Log detection (defensive: always know what was detected)
  if [[ "${APPLE_SILICON}" == "true" ]]; then
    success "Detected Apple Silicon (ARM64) - applying optimizations"
  else
    info "Detected Intel CPU (x86_64) - using standard settings"
  fi
}

########################################
# Reporting / Posture
########################################
status_dashboard() {
  # Quick at-a-glance system health dashboard
  section "System Health Dashboard"

  # Get system info
  local macos_ver
  local macos_bld
  macos_ver="$(macos_version)"
  macos_bld="$(macos_build)"

  # Disk usage with visual bar
  local disk_pct
  disk_pct="$(percent_used_root)"
  local disk_free
  disk_free=$(df -h / 2>/dev/null | awk 'NR==2{print $4}')

  # Create visual bar for disk usage
  local bar_width=30
  local filled=$(( disk_pct * bar_width / 100 ))
  local empty=$(( bar_width - filled ))
  local bar=""

  # Color bar based on usage
  local bar_color="$GREEN"
  if (( disk_pct >= 90 )); then
    bar_color="$RED"
  elif (( disk_pct >= 75 )); then
    bar_color="$YELLOW"
  fi

  for ((i=0; i<filled; i++)); do bar+="█"; done
  for ((i=0; i<empty; i++)); do bar+="░"; done

  # Security checks
  local sip_status="Unknown"
  local sip_icon="${WARN}"
  if command_exists csrutil; then
    local sip_output
    sip_output="$(csrutil status 2>/dev/null || echo "unknown")"
    if echo "$sip_output" | grep -qi "enabled"; then
      sip_status="Enabled"
      sip_icon="${OK}"
    elif echo "$sip_output" | grep -qi "disabled"; then
      sip_status="DISABLED"
      sip_icon="${FAIL}"
    fi
  fi

  local fv_status="Unknown"
  local fv_icon="${WARN}"
  if command_exists fdesetup; then
    local fv_output
    fv_output="$(fdesetup status 2>/dev/null || echo "unknown")"
    if echo "$fv_output" | grep -qi "On"; then
      fv_status="On"
      fv_icon="${OK}"
    else
      fv_status="Off"
      fv_icon="${FAIL}"
    fi
  fi

  # Time Machine snapshots
  local tm_count="0"
  if command_exists tmutil; then
    tm_count=$(tmutil listlocalsnapshots / 2>/dev/null | grep -c "com.apple" 2>/dev/null || true)
    [[ -z "$tm_count" || "$tm_count" == "0" ]] && tm_count="0"
  fi

  # Homebrew status
  local brew_status="Not installed"
  local brew_icon="${INFO}"
  if command_exists brew; then
    brew_status="Installed"
    brew_icon="${OK}"
  fi

  # Last maintenance run (check for log files)
  local last_run="Never"
  if [[ -d "${HOME}/Library/Logs/upkeep" ]]; then
    local latest_log
    latest_log=$(ls -t "${HOME}/Library/Logs/upkeep"/upkeep-*.log 2>/dev/null | head -n2 | tail -n1)
    if [[ -n "$latest_log" ]]; then
      local log_date
      log_date=$(basename "$latest_log" | sed 's/upkeep-//;s/\.log//;s/-\([0-9][0-9]\)\([0-9][0-9]\)\([0-9][0-9]\)/T\1:\2:\3/')
      if [[ "$log_date" =~ ^[0-9]{8}T[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        last_run=$(date -j -f "%Y%m%dT%H:%M:%S" "$log_date" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$log_date")
      fi
    fi
  fi

  # Display dashboard
  echo ""
  log "${BOLD}┌─────────────────────────────────────────────────────────┐${NC}"
  log "${BOLD}│  macOS: ${NC}$macos_ver (build $macos_bld)"
  log "${BOLD}├─────────────────────────────────────────────────────────┤${NC}"
  log "${BOLD}│  ${NC}Disk Usage:  ${bar_color}${bar}${NC} ${disk_pct}% (${disk_free} free)"
  log "${BOLD}│  ${NC}Security:"
  log "${BOLD}│    ${NC}${sip_icon} SIP:       ${sip_status}"
  log "${BOLD}│    ${NC}${fv_icon} FileVault: ${fv_status}"
  log "${BOLD}│  ${NC}Maintenance:"
  log "${BOLD}│    ${NC}${brew_icon} Homebrew:  ${brew_status}"
  log "${BOLD}│    ${INFO}  TM Snapshots: ${tm_count}"
  log "${BOLD}│    ${INFO}  Last Run: ${last_run}"
  log "${BOLD}└─────────────────────────────────────────────────────────┘${NC}"
  echo ""

  # Overall health assessment
  local health_score=100
  (( disk_pct >= 90 )) && health_score=$((health_score - 30))
  (( disk_pct >= 75 )) && health_score=$((health_score - 10))
  [[ "$sip_status" == "DISABLED" ]] && health_score=$((health_score - 40))
  [[ "$fv_status" == "Off" ]] && health_score=$((health_score - 20))

  if (( health_score >= 90 )); then
    success "Overall Health: Excellent (${health_score}/100)"
  elif (( health_score >= 70 )); then
    info "Overall Health: Good (${health_score}/100)"
  elif (( health_score >= 50 )); then
    warning "Overall Health: Fair (${health_score}/100) - Consider maintenance"
  else
    error "Overall Health: Poor (${health_score}/100) - Action required!"
  fi

  info "Run './upkeep.sh --all-safe' for safe maintenance"
  info "Run './upkeep.sh --security-audit' for detailed security check"
}

report_system_posture() {
  section "System Posture Report"

  info "macOS version: $(macos_version) (build $(macos_build))"
  info "Hardware:"
  system_profiler SPHardwareDataType 2>/dev/null | sed -n '1,30p' || true

  info "Storage summary:"
  df -h / || true

  info "Security status snapshot:"
  if command_exists fdesetup; then
    info "FileVault: $(fdesetup status 2>/dev/null || echo "unknown")"
  fi
  if command_exists spctl; then
    info "Gatekeeper: $(spctl --status 2>/dev/null || echo "unknown")"
  fi
  if command_exists /usr/libexec/ApplicationFirewall/socketfilterfw; then
    /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | sed 's/^/  /' || true
  fi
  if command_exists csrutil; then
    info "SIP: $(csrutil status 2>/dev/null || echo "unknown")"
  fi

  success "System posture report complete."
}

security_posture_check() {
  # Comprehensive security audit before running maintenance
  # This function checks critical security settings and fails if system is unsafe
  section "Security Posture Check"

  local security_issues=0
  local security_warnings=0

  # 1. Check macOS version (warn if outdated)
  local macos_ver
  macos_ver="$(macos_version)"
  info "macOS version: $macos_ver (build $(macos_build))"

  # Parse version to check if >= 26.1 (has sudo patches)
  local major minor
  major=$(echo "$macos_ver" | cut -d. -f1)
  minor=$(echo "$macos_ver" | cut -d. -f2)

  if [[ "$major" -lt 26 ]] || [[ "$major" -eq 26 && "$minor" -lt 1 ]]; then
    warning "macOS $macos_ver may have unpatched security vulnerabilities"
    warning "Upgrade to macOS 26.1 or later is recommended for sudo patches (CVE-2025-32462/32463)"
    ((security_warnings++))
  else
    success "macOS version is up to date"
  fi

  # 2. System Integrity Protection (CRITICAL - must be enabled)
  if command_exists csrutil; then
    local sip_status
    sip_status="$(csrutil status 2>/dev/null || echo "unknown")"

    if echo "$sip_status" | grep -qi "disabled"; then
      error "System Integrity Protection is DISABLED"
      error "SIP protects critical system files from modification"
      error "Running maintenance on a system with SIP disabled is dangerous"
      error "Enable SIP by booting to Recovery Mode (Cmd+R) and running: csrutil enable"
      ((security_issues++))
    elif echo "$sip_status" | grep -qi "enabled"; then
      success "System Integrity Protection: enabled"
    else
      warning "System Integrity Protection status unknown"
      ((security_warnings++))
    fi
  fi

  # 3. FileVault (encryption - strongly recommended)
  if command_exists fdesetup; then
    local fv_status
    fv_status="$(fdesetup status 2>/dev/null || echo "unknown")"

    if echo "$fv_status" | grep -qi "On"; then
      success "FileVault disk encryption: enabled"
    else
      warning "FileVault is not enabled - disk encryption strongly recommended"
      warning "Enable in: System Settings > Privacy & Security > FileVault"
      ((security_warnings++))
    fi
  fi

  # 4. Gatekeeper (app verification)
  if command_exists spctl; then
    local gk_status
    gk_status="$(spctl --status 2>/dev/null || echo "unknown")"

    if echo "$gk_status" | grep -qi "enabled"; then
      success "Gatekeeper app verification: enabled"
    else
      warning "Gatekeeper is not enabled - malware protection reduced"
      ((security_warnings++))
    fi
  fi

  # 5. Firewall status
  if command_exists /usr/libexec/ApplicationFirewall/socketfilterfw; then
    local fw_status
    fw_status="$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo "unknown")"

    if echo "$fw_status" | grep -qi "enabled"; then
      success "Application Firewall: enabled"
    else
      warning "Application Firewall is not enabled"
      warning "Enable in: System Settings > Network > Firewall"
      ((security_warnings++))
    fi
  fi

  # 6. Sudo version check (already done in check_sudo_security, but report here)
  local sudo_version
  sudo_version=$(sudo -V 2>/dev/null | head -n1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)
  if [[ -n "$sudo_version" ]]; then
    if version_compare "$sudo_version" "1.9.17"; then
      success "sudo version $sudo_version (patched)"
    else
      error "sudo version $sudo_version (vulnerable to CVE-2025-32462/32463)"
      ((security_issues++))
    fi
  fi

  # Summary
  echo ""
  if (( security_issues > 0 )); then
    error "Security check FAILED: $security_issues critical issue(s) found"
    error "Cannot proceed with system maintenance on an insecure system"
    die "Security posture check failed"
  elif (( security_warnings > 0 )); then
    warning "Security check passed with $security_warnings warning(s)"
    warning "Consider addressing these warnings to improve security posture"
    success "Proceeding with maintenance (warnings are non-blocking)"
  else
    success "Security posture check PASSED - all checks OK ✓"
  fi
}

report_big_space_users() {
  section "Disk Usage Hotspots (Top 15)"
  info "This is a quick signal - not a full forensic scan."

  # In dry-run mode, skip actual filesystem scan (can take minutes).
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    info "DRY-RUN: would scan for large directories"
    return 0
  fi

  # Try Python-enhanced analysis first (provides categorization)
  # Use ACTUAL_HOME for user's home, not daemon's HOME (/var/root)
  local home="${ACTUAL_HOME:-$HOME}"
  if [[ "${PYTHON_AVAILABLE:-0}" -eq 1 ]]; then
    info "Using Python storage analyzer for enhanced analysis..."
    if "$PYTHON_CMD" -m upkeep.bridge analyze "${home}" --max-depth 3 2>/dev/null; then
      success "Storage analysis complete (Python-enhanced)."
      return 0
    else
      warning "Python analyzer failed, falling back to du..."
    fi
  fi

  # Fallback: traditional du-based analysis
  [[ -d "$home" ]] || return 0
  info "Largest directories under ${home} (may take a minute)..."
  # -x: stay on one filesystem
  # Note: du flags differ slightly; this works on macOS du.
  du -xhd 3 "$home" 2>/dev/null | sort -hr | head -n 15 || true
  success "Hotspot report complete."
}

########################################
# Preflight Checks
########################################
preflight() {
  section "Preflight"

  # Detect CPU architecture for optimizations (Task #110)
  # Must run early so APPLE_SILICON env var is available for all operations
  detect_apple_silicon

  local used
  used="$(percent_used_root)"
  info "Root filesystem used: ${used}%"

  if (( used >= SPACE_THRESHOLD )); then
    warning "Disk usage is high (>= ${SPACE_THRESHOLD}%). Updates/index rebuilds may fail or feel slow."
    warning "Consider freeing space first (the script can help you find hotspots)."
  else
    success "Disk space check OK."
  fi

  # Safety threshold check (Task #109 - Business Logic Improvement)
  # Checks disk space and provides progressive warnings/confirmations
  # Feature flag: USE_SAFETY_THRESHOLDS (default: true)
  # Business logic: Prevent operations that could fill disk and cause system instability
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds
  fi

  if is_on_ac_power; then
    success "Power: AC Power"
  else
    warning "Power: Battery. For repairs/large updates, plug into AC."
  fi

  if quick_net_check; then
    success "Network: reachable"
  else
    warning "Network: not reachable (some update steps will be skipped/fail)."
  fi

  success "Preflight complete."
}

########################################
# Updates
########################################
list_macos_updates() {
  section "macOS Updates (list)"
  if ! command_exists softwareupdate; then
    warning "softwareupdate not found (unexpected)."
    return 0
  fi
  # List only (safe)
  info "RUN: softwareupdate -l"
  run_with_progress "Checking for macOS updates" softwareupdate -l || true
  success "macOS update listing complete."
}

install_macos_updates() {
  section "macOS Updates (install)"

  # Safety threshold check before installing updates (Task #109)
  # macOS updates can consume significant disk space
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  if ! command_exists softwareupdate; then
    warning "softwareupdate not found (unexpected)."
    return 0
  fi
  if ! confirm "Install all available macOS updates now?"; then
    warning "Skipped installing macOS updates."
    return 0
  fi

  info "RUN (sudo): softwareupdate --install --all --verbose"
  warning "This may take a while and may require a restart..."

  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    warning "DRY-RUN (sudo): softwareupdate --install --all --verbose"
  else
    sudo softwareupdate --install --all --verbose || warning "softwareupdate reported issues."
  fi

  success "macOS updates install pass complete."
}

setup_homebrew_sudo() {
  # 🔧 Feature Flag: USE_NOPASSWD_SUDOERS (easy disable if issues found)
  # Default: true (fixes "sudo: a terminal is required to read the password" error)
  # Set to false to disable this feature
  local USE_NOPASSWD_SUDOERS="${USE_NOPASSWD_SUDOERS:-true}"

  if [[ "$USE_NOPASSWD_SUDOERS" != "true" ]]; then
    info "Homebrew passwordless sudo disabled (USE_NOPASSWD_SUDOERS=false)"
    return 0
  fi

  local sudoers_file="/etc/sudoers.d/upkeep-homebrew"
  local actual_user="${ACTUAL_USER:-${SUDO_USER:-${USER}}}"
  local maintain_sh_path="${MAINTAIN_SH:-$0}"  # Use MAINTAIN_SH env var if set, else current script

  # Business logic: Auto-regenerate if upkeep.sh updated (zero friction for users)
  if [ -f "$sudoers_file" ]; then
    # Check if upkeep.sh is newer than sudoers file (code changes = auto-update)
    if [ "$maintain_sh_path" -nt "$sudoers_file" ]; then
      info "Detected sudoers file is outdated (upkeep.sh updated) - regenerating..."
      run_sudo rm -f "$sudoers_file" || {
        warning "Failed to remove outdated sudoers file - will try to overwrite"
      }
    # File exists - validate it's still correct for current user
    elif grep -q "$actual_user" "$sudoers_file" 2>/dev/null; then
      # Already configured for current user and up-to-date - skip
      return 0
    else
      info "Sudoers file exists but for different user - reconfiguring..."
      run_sudo rm -f "$sudoers_file" || {
        warning "Failed to remove old sudoers file"
        return 1
      }
    fi
  fi

  info "Configuring passwordless sudo for Homebrew cask operations..."
  info "This allows Homebrew casks to install without password prompts"

  # Create sudoers entry (explicit whitelist)
  # Business logic:
  # - Allows ALL brew commands (Homebrew's internal scripts need various permissions)
  # - Only allows specific user (not all users)
  # - Only allows specific Homebrew paths (ARM64 and Intel)
  # - NOPASSWD: no password required for these commands
  # - Security: Homebrew is trusted software, user-specific access only
  local sudoers_content
  sudoers_content=$(cat <<EOF
# Upkeep - Homebrew operations
# Created: $(date +%Y-%m-%d)
# Purpose: Allow Homebrew to run without password prompts
# Security: Only allows Homebrew commands for specific user
# Note: Homebrew internal scripts need various system commands (xargs, rm, cp, etc)
#       so we whitelist all brew commands rather than specific subcommands

# Allow ALL brew commands (ARM64 Homebrew)
$actual_user ALL=(root) NOPASSWD: /opt/homebrew/bin/brew *

# Allow ALL brew commands (Intel Homebrew)
$actual_user ALL=(root) NOPASSWD: /usr/local/bin/brew *
EOF
)

  # Write to temp file first (safer than direct pipe to tee)
  local temp_file="/tmp/upkeep-sudoers-$$.tmp"
  echo "$sudoers_content" > "$temp_file"

  # Validate syntax before installing (critical: invalid sudoers can lock you out)
  if run_sudo visudo -c -f "$temp_file" >/dev/null 2>&1; then
    # Syntax valid - install it
    if run_sudo cp "$temp_file" "$sudoers_file"; then
      run_sudo chmod 0440 "$sudoers_file"  # Strict permissions (sudoers requirement)
      rm -f "$temp_file"
      success "✓ Homebrew passwordless sudo configured"
      info "Homebrew casks will now install without password prompts"
      return 0
    else
      error "Failed to install sudoers file"
      rm -f "$temp_file"
      return 1
    fi
  else
    error "Invalid sudoers syntax - not installing (safety check)"
    error "This is unexpected - please report this issue"
    rm -f "$temp_file"
    # Disable feature flag for this run (fallback)
    USE_NOPASSWD_SUDOERS=false
    return 1
  fi
}

fix_homebrew_ownership() {
  # 🔧 Feature Flag: FIX_HOMEBREW_OWNERSHIP (easy disable if issues found)
  # Default: true (prevents nested sudo issues in cask operations)
  # Set to false to skip ownership fix
  local FIX_HOMEBREW_OWNERSHIP="${FIX_HOMEBREW_OWNERSHIP:-true}"

  if [[ "$FIX_HOMEBREW_OWNERSHIP" != "true" ]]; then
    return 0
  fi

  # Get actual user (not root)
  local actual_user=$(get_actual_user_home)
  actual_user=$(basename "$actual_user")

  # Business logic: Fix Homebrew directory ownership to avoid nested sudo
  #
  # Problem: When brew runs as user, it internally calls sudo for cask uninstall
  # This nested sudo fails because our NOPASSWD only covers outer sudo
  #
  # Solution: Give user ownership of Homebrew Caskroom directories
  # Then cask operations don't need sudo at all
  #
  # This is the recommended approach per Homebrew maintainers
  # Source: https://docs.brew.sh/FAQ

  # Detect Homebrew Caskroom paths
  local caskroom_paths=()
  [ -d "/opt/homebrew/Caskroom" ] && caskroom_paths+=("/opt/homebrew/Caskroom")
  [ -d "/usr/local/Caskroom" ] && caskroom_paths+=("/usr/local/Caskroom")

  if [ ${#caskroom_paths[@]} -eq 0 ]; then
    # No Caskroom directories found - nothing to fix
    return 0
  fi

  # Check if ownership fix is needed
  local needs_fix=false
  for caskroom in "${caskroom_paths[@]}"; do
    local current_owner=$(stat -f '%Su' "$caskroom" 2>/dev/null || echo "unknown")
    if [ "$current_owner" != "$actual_user" ]; then
      needs_fix=true
      break
    fi
  done

  if [ "$needs_fix" = false ]; then
    # Already owned by user - silent success (idempotent)
    return 0
  fi

  # One-time configuration message (only shown when fix is needed)
  info "Fixing Homebrew Caskroom ownership to avoid sudo prompts..."
  info "This prevents nested sudo issues during cask operations"

  # Fix ownership for each Caskroom path
  local fix_success=true
  for caskroom in "${caskroom_paths[@]}"; do
    if run_sudo chown -R "$actual_user:admin" "$caskroom" 2>/dev/null; then
      success "✓ Fixed ownership: $caskroom"
    else
      warning "⚠️  Could not fix ownership: $caskroom"
      fix_success=false
    fi
  done

  if [ "$fix_success" = true ]; then
    success "✓ Homebrew Caskroom ownership fixed"
    info "Cask operations will now run without nested sudo issues"
    return 0
  else
    warning "⚠️  Ownership fix had issues - will use fallback method"
    # Disable feature flag for this run (fallback will be used)
    FIX_HOMEBREW_OWNERSHIP=false
    return 1
  fi
}

setup_mas_sudo() {
  # 🔧 Feature Flag: USE_NOPASSWD_SUDOERS_MAS (easy disable if issues found)
  # Default: true (prevents sudo password prompts in daemon context)
  # Set to false to skip mas sudoers configuration
  local USE_NOPASSWD_SUDOERS_MAS="${USE_NOPASSWD_SUDOERS_MAS:-true}"

  if [[ "$USE_NOPASSWD_SUDOERS_MAS" != "true" ]]; then
    return 0
  fi

  # Get actual user (not root)
  local actual_user=$(get_actual_user_home)
  actual_user=$(basename "$actual_user")

  # Check if sudoers file needs updating (auto-regenerate if upkeep.sh changed)
  # Business logic: If upkeep.sh is newer than sudoers file, regenerate automatically
  # This ensures sudoers always matches current code (zero friction for users)
  local sudoers_file="/etc/sudoers.d/upkeep-mas"
  local maintain_sh_path="${MAINTAIN_SH:-$0}"  # Use MAINTAIN_SH env var if set, else current script

  if [ -f "$sudoers_file" ]; then
    # Check if upkeep.sh is newer than sudoers file
    if [ "$maintain_sh_path" -nt "$sudoers_file" ]; then
      info "Detected sudoers file is outdated (upkeep.sh updated) - regenerating..."
      run_sudo rm -f "$sudoers_file" || {
        warning "Failed to remove outdated sudoers file - will try to overwrite"
      }
    else
      # Already configured and up-to-date - silent success (don't spam logs)
      return 0
    fi
  fi

  # One-time configuration message (only shown on first run)
  info "Configuring passwordless sudo for mas operations..."
  info "This prevents 'terminal required' errors when updating App Store apps"

  # Business logic: mas must run as actual user for GUI session access
  # When daemon (root) uses sudo to run mas as user, it needs NOPASSWD entry
  # This is enterprise-standard practice for automation
  #
  # SETENV tag: Allows environment variables to pass through sudo
  # Why: mas CLI uses env vars like MAS_NO_AUTO_INDEX for configuration
  # Without SETENV: sudo blocks env vars with "not allowed to set environment variables"
  # With SETENV: env vars pass through safely (enterprise-standard for CLI tools)

  # Detect mas paths (both ARM64 and Intel locations)
  local mas_paths=()
  [ -x "/opt/homebrew/bin/mas" ] && mas_paths+=("/opt/homebrew/bin/mas")
  [ -x "/usr/local/bin/mas" ] && mas_paths+=("/usr/local/bin/mas")

  if [ ${#mas_paths[@]} -eq 0 ]; then
    info "mas not found - skipping sudoers configuration"
    return 0
  fi

  # Create sudoers entry with explicit command whitelist
  local sudoers_content=$(cat <<EOF
# Upkeep - mas CLI passwordless sudo
# Created: $(date '+%Y-%m-%d %H:%M:%S')
# Purpose: Allow mas operations in daemon context without password prompts
# Security: Only allows mas commands for specific user
# SETENV: Allows environment variables (mas uses MAS_NO_AUTO_INDEX, etc.)
EOF
)

  # Add entries for each detected mas path
  # SETENV tag allows environment variables to pass through sudo (required for mas)
  for mas_path in "${mas_paths[@]}"; do
    sudoers_content+="
$actual_user ALL=(root) NOPASSWD: SETENV: $mas_path *"
  done

  # Write to temp file first (safer than direct pipe to tee)
  local temp_file="/tmp/upkeep-mas-sudoers-$$.tmp"
  echo "$sudoers_content" > "$temp_file"

  # Validate syntax before installing (critical: invalid sudoers can lock you out)
  if run_sudo visudo -c -f "$temp_file" >/dev/null 2>&1; then
    # Syntax valid - install it
    if run_sudo cp "$temp_file" "$sudoers_file"; then
      run_sudo chmod 0440 "$sudoers_file"  # Strict permissions (sudoers requirement)
      rm -f "$temp_file"
      success "✓ mas passwordless sudo configured"
      info "App Store updates will now run without password prompts"
      return 0
    else
      error "Failed to install mas sudoers file"
      rm -f "$temp_file"
      return 1
    fi
  else
    error "Invalid mas sudoers syntax - not installing (safety check)"
    error "This is unexpected - please report this issue"
    rm -f "$temp_file"
    # Disable feature flag for this run (fallback)
    USE_NOPASSWD_SUDOERS_MAS=false
    return 1
  fi
}

brew_maintenance() {
  section "Homebrew"

  # Intelligent Homebrew detection
  if ! detect_homebrew; then
    warning "⚠️  Homebrew not found."

    # Offer opt-in auto-install when interactive. In non-interactive contexts (daemon/launchd),
    # show the command instead of hanging on prompts.
    if [[ -t 0 ]] && [[ -z "${MAC_MAINTENANCE_DAEMON:-}" ]]; then
      if confirm "Install Homebrew now?"; then
        if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
          warning "DRY-RUN: skipping Homebrew install"
          return 0
        fi
        run_with_progress "Installing Homebrew" /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
          warning "Homebrew install failed; skipping Homebrew operations"
          return 0
        }
        # Re-detect after install
        detect_homebrew || {
          warning "Homebrew install completed but brew not found in PATH; skipping"
          return 0
        }
      else
        warning "Skipped Homebrew installation"
        info "To install Homebrew manually:"
        info "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        info "Or visit: https://brew.sh"
        return 0
      fi
    else
      warning "Non-interactive mode: cannot auto-install Homebrew"
      info "To install Homebrew manually:"
      info "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
      info "Or visit: https://brew.sh"
      return 0
    fi
  fi

  # Use detected brew command
  local brew="${BREW_CMD}"
  info "✓ Using Homebrew: $brew"

  # Setup passwordless sudo for Homebrew cask operations (Task #113 fix)
  # This allows casks to run sudo in post-install scripts without password prompts
  # Critical for casks like gstreamer that need system-level permissions
  setup_homebrew_sudo

  # Fix Homebrew Caskroom ownership to avoid nested sudo issues
  # This prevents "sudo: a terminal is required" errors during cask uninstall
  # If ownership fix fails, we'll use HOMEBREW_ALLOW_UNSAFE as fallback
  if ! fix_homebrew_ownership; then
    # Ownership fix failed - use fallback method
    warning "⚠️  Using HOMEBREW_ALLOW_UNSAFE fallback (ownership fix failed)"
    export HOMEBREW_ALLOW_UNSAFE=1
    # Note: This allows Homebrew to run as root (against their security model)
    # But necessary when ownership cannot be fixed
  fi

  # Run all brew commands as actual user (not root)
  # Homebrew 2024+ refuses to run as root for security reasons (unless HOMEBREW_ALLOW_UNSAFE=1)
  # run_as_user helper automatically uses sudo -u when running as root
  #
  # If ownership was fixed: brew runs as user, no sudo needed for cask operations
  # If ownership fix failed: HOMEBREW_ALLOW_UNSAFE allows running as root
  run_with_progress "Updating Homebrew" run_as_user "$brew" update || warning "brew update reported issues."
  run_with_progress "Upgrading Homebrew packages" run_as_user "$brew" upgrade || warning "brew upgrade reported issues."

  # Cleanup may show permission warnings but still succeed in freeing space
  # Capture output to detect partial success
  local cleanup_output
  cleanup_output=$(run_as_user "$brew" cleanup 2>&1 || true)

  # Check if any space was freed (indicates partial/full success)
  if echo "$cleanup_output" | grep -q "freed approximately"; then
    # Extract freed space amount
    local freed=$(echo "$cleanup_output" | grep -o "freed approximately [^.]*" | head -1)
    info "Homebrew cleanup: $freed"
    # Show permission warnings as info, not errors
    if echo "$cleanup_output" | grep -q "Permission denied\|Could not cleanup"; then
      info "Note: Some files required elevated permissions (non-critical)"
    fi
  else
    # No space freed or cleanup had issues - just run silently
    run_as_user "$brew" cleanup >/dev/null 2>&1 || true
  fi

  # Doctor is helpful but noisy; parse for actionable warnings
  info "brew doctor (summary):"
  local doctor_output
  doctor_output=$(run_as_user "$brew" doctor 2>&1 || true)

  # Check for deprecated/disabled packages
  if echo "$doctor_output" | grep -q "deprecated or disabled"; then
    warning "⚠️  Deprecated packages detected:"

    # Extract deprecated casks
    local deprecated_casks
    deprecated_casks=$(echo "$doctor_output" | sed -n '/deprecated or disabled/,/^$/p' | grep -E '^\s+[a-z]' | sed 's/^[[:space:]]*//' || true)

    if [ -n "$deprecated_casks" ]; then
      echo "$deprecated_casks" | while IFS= read -r cask; do
        [ -n "$cask" ] && info "  - $cask"
      done

      info ""
      info "These packages will stop working soon. Consider:"
      info "  1. Find replacements: brew search <package-name>"
      info "  2. Remove if unused: brew uninstall --cask <package-name>"
      info "  3. Check alternatives: https://formulae.brew.sh"
    fi
  fi

  # Check for PATH issues and offer auto-fix
  if echo "$doctor_output" | grep -q "Homebrew's.*was not found in your PATH"; then
    warning "⚠️  Homebrew PATH issue detected"

    # Extract which path is missing (sbin, bin, etc.)
    local missing_path
    missing_path=$(echo "$doctor_output" | grep -o '"/[^"]*"' | tr -d '"' | head -1)
    # Homebrew sometimes prints suggestions like /opt/homebrew/sbin:$PATH. Keep only the real prefix.
    missing_path=${missing_path%%:\$PATH}

    if [ -n "$missing_path" ]; then
      info "Missing from PATH: $missing_path"

      if confirm "Add $missing_path to your shell profile automatically?"; then
        # Detect user's shell
        local actual_user=$(get_actual_user_home)
        local user_shell="${SHELL:-/bin/bash}"
        local profile_file

        # Determine correct profile file
        if echo "$user_shell" | grep -q "zsh"; then
          # Prefer .zprofile for PATH changes so login shells are correct and we avoid repeated edits in .zshrc
          profile_file="$(get_actual_user_home)/.zprofile"
        elif echo "$user_shell" | grep -q "bash"; then
          profile_file="$(get_actual_user_home)/.bash_profile"
        else
          # Last resort only; avoid editing .profile unless we truly don't know the user's shell.
          profile_file="$(get_actual_user_home)/.profile"
        fi

        # Add PATH export if not already present
        # Check if we can actually access the file (root can't access user files due to TCC)
        if [ -f "$profile_file" ] && ! cat "$profile_file" >/dev/null 2>&1; then
          warning "Cannot access $profile_file (permission denied)"
          info "To fix manually, add to your shell profile:"
          info "  export PATH=\"$missing_path:\$PATH\""
        elif [ -f "$profile_file" ] && ! grep -q "$missing_path" "$profile_file" 2>/dev/null; then
          echo "" >> "$profile_file" 2>/dev/null || { warning "Cannot write to $profile_file"; return; }
          echo "# Added by Upkeep - $(date +%Y-%m-%d)" >> "$profile_file"
          echo "export PATH=\"$missing_path:\$PATH\"" >> "$profile_file"
          success "✓ Added $missing_path to $profile_file"
          info "Restart your terminal or run: source $profile_file"
        elif [ -f "$profile_file" ]; then
          info "PATH already configured in $profile_file"
        else
          info "Creating $profile_file..."
          echo "# Upkeep - $(date +%Y-%m-%d)" > "$profile_file" 2>/dev/null || { warning "Cannot create $profile_file"; return; }
          echo "export PATH=\"$missing_path:\$PATH\"" >> "$profile_file"
          success "✓ Created $profile_file with PATH configuration"
        fi
      else
        info "To fix manually, add to your shell profile:"
        info "  export PATH=\"$missing_path:\$PATH\""
      fi
    fi
  fi

  # Parse and show smart summary of issues (Task #147: Smart Homebrew warnings)
  local unlinked_count=0
  local missing_count=0
  local deprecated_count=0

  # Count unlinked kegs
  if echo "$doctor_output" | grep -q "unlinked kegs"; then
    unlinked_count=$(echo "$doctor_output" | grep -A 200 "unlinked kegs" | grep -E "^\s+[a-z]" | wc -l | tr -d ' ')
  fi

  # Count missing formulae
  if echo "$doctor_output" | grep -q "deleted or installed manually"; then
    missing_count=$(echo "$doctor_output" | grep -A 50 "deleted or installed manually" | grep -E "^\s+[a-z]" | wc -l | tr -d ' ')
  fi

  # Count deprecated formulae
  if echo "$doctor_output" | grep -q "deprecated or disabled"; then
    deprecated_count=$(echo "$doctor_output" | grep -A 50 "deprecated or disabled" | grep -E "^\s+[a-z@]" | wc -l | tr -d ' ')
  fi

  # Show smart summary
  echo ""
  info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  info "📊 Homebrew Health Summary"
  info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ $unlinked_count -gt 0 || $missing_count -gt 0 || $deprecated_count -gt 0 ]]; then
    if [[ $deprecated_count -gt 0 ]]; then
      warning "  ⚠️  $deprecated_count deprecated package(s)"
      info "      These will stop working soon"
    fi

    if [[ $missing_count -gt 0 ]]; then
      info "  ℹ️  $missing_count manually installed package(s)"
      info "      These were deleted or installed outside Homebrew"
    fi

    if [[ $unlinked_count -gt 0 ]]; then
      warning "  ⚠️  $unlinked_count unlinked package(s)"
      info "      These aren't accessible via PATH"
    fi

    echo ""
    info "💡 Quick Fix Commands:"
    echo ""

    if [[ $unlinked_count -gt 0 ]]; then
      info "  # Link all packages:"
      echo "  brew list --formula | xargs -n1 brew link 2>/dev/null"
      echo ""
    fi

    if [[ $deprecated_count -gt 0 || $missing_count -gt 0 ]]; then
      info "  # Remove old versions and unused dependencies:"
      echo "  brew cleanup && brew autoremove"
      echo ""
    fi

    info "  # See full details:"
    echo "  brew doctor"
    echo ""
  else
    success "  ✅ No issues found - Homebrew is healthy!"
  fi

  info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # For debugging, show full doctor output only if there are warnings
  if echo "$doctor_output" | grep -q "Warning"; then
    info ""
    info "Full brew doctor output (for reference):"
    echo "$doctor_output"
  fi

  success "Homebrew maintenance complete."
}

brew_cleanup() {
  section "Homebrew Cleanup"

  if ! detect_homebrew; then
    warning "Homebrew not found - skipping cleanup"
    return 0
  fi

  local brew="${BREW_CMD}"
  info "✓ Using Homebrew: $brew"

  info "This will:"
  info "  • Remove old versions of packages (brew cleanup)"
  info "  • Remove unused dependencies (brew autoremove)"
  info "  • Link all unlinked packages (brew link)"
  echo ""

  if ! confirm "Run Homebrew cleanup?"; then
    warning "Skipped Homebrew cleanup."
    return 0
  fi

  # 1. Cleanup old versions
  info "Removing old package versions..."
  if run_as_user "$brew" cleanup 2>&1; then
    success "✓ Old versions removed"
  else
    warning "brew cleanup reported issues (non-fatal)"
  fi

  # 2. Auto-remove unused dependencies
  info "Removing unused dependencies..."
  if run_as_user "$brew" autoremove 2>&1; then
    success "✓ Unused dependencies removed"
  else
    info "No unused dependencies found"
  fi

  # 3. Link all unlinked packages (Task #147)
  info "Linking unlinked packages..."
  local linked_count=0
  local failed_count=0

  # Get list of all formulae and try to link each one
  local formulae
  formulae=$(run_as_user "$brew" list --formula 2>/dev/null || true)

  if [ -n "$formulae" ]; then
    while IFS= read -r formula; do
      [ -z "$formula" ] && continue

      # Try to link (suppress output, check exit code)
      if run_as_user "$brew" link "$formula" >/dev/null 2>&1; then
        ((linked_count++))
      elif run_as_user "$brew" link --overwrite "$formula" >/dev/null 2>&1; then
        ((linked_count++))
        info "  Linked (overwrite): $formula"
      else
        ((failed_count++))
      fi
    done <<< "$formulae"

    if [[ $linked_count -gt 0 ]]; then
      success "✓ Linked $linked_count package(s)"
    fi

    if [[ $failed_count -gt 0 ]]; then
      info "  Could not link $failed_count package(s) (conflicts/already linked)"
    fi
  else
    info "No formulae found to link"
  fi

  success "Homebrew cleanup complete."
}

# ============================================================================
# Running App Detection (Task #144 - Skip running apps during mas updates)
# ============================================================================

check_app_running() {
  # Check if a macOS application is currently running
  # Args: $1 = app name (e.g., "WhatsApp", "Spark Desktop")
  # Returns: 0 if running, 1 if not running
  local app_name="$1"

  # Method 1: Check using pgrep with app name
  # More reliable than ps aux | grep (avoids matching the grep process itself)
  if pgrep -q -i -f "$app_name"; then
    return 0  # App is running
  fi

  # Method 2: Check common app bundle locations
  # Some apps have different process names than display names
  local app_path="/Applications/${app_name}.app"
  if [[ -d "$app_path" ]]; then
    # Extract bundle identifier if possible
    local bundle_id=$(defaults read "${app_path}/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || echo "")
    if [[ -n "$bundle_id" ]]; then
      # Check if any process has this bundle identifier
      if pgrep -q -f "$bundle_id"; then
        return 0  # App is running
      fi
    fi
  fi

  return 1  # App is not running
}

mas_updates() {
  section "Mac App Store (mas)"

  # Check if mas is already installed
  if ! detect_mas; then
    # mas CLI not installed - attempt to auto-install via Homebrew
    info "📦 mas CLI not found - attempting auto-install..."

    # Detect Homebrew (intelligent detection for ARM/Intel Macs)
    if detect_homebrew; then
      local brew="${BREW_CMD}"
      info "✓ Found Homebrew: $brew"

      if [[ "${ASSUME_YES:-0}" -eq 1 ]]; then
        # Automated mode: auto-install mas via Homebrew
        # Run as actual user (not root) - Homebrew refuses to run as root
        info "Installing mas CLI via Homebrew (one-time setup)..."
        local install_output=$(run_as_user "$brew" install mas 2>&1)
        local install_status=$?

        if [[ $install_status -eq 0 ]]; then
          # Check if mas is installed but not linked
          if echo "$install_output" | grep -q "not linked"; then
            info "mas is installed but not linked - linking now..."
            if run_as_user "$brew" link mas 2>&1; then
              success "✓ mas CLI linked successfully"
            else
              warning "Failed to link mas - trying to force link..."
              run_as_user "$brew" link --overwrite mas 2>&1 || true
            fi
          fi
          success "✓ mas CLI installed successfully"
          export MAS_CMD="mas"
        else
          warning "Failed to install mas CLI. Skipping App Store updates."
          return 0
        fi
      else
        # Interactive mode: prompt user
        if confirm "Install mas CLI now via Homebrew to enable App Store updates?"; then
          info "Installing mas CLI..."
          # Run as actual user (not root) - Homebrew refuses to run as root
          local install_output=$(run_as_user "$brew" install mas 2>&1)
          local install_status=$?

          if [[ $install_status -eq 0 ]]; then
            # Check if mas is installed but not linked
            if echo "$install_output" | grep -q "not linked"; then
              info "mas is installed but not linked - linking now..."
              if run_as_user "$brew" link mas 2>&1; then
                success "✓ mas CLI linked successfully"
              else
                warning "Failed to link mas - trying to force link..."
                run_as_user "$brew" link --overwrite mas 2>&1 || true
              fi
            fi
            success "✓ mas CLI installed successfully"
            export MAS_CMD="mas"
          else
            warning "Failed to install mas CLI. Skipping App Store updates."
            return 0
          fi
        else
          info "Tip: $brew install mas"
          return 0
        fi
      fi
    else
      # Homebrew not available - can't auto-install mas
      warning "⚠️  mas CLI not found and Homebrew not available"
      info "To enable App Store updates:"
      info "  1. Install Homebrew: https://brew.sh"
      info "  2. Install mas: brew install mas"
      return 0
    fi
  fi

  # mas is now available - proceed with updates
  local mas="${MAS_CMD:-mas}"

  # Kill zombie mas processes first (Task #132 fix)
  # mas processes can hang and accumulate over time
  info "Checking for zombie mas processes..."
  local zombie_count=$(pgrep -x mas 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$zombie_count" -gt 0 ]]; then
    warning "Found $zombie_count zombie mas process(es) - cleaning up..."
    if sudo pkill -9 mas 2>/dev/null; then
      success "✓ Killed $zombie_count zombie mas process(es)"
      sleep 1  # Give system time to clean up
    else
      info "No zombies to clean up (or unable to kill)"
    fi
  else
    info "✓ No zombie mas processes found"
  fi

  # Pre-check for updates (Task #132 fix)
  # mas upgrade can take 5-30 minutes with no output - check first if updates exist
  info "Checking for available App Store updates..."
  local outdated_count=0
  if outdated_apps=$($mas outdated 2>&1); then
    outdated_count=$(echo "$outdated_apps" | grep -c "^[0-9]" || echo "0")
    if [[ "$outdated_count" -eq 0 ]]; then
      success "✓ All App Store apps are up to date - no updates needed"
      return 0
    else
      info "Found $outdated_count App Store app(s) with available updates:"
      # In JSON mode, do NOT emit raw text to stdout (breaks JSON parsing).
      if [[ "${OUTPUT_JSON:-0}" -ne 1 ]]; then
        echo "$outdated_apps" | head -5  # Show first 5
        if [[ "$outdated_count" -gt 5 ]]; then
          info "... and $((outdated_count - 5)) more"
        fi
      fi
      warning "⏱️  Installing App Store updates can take 10-20 minutes"
      info "Large apps (Final Cut, Logic Pro, Xcode) may take even longer"
    fi
  else
    warning "Unable to check for updates - proceeding with upgrade attempt"
  fi

  if ! confirm "Install App Store app updates using 'mas upgrade'? (may take 10-20 minutes)"; then
    warning "Skipped mas upgrade."
    return 0
  fi

  # Setup passwordless sudo for mas operations (one-time configuration)
  # This prevents "sudo: a terminal is required to read the password" errors
  # when daemon uses run_as_user to run mas as the actual user
  setup_mas_sudo

  # Task #144: Check for running apps before updating (skip running apps to avoid blocking system dialogs)
  info "Checking which apps are currently running..."

  local -a apps_to_update=()      # Array of "app_id|app_name" strings
  local -a apps_running=()        # Apps that are running (will be skipped)
  local -a apps_updated=()        # Successfully updated apps
  local -a apps_failed=()         # Failed updates

  # Parse outdated apps: format is "123456789 App Name (1.0 -> 2.0)"
  while IFS= read -r line; do
    if [[ -z "$line" ]]; then continue; fi

    # Skip lines that don't start with a number (error messages, warnings, etc.)
    if ! echo "$line" | grep -q "^[0-9]"; then
      # Silently skip non-app lines (like "mas: command not found")
      continue
    fi

    # Extract app ID (first field)
    local app_id=$(echo "$line" | awk '{print $1}')

    # Validate app_id is all digits (sanity check)
    if ! [[ "$app_id" =~ ^[0-9]+$ ]]; then
      # Not a valid app ID, skip this line
      continue
    fi

    # Extract app name (everything between first space and opening parenthesis)
    # Example: "6445813049  Spark Desktop  (3.27.6  -> 3.27.8)" → "Spark Desktop"
    local app_name=$(echo "$line" | sed -E 's/^[0-9]+[[:space:]]+//; s/[[:space:]]+\([^)]+\)[[:space:]]*$//')

    # Clean up extra spaces
    app_name=$(echo "$app_name" | xargs)

    if [[ -z "$app_name" ]]; then
      # No app name found, skip
      continue
    fi

    # Check if app is currently running
    if check_app_running "$app_name"; then
      warning "  ⏭️  $app_name - app is running, will skip"
      apps_running+=("$app_name")
    else
      info "  ✓ $app_name - ready to update"
      apps_to_update+=("${app_id}|${app_name}")
    fi
  done <<< "$outdated_apps"

  # Summary before updating
  local total_updates=${#apps_to_update[@]}
  local total_skipped=${#apps_running[@]}

  if [[ $total_skipped -gt 0 ]]; then
    warning "⏭️  Skipping $total_skipped running app(s): ${apps_running[*]}"
    info "💡 Tip: Close these apps and run 'Update App Store Apps' again to update them"
  fi

  if [[ $total_updates -eq 0 ]]; then
    if [[ $total_skipped -gt 0 ]]; then
      warning "All apps are currently running - nothing to update now"
      info "Close the apps and try again, or use 'mas upgrade' manually"
    else
      success "✓ All App Store apps are up to date"
    fi
    return 0
  fi

  info "Updating $total_updates app(s)..."

  # Update each app individually (allows us to skip running apps)
  for app_entry in "${apps_to_update[@]}"; do
    local app_id="${app_entry%%|*}"
    local app_name="${app_entry##*|}"

    info "Updating $app_name (ID: $app_id)..."

    # Run mas install for this specific app
    # Use run_as_user to avoid "Failed to get sudo uid" error
    if run_as_user "$mas" install "$app_id" 2>&1; then
      success "  ✅ Updated $app_name"
      apps_updated+=("$app_name")
    else
      warning "  ❌ Failed to update $app_name"
      apps_failed+=("$app_name")
    fi
  done

  # Final summary
  echo ""
  section "App Store Update Summary"

  if [[ ${#apps_updated[@]} -gt 0 ]]; then
    success "✅ Successfully Updated (${#apps_updated[@]}):"
    for app in "${apps_updated[@]}"; do
      print_human "  • $app"
    done
  fi

  if [[ ${#apps_running[@]} -gt 0 ]]; then
    print_human ""
    warning "⏭️  Skipped - App Running (${#apps_running[@]}):"
    for app in "${apps_running[@]}"; do
      print_human "  • $app"
    done
    print_human ""
    info "💡 To update skipped apps:"
    info "   1. Close the apps listed above"
    info "   2. Run 'Update App Store Apps' again"
    info "   3. Or run: mas upgrade"
  fi

  if [[ ${#apps_failed[@]} -gt 0 ]]; then
    print_human ""
    warning "❌ Failed Updates (${#apps_failed[@]}):"
    for app in "${apps_failed[@]}"; do
      print_human "  • $app"
    done
  fi

  # Overall success if at least one app was updated
  if [[ ${#apps_updated[@]} -gt 0 ]]; then
    success "App Store updates complete."
  elif [[ ${#apps_running[@]} -gt 0 && ${#apps_failed[@]} -eq 0 ]]; then
    info "No apps were updated (all were running). Close apps and try again."
  else
    warning "App Store update process completed with issues."
  fi
}

########################################
# Disk / Filesystem health
########################################
verify_root_volume() {
  section "Disk Verification"
  if ! command_exists diskutil; then
    warning "diskutil not found (unexpected)."
    return 0
  fi
  info "Verifying root volume (/)..."
  run diskutil verifyVolume / || warning "diskutil verifyVolume reported issues."
  success "Disk verification complete."
}

smart_status() {
  section "SMART Status"
  if ! command_exists diskutil; then return 0; fi
  # Best-effort: many Apple Silicon internal NVMe don’t expose SMART in the same way.
  local rootdisk
  rootdisk="$(diskutil info / 2>/dev/null | awk -F': ' '/Device Node/ {print $2}' | head -n1 || true)"
  if [[ -z "$rootdisk" ]]; then
    warning "Could not determine root device node."
    return 0
  fi
  info "Root device node: $rootdisk"
  diskutil info "$rootdisk" 2>/dev/null | awk '/SMART/ {print "  " $0}' || true
  success "SMART check complete (best-effort)."
}

repair_root_volume() {
  section "Disk Repair"
  if ! command_exists diskutil; then return 0; fi
  if ! confirm "Attempt repair of root volume? (This may take time)"; then
    warning "Skipped repair."
    return 0
  fi

  # Run repair and capture output
  local repair_output
  repair_output=$(run_sudo diskutil repairVolume / 2>&1) || true

  # Check for expected "Unable to unmount" error (boot volume limitation)
  if echo "$repair_output" | grep -q "Unable to unmount.*(-69673)"; then
    info "ℹ️  Cannot repair boot volume while system is running (expected behavior)"
    info "ℹ️  To repair boot volume: Restart → Recovery Mode (⌘R) → Disk Utility → First Aid"
    success "Disk check complete (repair skipped for boot volume)"
  elif echo "$repair_output" | grep -qi "error\|fail\|issue"; then
    echo "$repair_output"
    warning "diskutil repairVolume reported issues."
    success "Disk repair pass complete."
  else
    echo "$repair_output"
    success "Disk repair pass complete."
  fi
}

########################################
# Time Machine snapshots (APFS locals)
########################################
list_tm_localsnapshots() {
  section "Time Machine Local Snapshots"
  if ! command_exists tmutil; then
    warning "tmutil not found."
    return 0
  fi
  tmutil listlocalsnapshots / || true
  success "Listed local snapshots."
}

thin_tm_localsnapshots() {
  section "Thin Time Machine Local Snapshots"

  # Safety threshold check before thinning snapshots (Task #109)
  # Thinning snapshots frees space, but we should warn if disk is critically full
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  if ! command_exists tmutil; then return 0; fi

  # Check if any snapshots exist before attempting to thin
  local snapshot_count
  snapshot_count=$(tmutil listlocalsnapshots / 2>/dev/null | grep -c "com.apple" 2>/dev/null || echo "0")
  snapshot_count=$(echo "$snapshot_count" | tr -d '\n\r' | head -1)

  if [[ "$snapshot_count" -eq 0 ]]; then
    info "No local snapshots found - nothing to thin."
    return 0
  fi

  local used
  used="$(percent_used_root)"

  # Validate disk usage percentage (percent_used_root returns 0 on error)
  if ! [[ "$used" =~ ^[0-9]+$ ]] || [[ "$used" -eq 0 ]]; then
    warning "Could not determine disk usage - skipping snapshot thinning"
    return 0
  fi

  info "Disk used: ${used}% (thin threshold is ${TM_THIN_THRESHOLD}%)"
  info "Found $snapshot_count local snapshot(s)"

  if (( used < TM_THIN_THRESHOLD )); then
    info "Disk pressure below threshold - not thinning snapshots."
    return 0
  fi

  warning "Thinning snapshots can free space, but it may reduce rollback options."
  if ! confirm "Proceed to thin local snapshots (best-effort)?"; then
    warning "Skipped thinning snapshots."
    return 0
  fi

  # Thin by bytes and urgency; this is best-effort and may do nothing if macOS decides it shouldn't.
  # 20GB request by default, can be adjusted by TM_THIN_BYTES.
  run_sudo tmutil thinlocalsnapshots / "$TM_THIN_BYTES" 4 || warning "tmutil thinlocalsnapshots reported issues."
  success "Snapshot thinning attempt complete."
}

########################################
# Spotlight / Indexes
########################################
spotlight_status() {
  section "Spotlight Status"
  if ! command_exists mdutil; then
    warning "mdutil not found."
    return 0
  fi
  # Capture output to avoid corrupting JSON mode stdout.
  local status_output
  status_output=$(mdutil -s / 2>&1) || true
  if [[ -n "$status_output" ]]; then
    # Print via info (which respects QUIET/JSON mode).
    info "$status_output"
  fi
  success "Spotlight status checked."
}

spotlight_reindex() {
  section "Spotlight Reindex (heavy)"
  if ! command_exists mdutil; then return 0; fi
  warning "Reindexing can take a long time and cause temporary CPU/disk activity."
  if ! confirm "Proceed to rebuild Spotlight index for / ?"; then
    warning "Skipped Spotlight reindex."
    return 0
  fi
  run_sudo mdutil -E / || warning "mdutil -E reported issues."
  success "Spotlight reindex triggered."
}

########################################
# Housekeeping (DNS flush, browser cache, developer cache, mail optimization)
########################################
run_periodic_scripts() {
  section "Periodic Maintenance Scripts"
  # OBSOLETE in macOS 15 Sequoia - Apple removed periodic command
  # System now uses launchd daemons for automatic maintenance
  warning "⚠️  Periodic scripts removed in macOS 15 Sequoia - operation skipped"
  info "ℹ️  macOS now handles maintenance automatically via launchd"
  return 0
}

clear_browser_caches() {
  section "Clear Browser Caches (Safari, Chrome)"

  # Safety threshold check before clearing caches (Task #109)
  # While this frees space, operations should be aware of current disk state
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  # Use actual user's home directory (not root's when running as daemon)
  local user_home=$(get_actual_user_home)
  local freed=0

  # Safari cache
  if [ -d "$user_home/Library/Caches/com.apple.Safari" ]; then
    local safari_size=$(du -sk "$user_home/Library/Caches/com.apple.Safari" 2>/dev/null | awk '{print $1}')
    if confirm "Clear Safari cache (~$((safari_size / 1024))MB)?"; then
      rm -rf "$user_home/Library/Caches/com.apple.Safari/"* 2>/dev/null
      success "Safari cache cleared"
      freed=$((freed + safari_size))
    fi
  fi

  # Chrome cache
  if [ -d "$user_home/Library/Caches/Google/Chrome" ]; then
    local chrome_size=$(du -sk "$user_home/Library/Caches/Google/Chrome" 2>/dev/null | awk '{print $1}')
    if confirm "Clear Chrome cache (~$((chrome_size / 1024))MB)?"; then
      rm -rf "$user_home/Library/Caches/Google/Chrome/"* 2>/dev/null
      success "Chrome cache cleared"
      freed=$((freed + chrome_size))
    fi
  fi

  if [ $freed -gt 0 ]; then
    success "Freed ~$((freed / 1024))MB from browser caches"
  else
    info "No browser caches found to clear"
  fi
}

clear_developer_caches() {
  section "Clear Developer Caches (Xcode)"

  # Safety threshold check before clearing developer caches (Task #109)
  # Developer caches can be large; operations should be aware of disk state
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  # Use actual user's home directory (not root's when running as daemon)
  local user_home=$(get_actual_user_home)

  if [ ! -d "$user_home/Library/Developer/Xcode" ]; then
    info "Xcode not found - skipping developer cache cleanup"
    return 0
  fi

  local freed=0

  # DerivedData
  if [ -d "$user_home/Library/Developer/Xcode/DerivedData" ]; then
    local derived_size=$(du -sk "$user_home/Library/Developer/Xcode/DerivedData" 2>/dev/null | awk '{print $1}')
    if confirm "Clear Xcode DerivedData (~$((derived_size / 1024))MB)?"; then
      rm -rf "$user_home/Library/Developer/Xcode/DerivedData/"* 2>/dev/null
      success "DerivedData cleared"
      freed=$((freed + derived_size))
    fi
  fi

  # Old simulators
  if command_exists xcrun; then
    if confirm "Delete unavailable iOS Simulators?"; then
      if xcrun simctl delete unavailable 2>/dev/null; then
        success "Old simulators deleted"
      else
        # Exit code 72 (EX_OSFILE) is common when no unavailable simulators exist
        # Don't fail the entire operation for this
        info "No unavailable simulators to delete (or simulators in use)"
      fi
    fi
  fi

  if [ $freed -gt 0 ]; then
    success "Freed ~$((freed / 1024))MB from developer caches"
  fi
}

clear_dev_tools_caches() {
  section "Developer Tools Cache Cleanup"

  # Use actual user's home directory (not root's when running as daemon)
  local user_home=$(get_actual_user_home)
  local freed=0
  local total_size=0

  # npm cache (~/.npm)
  if [ -d "$user_home/.npm" ]; then
    local npm_size=$(du -sk "$user_home/.npm" 2>/dev/null | awk '{print $1}')
    total_size=$((total_size + npm_size))
    info "npm cache: ~$((npm_size / 1024))MB"
    if confirm "Clear npm cache (~$((npm_size / 1024))MB)?"; then
      if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
        success "npm cache cleared (dry-run)"
      elif command_exists npm; then
        npm cache clean --force 2>/dev/null || rm -rf "$user_home/.npm/_cacache" 2>/dev/null
        success "npm cache cleared"
      else
        rm -rf "$user_home/.npm/_cacache" 2>/dev/null
        success "npm cache cleared (manual)"
      fi
      freed=$((freed + npm_size))
    fi
  fi

  # pip cache (~/Library/Caches/pip)
  if [ -d "$user_home/Library/Caches/pip" ]; then
    local pip_size=$(du -sk "$user_home/Library/Caches/pip" 2>/dev/null | awk '{print $1}')
    total_size=$((total_size + pip_size))
    info "pip cache: ~$((pip_size / 1024))MB"
    if confirm "Clear pip cache (~$((pip_size / 1024))MB)?"; then
      if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
        success "pip cache cleared (dry-run)"
      elif command_exists pip3; then
        pip3 cache purge 2>/dev/null || rm -rf "$user_home/Library/Caches/pip" 2>/dev/null
        success "pip cache cleared"
      else
        rm -rf "$user_home/Library/Caches/pip" 2>/dev/null
        success "pip cache cleared (manual)"
      fi
      freed=$((freed + pip_size))
    fi
  fi

  # Go module cache (~/go/pkg/mod/cache)
  if [ -d "$user_home/go/pkg/mod/cache" ]; then
    local go_size=$(du -sk "$user_home/go/pkg/mod/cache" 2>/dev/null | awk '{print $1}')
    total_size=$((total_size + go_size))
    info "Go module cache: ~$((go_size / 1024))MB"
    if confirm "Clear Go module cache (~$((go_size / 1024))MB)?"; then
      if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
        success "Go module cache cleared (dry-run)"
      elif command_exists go; then
        go clean -modcache 2>/dev/null || rm -rf "$user_home/go/pkg/mod/cache" 2>/dev/null
        success "Go module cache cleared"
      else
        rm -rf "$user_home/go/pkg/mod/cache" 2>/dev/null
        success "Go module cache cleared (manual)"
      fi
      freed=$((freed + go_size))
    fi
  fi

  # Cargo/Rust cache (~/.cargo/registry/cache)
  if [ -d "$user_home/.cargo/registry/cache" ]; then
    local cargo_size=$(du -sk "$user_home/.cargo/registry/cache" 2>/dev/null | awk '{print $1}')
    total_size=$((total_size + cargo_size))
    info "Cargo registry cache: ~$((cargo_size / 1024))MB"
    if confirm "Clear Cargo registry cache (~$((cargo_size / 1024))MB)?"; then
      if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
        success "Cargo cache cleared (dry-run)"
      else
        rm -rf "$user_home/.cargo/registry/cache" 2>/dev/null
        success "Cargo cache cleared"
      fi
      freed=$((freed + cargo_size))
    fi
  fi

  # Composer/PHP cache (~/.composer/cache)
  if [ -d "$user_home/.composer/cache" ]; then
    local composer_size=$(du -sk "$user_home/.composer/cache" 2>/dev/null | awk '{print $1}')
    total_size=$((total_size + composer_size))
    info "Composer cache: ~$((composer_size / 1024))MB"
    if confirm "Clear Composer cache (~$((composer_size / 1024))MB)?"; then
      if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
        success "Composer cache cleared (dry-run)"
      elif command_exists composer; then
        composer clear-cache 2>/dev/null || rm -rf "$user_home/.composer/cache" 2>/dev/null
        success "Composer cache cleared"
      else
        rm -rf "$user_home/.composer/cache" 2>/dev/null
        success "Composer cache cleared (manual)"
      fi
      freed=$((freed + composer_size))
    fi
  fi

  if [ $total_size -eq 0 ]; then
    info "No developer tool caches found"
    return 0
  fi

  if [ $freed -gt 0 ]; then
    success "Freed ~$((freed / 1024))MB from developer tool caches"
  fi
}

optimize_mail_database() {
  section "Optimize Mail.app Database"

  # Use actual user's home directory (not root's when running as daemon)
  local user_home=$(get_actual_user_home)
  local mail_data="$user_home/Library/Mail"

  if [ ! -d "$mail_data" ]; then
    info "Mail.app data not found - skipping"
    return 0
  fi

  if ! confirm "Rebuild Mail envelope index? (Mail will rebuild on next launch)"; then
    warning "Skipped Mail optimization"
    return 0
  fi

  # Close Mail if running
  if pgrep -x "Mail" > /dev/null 2>&1; then
    info "Closing Mail.app..."
    osascript -e 'quit app "Mail"' 2>/dev/null || warning "Failed to quit Mail.app - may need manual close"
    sleep 2
  fi

  # Remove envelope index files (Mail rebuilds automatically)
  # Find may return non-zero if no files found - this is OK
  find "$mail_data" -name "Envelope Index*" -delete 2>/dev/null || true

  success "Mail envelope index deleted - Mail will rebuild on next launch"
  info "This may take a few minutes depending on mailbox size"
}

flush_dns() {
  section "DNS Flush"
  warning "Only needed if you have DNS/resolution weirdness."
  if ! confirm "Flush DNS cache now?"; then
    warning "Skipped DNS flush."
    return 0
  fi
  run dscacheutil -flushcache || true
  run_sudo killall -HUP mDNSResponder || true
  success "DNS flush complete."
}

########################################
# Cleanup (guardrailed)
########################################
trim_user_logs() {
  section "Trim User Logs"

  # Safety threshold check before trimming logs (Task #109)
  # While this frees space, operations should be aware of current disk state
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  # Apple Silicon optimization (Task #110)
  # Business logic: Apple Silicon unified memory reduces log pressure by ~30%
  # Increase trim age from 30 → 45 days (less aggressive cleanup needed)
  # Feature flag: USE_APPLE_SILICON_OPTIMIZATIONS (default: true)
  local effective_log_trim_days="${LOG_TRIM_DAYS}"
  if [[ "${APPLE_SILICON:-false}" == "true" ]] && [[ "${USE_APPLE_SILICON_OPTIMIZATIONS:-true}" == "true" ]]; then
    effective_log_trim_days=$((LOG_TRIM_DAYS * 3 / 2))  # 30 → 45 days (50% increase)
    info "Apple Silicon detected: Using ${effective_log_trim_days}-day retention (vs ${LOG_TRIM_DAYS} on Intel)"
  fi

  local path="${HOME}/Library/Logs"
  local expected="${HOME}/Library/Logs"

  [[ -d "$path" ]] || { warning "No logs dir: $path"; return 0; }

  # Security: Validate path resolution to prevent symlink attacks
  validate_safe_path "$path" "$expected" "user logs directory" || return 1

  # File count guardrail (pre-check)
  # Business logic: very large log directories can indicate runaway logging.
  # We surface a warning before doing any deletion work.
  local file_count
  file_count=$(find "$path" -type f -name "*.log" 2>/dev/null | wc -l | tr -d " ")
  local MAX_DELETE_FILES=5000
  if [[ -n "$file_count" ]] && [[ "$file_count" -gt "$MAX_DELETE_FILES" ]]; then
    warning "Log file count exceeds MAX_DELETE_FILES threshold: ${file_count} files in ${path}"
  fi

  # Preview mode: show what would be deleted
  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Files that would be deleted (*.log older than ${effective_log_trim_days} days):"
    local count=0
    while IFS= read -r -d '' file; do
      count=$((count + 1))
      info "  - $file"
    done < <(find "$path" -type f -name "*.log" -mtime +"$effective_log_trim_days" -print0 2>/dev/null)
    if [[ $count -eq 0 ]]; then
      info "  (no files found)"
    else
      info "Total files: $count"
    fi
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: no deletions performed."; return 0; }

  # Get deletion statistics for informed consent (Task #111)
  # Shows user exactly what will be deleted before proceeding
  get_deletion_stats "$path" "$effective_log_trim_days" "*.log"

  # Handle zero files case (early return, no confirmation needed)
  if [[ "$DELETION_FILE_COUNT" == "0" ]] || [[ -z "$DELETION_FILE_COUNT" ]]; then
    info "No log files older than ${effective_log_trim_days} days found. Nothing to delete."
    return 0
  fi

  # Show detailed information to user (enhanced UX - Task #111)
  if [[ -n "$DELETION_SIZE_MB" ]] && [[ "$DELETION_SIZE_MB" -gt 0 ]]; then
    info "Found ${DELETION_FILE_COUNT} log files older than ${effective_log_trim_days} days (total: ${DELETION_SIZE_MB} MB)"
  else
    info "Found ${DELETION_FILE_COUNT} log files older than ${effective_log_trim_days} days"
  fi
  info "Location: $path"

  # High-risk operation warning (>5,000 files or >1GB)
  # Business logic: Large deletions require extra confirmation (DaisyDisk pattern)
  local file_count_numeric="${DELETION_FILE_COUNT//[^0-9]/}"  # Remove "+" suffix
  local needs_typed_confirm=false

  if [[ -n "$file_count_numeric" ]] && [[ $file_count_numeric -gt 5000 ]]; then
    needs_typed_confirm=true
  elif [[ -n "$DELETION_SIZE_MB" ]] && [[ $DELETION_SIZE_MB -gt 1024 ]]; then
    needs_typed_confirm=true
  fi

  if [[ "$needs_typed_confirm" == "true" ]]; then
    warning "⚠️  LARGE DELETION: ${DELETION_FILE_COUNT} files"
    [[ -n "$DELETION_SIZE_MB" ]] && warning "   Total size: ${DELETION_SIZE_MB} MB ($(echo "scale=1; $DELETION_SIZE_MB / 1024" | bc) GB)"
    warning "   Type 'DELETE' to confirm (or anything else to cancel):"
    read -r user_input
    if [[ "$user_input" != "DELETE" ]]; then
      warning "Deletion cancelled."
      return 0
    fi
  else
    # Normal confirmation for smaller operations
    if ! confirm "Proceed deleting ${DELETION_FILE_COUNT} log files?"; then
      warning "Skipped log trimming."
      return 0
    fi
  fi

  find "$path" -type f -name "*.log" -mtime +"$effective_log_trim_days" -delete 2>/dev/null || true
  success "User log trim complete."
}

trim_user_caches() {
  section "Trim User Caches (age-based)"

  # Safety threshold check before trimming caches (Task #109)
  # While this frees space, operations should be aware of current disk state
  if [[ "${USE_SAFETY_THRESHOLDS:-true}" == "true" ]]; then
    check_disk_safety_thresholds || return 1
  fi

  # Apple Silicon optimization (Task #110)
  # Business logic: Unified memory architecture handles cache more efficiently (~30-40%)
  # Increase trim age from 30 → 45 days (less aggressive cleanup needed)
  # Research: Apple Silicon memory management reduces cache pressure significantly
  local effective_cache_trim_days="${CACHE_TRIM_DAYS}"
  if [[ "${APPLE_SILICON:-false}" == "true" ]] && [[ "${USE_APPLE_SILICON_OPTIMIZATIONS:-true}" == "true" ]]; then
    effective_cache_trim_days=$((CACHE_TRIM_DAYS * 3 / 2))  # 30 → 45 days (50% increase)
    info "Apple Silicon detected: Using ${effective_cache_trim_days}-day retention (vs ${CACHE_TRIM_DAYS} on Intel)"
  fi

  local target="${HOME}/Library/Caches"
  local expected="${HOME}/Library/Caches"

  [[ -d "$target" ]] || { warning "No caches dir: $target"; return 0; }

  # Security: Validate path resolution to prevent symlink attacks (replaces string comparison)
  validate_safe_path "$target" "$expected" "user caches directory" || return 1

  # Preview mode: show what would be deleted
  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Cache files that would be deleted (older than ${effective_cache_trim_days} days):"
    local count=0
    while IFS= read -r -d '' file; do
      count=$((count + 1))
      info "  - $file"
      # Limit output to first 50 files in preview
      if [[ $count -ge 50 ]]; then
        info "  ... (showing first 50 files)"
        break
      fi
    done < <(find "$target" -type f -mtime +"$effective_cache_trim_days" -print0 2>/dev/null)
    local total=$(find "$target" -type f -mtime +"$effective_cache_trim_days" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $total -eq 0 ]]; then
      info "  (no files found)"
    else
      info "Total files: $total"
    fi
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: no deletions performed."; return 0; }

  # Get deletion statistics for informed consent (Task #111)
  get_deletion_stats "$target" "$effective_cache_trim_days" "*"

  # Handle zero files case (early return)
  if [[ "$DELETION_FILE_COUNT" == "0" ]] || [[ -z "$DELETION_FILE_COUNT" ]]; then
    info "No cache files older than ${effective_cache_trim_days} days found. Nothing to delete."
    return 0
  fi

  # Show detailed information to user (enhanced UX - Task #111)
  warning "This is NOT a full cache wipe. It trims files older than ${effective_cache_trim_days} days."
  if [[ -n "$DELETION_SIZE_MB" ]] && [[ "$DELETION_SIZE_MB" -gt 0 ]]; then
    info "Found ${DELETION_FILE_COUNT} cache files older than ${effective_cache_trim_days} days (total: ${DELETION_SIZE_MB} MB)"
  else
    info "Found ${DELETION_FILE_COUNT} cache files older than ${effective_cache_trim_days} days"
  fi
  info "Location: $target"

  # High-risk operation warning (>5,000 files or >1GB)
  local file_count_numeric="${DELETION_FILE_COUNT//[^0-9]/}"
  local needs_typed_confirm=false

  if [[ -n "$file_count_numeric" ]] && [[ $file_count_numeric -gt 5000 ]]; then
    needs_typed_confirm=true
  elif [[ -n "$DELETION_SIZE_MB" ]] && [[ $DELETION_SIZE_MB -gt 1024 ]]; then
    needs_typed_confirm=true
  fi

  if [[ "$needs_typed_confirm" == "true" ]]; then
    warning "⚠️  LARGE DELETION: ${DELETION_FILE_COUNT} files"
    [[ -n "$DELETION_SIZE_MB" ]] && warning "   Total size: ${DELETION_SIZE_MB} MB ($(echo "scale=1; $DELETION_SIZE_MB / 1024" | bc) GB)"
    warning "   Type 'DELETE' to confirm (or anything else to cancel):"
    read -r user_input
    if [[ "$user_input" != "DELETE" ]]; then
      warning "Deletion cancelled."
      return 0
    fi
  else
    # Normal confirmation for smaller operations
    if ! confirm "Proceed deleting ${DELETION_FILE_COUNT} cache files?"; then
      warning "Skipped cache trimming."
      return 0
    fi
  fi

  # Delete old cache files; do not recursively delete directories wholesale.
  find "$target" -type f -mtime +"$effective_cache_trim_days" -delete 2>/dev/null || true
  success "User cache trim complete."
}

clear_messages_caches() {
  section "Clear Messages Caches"

  local user_home
  user_home=$(get_actual_user_home)

  local target="${user_home}/Library/Messages/Caches"
  local expected="${user_home}/Library/Messages/Caches"

  [[ -d "$target" ]] || { info "No Messages cache dir found: $target"; return 0; }

  validate_safe_path "$target" "$expected" "Messages caches directory" || return 1

  local size
  size=$(du -sh "$target" 2>/dev/null | awk '{print $1}' || echo "")
  [[ -n "$size" ]] && info "Current size: ${size}" || true

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete: $target"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would rm -rf: $target"; return 0; }

  warning "This deletes Messages cache/preview files. It does NOT delete chat history."
  if ! confirm "Proceed deleting Messages caches?"; then
    warning "Skipped Messages cache cleanup."
    return 0
  fi

  rm -rf "$target" || true
  success "Messages caches cleared."
}

remove_aerial_wallpaper_videos() {
  section "Remove macOS Aerial Wallpaper Videos"

  local user_home
  user_home=$(get_actual_user_home)

  local target="${user_home}/Library/Application Support/com.apple.wallpaper/aerials/videos"
  local expected="${user_home}/Library/Application Support/com.apple.wallpaper/aerials/videos"

  [[ -d "$target" ]] || { info "No Aerial videos dir found: $target"; return 0; }

  validate_safe_path "$target" "$expected" "Aerial wallpaper videos directory" || return 1

  local size
  size=$(du -sh "$target" 2>/dev/null | awk '{print $1}' || echo "")
  [[ -n "$size" ]] && info "Current size: ${size}" || true

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete: $target"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would rm -rf: $target"; return 0; }

  warning "This deletes downloaded Aerial videos. macOS may re-download them later if Aerial wallpapers/screensavers are enabled."
  if ! confirm "Proceed deleting Aerial wallpaper videos?"; then
    warning "Skipped Aerial wallpaper cleanup."
    return 0
  fi

  rm -rf "$target" || true
  success "Aerial wallpaper videos removed."
}

########################################
# Tier 1 Operations (v3.1)
########################################

disk_triage() {
  section "Disk Triage"
  info "Quick overview of disk usage across key directories..."

  local user_home
  user_home=$(get_actual_user_home)

  # Overall disk usage
  info "=== Disk Overview ==="
  df -h / 2>/dev/null || true
  echo ""

  # Top-level home directory breakdown
  info "=== Home Directory (Top 15) ==="
  if [[ -d "$user_home" ]]; then
    du -xhd 1 "$user_home" 2>/dev/null | sort -hr | head -15 || true
  fi
  echo ""

  # Library breakdown (usually the biggest)
  info "=== Library (Top 15) ==="
  if [[ -d "$user_home/Library" ]]; then
    du -xhd 1 "$user_home/Library" 2>/dev/null | sort -hr | head -15 || true
  fi
  echo ""

  # Application Support breakdown
  info "=== Application Support (Top 10) ==="
  if [[ -d "$user_home/Library/Application Support" ]]; then
    du -xhd 1 "$user_home/Library/Application Support" 2>/dev/null | sort -hr | head -10 || true
  fi
  echo ""

  # Caches breakdown
  info "=== Caches (Top 10) ==="
  if [[ -d "$user_home/Library/Caches" ]]; then
    du -xhd 1 "$user_home/Library/Caches" 2>/dev/null | sort -hr | head -10 || true
  fi

  success "Disk triage complete. Use this to identify cleanup targets."
}

ios_backups_report() {
  section "iOS Backups Report"

  local user_home
  user_home=$(get_actual_user_home)
  local backups_dir="${user_home}/Library/Application Support/MobileSync/Backup"

  if [[ ! -d "$backups_dir" ]]; then
    info "No iOS backups found at: $backups_dir"
    info "This is normal if you haven't backed up any iOS devices to this Mac."
    return 0
  fi

  # Get total size
  local total_size
  total_size=$(du -sh "$backups_dir" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "Total iOS Backup Size: ${total_size}"
  echo ""

  # Count number of backups (each subdirectory is a backup)
  local backup_count
  backup_count=$(find "$backups_dir" -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  backup_count=$((backup_count - 1))  # Subtract the parent directory

  if [[ "$backup_count" -eq 0 ]]; then
    info "No device backups found."
    return 0
  fi

  info "Found ${backup_count} device backup(s):"
  echo ""

  # List each backup with details
  for backup_path in "$backups_dir"/*/; do
    [[ -d "$backup_path" ]] || continue

    local backup_size
    backup_size=$(du -sh "$backup_path" 2>/dev/null | awk '{print $1}' || echo "?")

    # Try to get device name from Info.plist
    local device_name="Unknown Device"
    local info_plist="${backup_path}Info.plist"
    if [[ -f "$info_plist" ]]; then
      # Extract device name using plutil (built into macOS)
      device_name=$(plutil -extract "Device Name" raw "$info_plist" 2>/dev/null || echo "Unknown Device")
    fi

    # Get last modified date
    local last_modified
    last_modified=$(stat -f "%Sm" -t "%Y-%m-%d" "$backup_path" 2>/dev/null || echo "unknown")

    printf "  %-30s %8s  (modified: %s)\n" "$device_name" "$backup_size" "$last_modified"
  done

  echo ""
  info "To manage backups: Finder → iPhone → Manage Backups..."
  info "Or: System Settings → General → iPhone & iPad"

  success "iOS backups report complete."
}

application_support_report() {
  section "Application Support Report"

  local user_home
  user_home=$(get_actual_user_home)
  local app_support="${user_home}/Library/Application Support"

  if [[ ! -d "$app_support" ]]; then
    info "No Application Support folder found at: $app_support"
    return 0
  fi

  # Get total size
  local total_size
  total_size=$(du -sh "$app_support" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "Total Application Support Size: ${total_size}"
  echo ""

  info "Top 20 folders by size:"
  echo ""

  # List top 20 folders sorted by size
  du -sh "$app_support"/*/ 2>/dev/null | sort -hr | head -20 | while read -r size folder; do
    local folder_name
    folder_name=$(basename "$folder")
    printf "  %8s  %s\n" "$size" "$folder_name"
  done

  echo ""
  warning "⚠️  DO NOT auto-delete Application Support folders!"
  info "Many contain irreplaceable data: DAW projects, app databases, game saves, etc."
  info "To clean up: Uninstall apps properly or manually review folder contents."

  success "Application Support report complete."
}

dev_artifacts_report() {
  section "Dev Artifacts Report"

  local user_home
  user_home=$(get_actual_user_home)

  info "Scanning for development artifacts in ${user_home}..."
  info "This may take 1-2 minutes on large codebases."
  echo ""

  local total_node_modules=0
  local total_venv=0
  local total_build=0
  local count_node_modules=0
  local count_venv=0
  local count_build=0

  # Find node_modules directories (exclude hidden and common non-project paths)
  info "📦 node_modules directories:"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      local size
      size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
      local parent
      parent=$(dirname "$dir")
      printf "  %8s  %s\n" "$size" "${parent/#$user_home/~}"
      ((count_node_modules++))
    fi
  done < <(find "$user_home" -type d -name "node_modules" -not -path "*/.*" -not -path "*/Library/*" 2>/dev/null | head -20)

  if [[ $count_node_modules -eq 0 ]]; then
    info "  (none found)"
  fi
  echo ""

  # Find Python virtual environments
  info "🐍 Python virtual environments (.venv, venv):"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      local size
      size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
      local parent
      parent=$(dirname "$dir")
      printf "  %8s  %s\n" "$size" "${parent/#$user_home/~}"
      ((count_venv++))
    fi
  done < <(find "$user_home" -type d \( -name ".venv" -o -name "venv" \) -not -path "*/Library/*" 2>/dev/null | head -20)

  if [[ $count_venv -eq 0 ]]; then
    info "  (none found)"
  fi
  echo ""

  # Find build/dist/target directories
  info "🔨 Build artifacts (build, dist, target):"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      local size
      size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
      local parent
      parent=$(dirname "$dir")
      printf "  %8s  %s\n" "$size" "${parent/#$user_home/~}"
      ((count_build++))
    fi
  done < <(find "$user_home" -type d \( -name "build" -o -name "dist" -o -name "target" \) -not -path "*/.*" -not -path "*/Library/*" -not -path "*/node_modules/*" 2>/dev/null | head -20)

  if [[ $count_build -eq 0 ]]; then
    info "  (none found)"
  fi
  echo ""

  info "Summary: ${count_node_modules} node_modules, ${count_venv} venvs, ${count_build} build dirs found"
  info "To clean: Verify project is not active, then delete with 'rm -rf <path>'"

  success "Dev artifacts report complete."
}

downloads_report() {
  section "Downloads Report"

  local user_home
  user_home=$(get_actual_user_home)
  local downloads_dir="${user_home}/Downloads"

  [[ -d "$downloads_dir" ]] || { info "No Downloads folder found: $downloads_dir"; return 0; }

  local total_size
  total_size=$(du -sh "$downloads_dir" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "Total Downloads size: ${total_size}"
  echo ""

  # Show largest files
  info "=== Largest Files (Top 20) ==="
  find "$downloads_dir" -maxdepth 2 -type f -exec du -h {} + 2>/dev/null | sort -hr | head -20 || true
  echo ""

  # Show old installers that could be cleaned
  info "=== Old Installers (>30 days) ==="
  local old_count
  old_count=$(find "$downloads_dir" -maxdepth 1 -type f \( -name "*.dmg" -o -name "*.zip" -o -name "*.pkg" -o -name "*.iso" \) -mtime +30 2>/dev/null | wc -l | tr -d ' ')
  info "Found ${old_count} installer files older than 30 days"

  if [[ "$old_count" -gt 0 ]]; then
    find "$downloads_dir" -maxdepth 1 -type f \( -name "*.dmg" -o -name "*.zip" -o -name "*.pkg" -o -name "*.iso" \) -mtime +30 -exec ls -lh {} \; 2>/dev/null | head -20 || true
  fi

  success "Downloads report complete."
}

downloads_cleanup() {
  section "Clean Downloads"

  local user_home
  user_home=$(get_actual_user_home)
  local downloads_dir="${user_home}/Downloads"

  [[ -d "$downloads_dir" ]] || { info "No Downloads folder found: $downloads_dir"; return 0; }

  # Find old installer files
  local files_to_delete
  files_to_delete=$(find "$downloads_dir" -maxdepth 1 -type f \( -name "*.dmg" -o -name "*.zip" -o -name "*.pkg" -o -name "*.iso" \) -mtime +30 2>/dev/null)

  if [[ -z "$files_to_delete" ]]; then
    info "No old installer files to clean (older than 30 days)."
    return 0
  fi

  local count
  count=$(echo "$files_to_delete" | wc -l | tr -d ' ')
  local total_size
  total_size=$(echo "$files_to_delete" | xargs du -ch 2>/dev/null | tail -1 | awk '{print $1}' || echo "unknown")

  info "Found ${count} installer files (${total_size}) older than 30 days."

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete these files:"
    echo "$files_to_delete" | head -20
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would delete ${count} files"; return 0; }

  warning "This will permanently delete ${count} old installer files (${total_size})."
  if ! confirm "Proceed with cleanup?"; then
    warning "Skipped Downloads cleanup."
    return 0
  fi

  echo "$files_to_delete" | while read -r file; do
    rm -f "$file" 2>/dev/null && info "Deleted: $(basename "$file")" || warning "Failed to delete: $file"
  done

  success "Downloads cleanup complete."
}

xcode_cleanup() {
  section "Xcode Cleanup"

  local user_home
  user_home=$(get_actual_user_home)
  local derived_data="${user_home}/Library/Developer/Xcode/DerivedData"

  [[ -d "$derived_data" ]] || { info "No Xcode DerivedData found: $derived_data"; return 0; }

  local size
  size=$(du -sh "$derived_data" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "DerivedData size: ${size}"

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete: $derived_data/*"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would clear DerivedData"; return 0; }

  info "Clearing Xcode DerivedData (build cache)..."
  rm -rf "${derived_data:?}"/* 2>/dev/null || true

  success "Xcode DerivedData cleared. Next build will be a full rebuild."
}

xcode_device_support_cleanup() {
  section "Xcode Device Support Cleanup"

  local user_home
  user_home=$(get_actual_user_home)

  # Device support paths for iOS, watchOS, tvOS
  local ios_support="${user_home}/Library/Developer/Xcode/iOS DeviceSupport"
  local watchos_support="${user_home}/Library/Developer/Xcode/watchOS DeviceSupport"
  local tvos_support="${user_home}/Library/Developer/Xcode/tvOS DeviceSupport"

  local found_any=0
  local total_size=0

  # Check each device support directory
  for support_dir in "$ios_support" "$watchos_support" "$tvos_support"; do
    if [[ -d "$support_dir" ]]; then
      found_any=1
      local dir_name
      dir_name=$(basename "$support_dir")
      local size
      size=$(du -sh "$support_dir" 2>/dev/null | awk '{print $1}' || echo "0")
      local count
      count=$(find "$support_dir" -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
      count=$((count - 1))  # Subtract the directory itself
      info "${dir_name}: ${size} (${count} device versions)"
    fi
  done

  if [[ "$found_any" -eq 0 ]]; then
    info "No Xcode Device Support folders found. Xcode may not be installed or no devices connected."
    return 0
  fi

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete contents of:"
    [[ -d "$ios_support" ]] && info "  - $ios_support/*"
    [[ -d "$watchos_support" ]] && info "  - $watchos_support/*"
    [[ -d "$tvos_support" ]] && info "  - $tvos_support/*"
    info "Note: Will re-download when you connect a device (2-5 minutes)."
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would clear device support caches"; return 0; }

  info "Clearing Xcode Device Support caches..."

  for support_dir in "$ios_support" "$watchos_support" "$tvos_support"; do
    if [[ -d "$support_dir" ]]; then
      rm -rf "${support_dir:?}"/* 2>/dev/null || true
    fi
  done

  success "Xcode Device Support caches cleared. Will re-download on next device connection."
}

caches_cleanup() {
  section "Clear User Caches"

  local user_home
  user_home=$(get_actual_user_home)
  local caches_dir="${user_home}/Library/Caches"

  [[ -d "$caches_dir" ]] || { info "No Caches folder found: $caches_dir"; return 0; }

  local size
  size=$(du -sh "$caches_dir" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "Caches size: ${size}"

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete contents of: $caches_dir"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would clear caches"; return 0; }

  warning "This will clear all user caches. Apps will rebuild caches as needed."
  if ! confirm "Proceed with cache cleanup?"; then
    warning "Skipped cache cleanup."
    return 0
  fi

  rm -rf "${caches_dir:?}"/* 2>/dev/null || true

  success "User caches cleared."
}

logs_cleanup() {
  section "Clean Old Logs"

  local user_home
  user_home=$(get_actual_user_home)
  local logs_dir="${user_home}/Library/Logs"

  [[ -d "$logs_dir" ]] || { info "No Logs folder found: $logs_dir"; return 0; }

  # Count and size old logs
  local old_logs
  old_logs=$(find "$logs_dir" -type f -mtime +30 2>/dev/null)

  if [[ -z "$old_logs" ]]; then
    info "No logs older than 30 days found."
    return 0
  fi

  local count
  count=$(echo "$old_logs" | wc -l | tr -d ' ')
  local total_size
  total_size=$(echo "$old_logs" | xargs du -ch 2>/dev/null | tail -1 | awk '{print $1}' || echo "unknown")

  info "Found ${count} log files (${total_size}) older than 30 days."

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would delete ${count} old log files"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would delete ${count} old logs"; return 0; }

  # Delete old logs
  find "$logs_dir" -type f -mtime +30 -delete 2>/dev/null || true

  success "Old logs cleaned. Recent logs (< 30 days) preserved."
}

trash_empty() {
  section "Empty Trash"

  local user_home
  user_home=$(get_actual_user_home)
  local trash_dir="${user_home}/.Trash"

  [[ -d "$trash_dir" ]] || { info "Trash folder not found or empty."; return 0; }

  # Check if trash has contents
  local item_count
  item_count=$(find "$trash_dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')

  if [[ "$item_count" -eq 0 ]]; then
    info "Trash is already empty."
    return 0
  fi

  local size
  size=$(du -sh "$trash_dir" 2>/dev/null | awk '{print $1}' || echo "unknown")
  info "Trash contains ${item_count} items (${size})"

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would empty Trash (${item_count} items, ${size})"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would empty Trash"; return 0; }

  warning "This will PERMANENTLY delete all ${item_count} items in Trash. This cannot be undone."
  if ! confirm "Proceed with emptying Trash?"; then
    warning "Skipped Trash emptying."
    return 0
  fi

  rm -rf "${trash_dir:?}"/* 2>/dev/null || true
  rm -rf "${trash_dir:?}"/.[!.]* 2>/dev/null || true  # Hidden files too

  success "Trash emptied."
}

docker_prune() {
  section "Docker Cleanup"

  # Check if Docker is installed
  if ! command -v docker &>/dev/null; then
    info "Docker is not installed. Skipping."
    return 0
  fi

  # Check if Docker daemon is running
  if ! docker info &>/dev/null; then
    warning "Docker daemon is not running. Start Docker Desktop first."
    return 0
  fi

  info "Analyzing Docker disk usage..."

  # Get Docker disk usage summary
  local docker_df
  docker_df=$(docker system df 2>/dev/null) || { warning "Failed to get Docker disk usage."; return 1; }

  echo "$docker_df"
  echo ""

  # Get reclaimable space
  local images_reclaimable build_cache_reclaimable
  images_reclaimable=$(docker system df 2>/dev/null | grep "Images" | awk '{print $NF}' | tr -d '()' || echo "0B")
  build_cache_reclaimable=$(docker system df 2>/dev/null | grep "Build cache" | awk '{print $NF}' | tr -d '()' || echo "0B")

  # Count stopped containers and dangling images
  local stopped_containers dangling_images unused_volumes
  stopped_containers=$(docker ps -aq --filter "status=exited" 2>/dev/null | wc -l | tr -d ' ')
  dangling_images=$(docker images -q --filter "dangling=true" 2>/dev/null | wc -l | tr -d ' ')
  unused_volumes=$(docker volume ls -q --filter "dangling=true" 2>/dev/null | wc -l | tr -d ' ')

  info "Reclaimable: Images (${images_reclaimable}), Build cache (${build_cache_reclaimable})"
  info "Stopped containers: ${stopped_containers}, Dangling images: ${dangling_images}, Unused volumes: ${unused_volumes}"

  if [[ "$stopped_containers" -eq 0 ]] && [[ "$dangling_images" -eq 0 ]] && [[ "$unused_volumes" -eq 0 ]]; then
    info "Docker is already clean. No resources to prune."
    return 0
  fi

  if [[ "${PREVIEW:-0}" -eq 1 ]]; then
    info "PREVIEW: Would prune stopped containers, dangling images, unused networks, and build cache."
    info "  - Stopped containers: ${stopped_containers}"
    info "  - Dangling images: ${dangling_images}"
    info "  - Unused volumes: ${unused_volumes}"
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: would run docker system prune"; return 0; }

  warning "This will remove:"
  warning "  - All stopped containers"
  warning "  - All networks not used by at least one container"
  warning "  - All dangling images"
  warning "  - All dangling build cache"
  echo ""
  warning "Note: Unused volumes are NOT removed by default (use --volumes flag in Docker CLI for that)."

  if ! confirm "Proceed with Docker cleanup?"; then
    warning "Skipped Docker cleanup."
    return 0
  fi

  info "Running docker system prune..."
  docker system prune -f 2>&1 | while read -r line; do
    info "  $line"
  done

  success "Docker cleanup complete."

  # Show updated disk usage
  info "Updated Docker disk usage:"
  docker system df 2>/dev/null || true
}

########################################
# Orchestrators
########################################
run_all_safe() {
  preflight
  security_posture_check
  report_system_posture
  list_macos_updates
  verify_root_volume
  smart_status
  report_big_space_users
  list_tm_localsnapshots
  spotlight_status
  # Light cleanup (opt-in prompts inside)
  trim_user_logs
}

run_all_deep() {
  run_all_safe
  # Deep additions (still opt-in prompts inside)
  thin_tm_localsnapshots
  trim_user_caches
  run_periodic_scripts
  flush_dns
  spotlight_reindex
}

########################################
# CLI
########################################
ASSUME_YES=0
DRY_RUN=0
PREVIEW=0
OUTPUT_JSON=0
QUIET=0

ALL_SAFE=0
ALL_DEEP=0

DO_REPORT=0
DO_PREFLIGHT=0
DO_SECURITY_AUDIT=0
DO_STATUS=0

DO_LIST_MACOS_UPDATES=0
DO_INSTALL_MACOS_UPDATES=0
DO_BREW=0
DO_BREW_CLEANUP=0
DO_MAS=0

DO_VERIFY_DISK=0
DO_REPAIR_DISK=0
DO_SMART=0

DO_BIG_SPACE=0
DO_TM_LIST=0
DO_TM_THIN=0

DO_SPOTLIGHT_STATUS=0
DO_SPOTLIGHT_REINDEX=0

DO_PERIODIC=0  # OBSOLETE in macOS 15 - kept for backward compatibility
DO_BROWSER_CACHE=0
DO_DEV_CACHE=0
DO_DEV_TOOLS_CACHE=0
DO_MAIL_OPTIMIZE=0
DO_DNS_FLUSH=0

DO_TRIM_LOGS=0
DO_TRIM_CACHES=0
DO_MESSAGES_CACHE=0
DO_WALLPAPER_AERIALS=0

# Tier 1 Operations (v3.1)
DO_DISK_TRIAGE=0
DO_IOS_BACKUPS_REPORT=0
DO_APP_SUPPORT_REPORT=0
DO_DEV_ARTIFACTS_REPORT=0
DO_DOWNLOADS_REPORT=0
DO_DOWNLOADS_CLEANUP=0
DO_XCODE_CLEANUP=0
DO_XCODE_DEVICE_SUPPORT=0
DO_CACHES_CLEANUP=0
DO_LOGS_CLEANUP=0
DO_TRASH_EMPTY=0

# Tier 2 Operations
DO_DOCKER_PRUNE=0

SPACE_THRESHOLD=85
TM_THIN_THRESHOLD=88
TM_THIN_BYTES=20000000000  # ~20GB request
LOG_TRIM_DAYS=30
CACHE_TRIM_DAYS=30
MAX_DELETE_FILES=10000  # Maximum files to delete in one operation (safety limit)

usage() {
  cat <<EOF
macOS Tahoe Maintenance Toolkit (safe-by-default)

Usage:
  ./upkeep.sh [options]

Quick presets:
  --all-safe                 Preflight + posture report + updates list + disk verify + space reports + light trim
  --all-deep                 all-safe plus snapshot thinning, cache trim, periodic, DNS flush, Spotlight reindex (guarded)

Common options:
  --assume-yes               Non-interactive (auto-yes where possible; still avoids unsafe defaults)
  --dry-run                  Print what would run, do not change system
  --preview                  Preview mode - show what would be deleted without deleting (for cleanup operations)
  --output-json              Output results in JSON format (for programmatic parsing)
  --quiet, -q                Quiet mode (suppress output except errors, useful for cron)
  --no-emoji                 Disable emoji symbols (use text symbols instead)

Display:
  --status                   Show system health dashboard (disk, updates, security, etc.)

Security:
  --security-audit           Comprehensive security posture check (SIP, FileVault, Gatekeeper, sudo vulnerabilities)

Updates:
  --list-macos-updates
  --install-macos-updates
  --brew
  --mas

Disk:
  --verify-disk
  --repair-disk
  --smart

Storage:
  --space-report
  --list-tm-snapshots
  --thin-tm-snapshots

Spotlight:
  --spotlight-status
  --spotlight-reindex

Housekeeping:
  --periodic
  --flush-dns

Cleanup:
  --trim-logs [days]
  --trim-caches [days]
  --messages-cache           Clear Messages cache/preview files (not chat history)
  --wallpaper-aerials        Delete downloaded macOS Aerial wallpaper videos
  --browser-cache            Clear Safari and Chrome browser caches
  --dev-cache                Clear Xcode DerivedData and simulators
  --dev-tools-cache          Clear npm, pip, Go, Cargo, Composer caches
  --mail-optimize            Rebuild Mail.app envelope index

Tier 1 Operations (v3.1):
  --disk-triage              Quick overview of disk usage across key directories
  --ios-backups-report       Report size and details of iPhone/iPad backups
  --app-support-report       Report top space consumers in Application Support
  --dev-artifacts-report     Find node_modules, .venv, build directories
  --downloads-report         Report size and age of Downloads files
  --downloads-cleanup        Remove old installers/archives from Downloads
  --xcode-cleanup            Clear Xcode DerivedData (not simulators)
  --xcode-device-support     Clear iOS/watchOS/tvOS device support caches
  --caches-cleanup           Clear all user caches (~~/Library/Caches)
  --logs-cleanup             Remove log files older than 30 days
  --trash-empty              Empty the Trash (permanent delete)

Tier 2 Operations:
  --docker-prune             Clean up Docker (stopped containers, dangling images, build cache)

Tuning:
  --space-threshold PCT
  --tm-thin-threshold PCT
  --tm-thin-bytes BYTES

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all-safe) ALL_SAFE=1; shift ;;
    --all-deep) ALL_DEEP=1; shift ;;

    --assume-yes) ASSUME_YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --preview) PREVIEW=1; shift ;;
    --output-json) OUTPUT_JSON=1; QUIET=1; NO_COLOR=1; shift ;;  # JSON mode implies quiet and no color
    --quiet|-q) QUIET=1; shift ;;
    --no-emoji) NO_EMOJI=1; shift ;;

    --status) DO_STATUS=1; shift ;;
    --preflight) DO_PREFLIGHT=1; shift ;;
    --report) DO_REPORT=1; shift ;;
    --security-audit) DO_SECURITY_AUDIT=1; shift ;;
    --list-macos-updates) DO_LIST_MACOS_UPDATES=1; shift ;;
    --install-macos-updates) DO_INSTALL_MACOS_UPDATES=1; shift ;;
    --brew) DO_BREW=1; shift ;;
    --brew-cleanup) DO_BREW_CLEANUP=1; shift ;;
    --mas) DO_MAS=1; shift ;;

    --verify-disk) DO_VERIFY_DISK=1; shift ;;
    --repair-disk) DO_REPAIR_DISK=1; shift ;;
    --smart) DO_SMART=1; shift ;;

    --space-report) DO_BIG_SPACE=1; shift ;;
    --list-tm-snapshots) DO_TM_LIST=1; shift ;;
    --thin-tm-snapshots) DO_TM_THIN=1; shift ;;

    --spotlight-status) DO_SPOTLIGHT_STATUS=1; shift ;;
    --spotlight-reindex) DO_SPOTLIGHT_REINDEX=1; shift ;;

    --periodic) DO_PERIODIC=1; shift ;;
    --flush-dns) DO_DNS_FLUSH=1; shift ;;
    --browser-cache) DO_BROWSER_CACHE=1; shift ;;
    --dev-cache) DO_DEV_CACHE=1; shift ;;
    --dev-tools-cache) DO_DEV_TOOLS_CACHE=1; shift ;;
    --mail-optimize) DO_MAIL_OPTIMIZE=1; shift ;;
    --messages-cache) DO_MESSAGES_CACHE=1; shift ;;
    --wallpaper-aerials) DO_WALLPAPER_AERIALS=1; shift ;;

    # Tier 1 Operations (v3.1)
    --disk-triage) DO_DISK_TRIAGE=1; shift ;;
    --ios-backups-report) DO_IOS_BACKUPS_REPORT=1; shift ;;
    --app-support-report) DO_APP_SUPPORT_REPORT=1; shift ;;
    --dev-artifacts-report) DO_DEV_ARTIFACTS_REPORT=1; shift ;;
    --downloads-report) DO_DOWNLOADS_REPORT=1; shift ;;
    --downloads-cleanup) DO_DOWNLOADS_CLEANUP=1; shift ;;
    --xcode-cleanup) DO_XCODE_CLEANUP=1; shift ;;
    --xcode-device-support) DO_XCODE_DEVICE_SUPPORT=1; shift ;;
    --caches-cleanup) DO_CACHES_CLEANUP=1; shift ;;
    --logs-cleanup) DO_LOGS_CLEANUP=1; shift ;;
    --trash-empty) DO_TRASH_EMPTY=1; shift ;;

    # Tier 2 Operations
    --docker-prune) DO_DOCKER_PRUNE=1; shift ;;

    --trim-logs)
      DO_TRIM_LOGS=1
      if [[ -n "${2:-}" ]]; then
        validate_numeric "$2" "--trim-logs days" 1 3650  # 1 day to 10 years
        LOG_TRIM_DAYS="$2"
        shift 2
      else
        shift
      fi
      ;;
    --trim-caches)
      DO_TRIM_CACHES=1
      if [[ -n "${2:-}" ]]; then
        validate_numeric "$2" "--trim-caches days" 1 3650  # 1 day to 10 years
        CACHE_TRIM_DAYS="$2"
        shift 2
      else
        shift
      fi
      ;;

    --space-threshold)
      validate_numeric "${2:-85}" "--space-threshold" 50 99  # Reasonable disk usage range
      SPACE_THRESHOLD="$2"
      shift 2
      ;;
    --tm-thin-threshold)
      validate_numeric "${2:-88}" "--tm-thin-threshold" 50 99  # Reasonable disk usage range
      TM_THIN_THRESHOLD="$2"
      shift 2
      ;;
    --tm-thin-bytes)
      validate_numeric "${2:-20000000000}" "--tm-thin-bytes" 1000000000 100000000000  # 1GB to 100GB
      TM_THIN_BYTES="$2"
      shift 2
      ;;

    -h|--help) usage; exit 0 ;;
    *) warning "Unknown option: $1"; shift ;;
  esac
done

########################################
# Main
########################################
START_TIME=$(date +%s)

require_macos
refuse_root
check_sudo_security
check_minimum_space

# Check if Python environment is available
PYTHON_AVAILABLE=0
PYTHON_VERSION=""

# Auto-detect local .venv and use it if available
PYTHON_CMD="python3"
if [[ -f ".venv/bin/python" ]]; then
  PYTHON_CMD=".venv/bin/python"
fi

if command_exists "$PYTHON_CMD" || [[ -x "$PYTHON_CMD" ]]; then
  # Try to check Python bridge availability (non-blocking)
  if "$PYTHON_CMD" -m upkeep.bridge check >/dev/null 2>&1; then
    # Parse output safely without eval
    BRIDGE_OUTPUT=$("$PYTHON_CMD" -m upkeep.bridge check 2>/dev/null || echo "")
    if echo "$BRIDGE_OUTPUT" | grep -q "PYTHON_AVAILABLE=1"; then
      PYTHON_AVAILABLE=1
      PYTHON_VERSION=$(echo "$BRIDGE_OUTPUT" | grep "^VERSION=" | cut -d= -f2)
      info "Python features available (v${PYTHON_VERSION})"
    fi
  fi
fi

info "Log file: $LOG_FILE"
info "Dry run: ${DRY_RUN}"
info "Preview: ${PREVIEW}"
info "Assume yes: ${ASSUME_YES}"

# Presets
if (( ALL_DEEP )); then
  run_all_deep
elif (( ALL_SAFE )); then
  run_all_safe
else
  # Explicit modules (only what user asked)
  (( DO_STATUS )) && status_dashboard
  (( DO_PREFLIGHT )) && preflight
  (( DO_REPORT )) && report_system_posture
  (( DO_SECURITY_AUDIT )) && security_posture_check

  (( DO_LIST_MACOS_UPDATES )) && list_macos_updates
  (( DO_INSTALL_MACOS_UPDATES )) && install_macos_updates
  (( DO_BREW )) && brew_maintenance
  (( DO_BREW_CLEANUP )) && brew_cleanup
  (( DO_MAS )) && mas_updates

  (( DO_VERIFY_DISK )) && verify_root_volume
  (( DO_REPAIR_DISK )) && repair_root_volume
  (( DO_SMART )) && smart_status

  (( DO_BIG_SPACE )) && report_big_space_users
  (( DO_TM_LIST )) && list_tm_localsnapshots
  (( DO_TM_THIN )) && thin_tm_localsnapshots

  (( DO_SPOTLIGHT_STATUS )) && spotlight_status
  (( DO_SPOTLIGHT_REINDEX )) && spotlight_reindex

  (( DO_PERIODIC )) && run_periodic_scripts
  (( DO_DNS_FLUSH )) && flush_dns
  (( DO_BROWSER_CACHE )) && clear_browser_caches
  (( DO_DEV_CACHE )) && clear_developer_caches
  (( DO_DEV_TOOLS_CACHE )) && clear_dev_tools_caches
  (( DO_MAIL_OPTIMIZE )) && optimize_mail_database

  (( DO_TRIM_LOGS )) && trim_user_logs
  (( DO_TRIM_CACHES )) && trim_user_caches
  (( DO_MESSAGES_CACHE )) && clear_messages_caches
  (( DO_WALLPAPER_AERIALS )) && remove_aerial_wallpaper_videos

  # Tier 1 Operations (v3.1)
  (( DO_DISK_TRIAGE )) && disk_triage
  (( DO_IOS_BACKUPS_REPORT )) && ios_backups_report
  (( DO_APP_SUPPORT_REPORT )) && application_support_report
  (( DO_DEV_ARTIFACTS_REPORT )) && dev_artifacts_report
  (( DO_DOWNLOADS_REPORT )) && downloads_report
  (( DO_DOWNLOADS_CLEANUP )) && downloads_cleanup
  (( DO_XCODE_CLEANUP )) && xcode_cleanup
  (( DO_XCODE_DEVICE_SUPPORT )) && xcode_device_support_cleanup
  (( DO_CACHES_CLEANUP )) && caches_cleanup
  (( DO_LOGS_CLEANUP )) && logs_cleanup
  (( DO_TRASH_EMPTY )) && trash_empty

  # Tier 2 Operations
  (( DO_DOCKER_PRUNE )) && docker_prune
fi

END_TIME=$(date +%s)
RUNTIME=$(( END_TIME - START_TIME ))

# Output JSON summary if requested
if [[ "${OUTPUT_JSON:-0}" -eq 1 ]]; then
  cat <<EOF
{
  "summary": {
    "runtime_seconds": $RUNTIME,
    "log_file": "$(json_escape "$LOG_FILE")",
    "dry_run": $DRY_RUN,
    "preview": ${PREVIEW:-0},
    "assume_yes": $ASSUME_YES,
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "status": "completed"
  }
}
EOF
fi

success "Done in ${RUNTIME}s. Log: ${LOG_FILE}"
