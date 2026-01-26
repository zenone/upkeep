#!/usr/bin/env bash
# macOS Tahoe Maintenance Toolkit (safe-by-default, OnyX-ish but guardrailed)
#
# Philosophy:
# - Default mode: AUDIT + REPORT (no destructive actions)
# - "Maintenance" that actually matters: updates, disk health, free space, targeted fixes
# - Heavier rebuild/cleanup tasks are opt-in and confirmation-gated
#
# Usage:
#   ./maintain.sh --help
#
# Recommended runs:
#   ./maintain.sh --all-safe
#   ./maintain.sh --all-safe --install-macos-updates
#   ./maintain.sh --all-deep --install-macos-updates
#
# Notes:
# - Do NOT run as root. Script will use sudo only for specific tasks.
# - Works on macOS Tahoe (and should be compatible with recent macOS versions).
#
set -Eeuo pipefail
IFS=$'\n\t'
umask 022

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

LOG_DIR="${HOME}/Library/Logs"
mkdir -p "${LOG_DIR}"
chmod 700 "${LOG_DIR}"  # Restrict directory access to owner only
LOG_FILE="${LOG_DIR}/mac-maintenance-$(date +%Y%m%d-%H%M%S).log"
touch "${LOG_FILE}"
chmod 600 "${LOG_FILE}"  # Restrict log file access to owner only (security: may contain sensitive command output)
exec > >(tee -a "${LOG_FILE}") 2>&1

ts() { date +"%Y-%m-%d %H:%M:%S"; }

log()        { [[ -z "${QUIET:-}" ]] && echo -e "$(ts) $*" || echo -e "$(ts) $*" >> "${LOG_FILE}"; }
log_always() { echo -e "$(ts) $*"; }  # Always output (for errors in quiet mode)

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

  # Verify resolved path matches expected
  if [[ "$resolved" != "$expected" ]]; then
    error "SECURITY: Path resolution mismatch for $description"
    error "  Expected: $expected"
    error "  Got:      $resolved"
    error "  Original: $actual"
    error ""
    error "This could indicate a symlink attack. Refusing to proceed."
    die "Path validation failed"
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
    warning "DRY-RUN: $*"
    return 0
  fi
  info "RUN: $*"
  "$@"
}

run_sudo() {
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    warning "DRY-RUN (sudo): $*"
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
  if [[ ${EUID} -eq 0 ]]; then
    error "Do not run as root. Use a normal user; script will sudo when needed."
    error ""
    error "Try this instead:"
    error "  1. Exit the root shell: exit"
    error "  2. Run as your normal user: ./maintain.sh [options]"
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
    error "  4. Delete old snapshots: ./maintain.sh --thin-tm-snapshots"
    error "  5. Check large files:    du -sh ~/* | sort -h"
    error ""
    error "Or use: ./maintain.sh --space-report  (to find what's using space)"
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
  if [[ -d "${HOME}/Library/Logs" ]]; then
    local latest_log
    latest_log=$(ls -t "${HOME}/Library/Logs"/mac-maintenance-*.log 2>/dev/null | head -n2 | tail -n1)
    if [[ -n "$latest_log" ]]; then
      local log_date
      log_date=$(basename "$latest_log" | sed 's/mac-maintenance-//;s/\.log//;s/-\([0-9][0-9]\)\([0-9][0-9]\)\([0-9][0-9]\)/T\1:\2:\3/')
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

  info "Run './maintain.sh --all-safe' for safe maintenance"
  info "Run './maintain.sh --security-audit' for detailed security check"
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
  # Keep it safe: only scan within $HOME and a few common locations
  local home="${HOME}"
  [[ -d "$home" ]] || return 0
  info "Largest directories under Home (may take a minute)..."
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

  local used
  used="$(percent_used_root)"
  info "Root filesystem used: ${used}%"

  if (( used >= SPACE_THRESHOLD )); then
    warning "Disk usage is high (>= ${SPACE_THRESHOLD}%). Updates/index rebuilds may fail or feel slow."
    warning "Consider freeing space first (the script can help you find hotspots)."
  else
    success "Disk space check OK."
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

brew_maintenance() {
  section "Homebrew"
  if ! command_exists brew; then
    warning "Homebrew not found. Skipping."
    return 0
  fi

  run_with_progress "Updating Homebrew" brew update || warning "brew update reported issues."
  run_with_progress "Upgrading Homebrew packages" brew upgrade || warning "brew upgrade reported issues."
  run_with_progress "Cleaning up Homebrew" brew cleanup || true

  # Doctor is helpful but noisy; keep it as info
  info "brew doctor (summary):"
  brew doctor || true

  success "Homebrew maintenance complete."
}

mas_updates() {
  section "Mac App Store (mas)"
  if ! command_exists mas; then
    warning "mas CLI not found. Skipping App Store updates."
    info "Tip: brew install mas"
    return 0
  fi
  if ! confirm "Install App Store app updates using 'mas upgrade'?"; then
    warning "Skipped mas upgrade."
    return 0
  fi
  run mas upgrade || warning "mas upgrade reported issues."
  success "mas updates complete."
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
  run_sudo diskutil repairVolume / || warning "diskutil repairVolume reported issues."
  success "Disk repair pass complete."
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
  if ! command_exists tmutil; then return 0; fi

  # Check if any snapshots exist before attempting to thin
  local snapshot_count
  snapshot_count=$(tmutil listlocalsnapshots / 2>/dev/null | grep -c "com.apple" || echo "0")

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
  mdutil -s / || true
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
# Housekeeping (periodic, DNS flush)
########################################
run_periodic_scripts() {
  section "Periodic Maintenance Scripts"
  if ! command_exists periodic; then
    warning "periodic not found."
    return 0
  fi
  warning "This is usually unnecessary on modern macOS, but can help in some edge cases."
  if ! confirm "Run: sudo periodic daily weekly monthly ?"; then
    warning "Skipped periodic."
    return 0
  fi
  run_sudo periodic daily weekly monthly || warning "periodic reported issues."
  success "Periodic scripts complete."
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
  local path="${HOME}/Library/Logs"
  local expected="${HOME}/Library/Logs"

  [[ -d "$path" ]] || { warning "No logs dir: $path"; return 0; }

  # Security: Validate path resolution to prevent symlink attacks
  validate_safe_path "$path" "$expected" "user logs directory" || return 1

  info "Deleting *.log older than ${LOG_TRIM_DAYS} days in: $path"
  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: no deletions performed."; return 0; }

  find "$path" -type f -name "*.log" -mtime +"$LOG_TRIM_DAYS" -delete 2>/dev/null || true
  success "User log trim complete."
}

trim_user_caches() {
  section "Trim User Caches (age-based)"
  local target="${HOME}/Library/Caches"
  local expected="${HOME}/Library/Caches"

  [[ -d "$target" ]] || { warning "No caches dir: $target"; return 0; }

  # Security: Validate path resolution to prevent symlink attacks (replaces string comparison)
  validate_safe_path "$target" "$expected" "user caches directory" || return 1

  warning "This is NOT a full cache wipe. It trims files older than ${CACHE_TRIM_DAYS} days."
  if ! confirm "Proceed trimming user cache files older than ${CACHE_TRIM_DAYS} days?"; then
    warning "Skipped cache trimming."
    return 0
  fi

  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: no deletions performed."; return 0; }

  # Delete old cache files; do not recursively delete directories wholesale.
  find "$target" -type f -mtime +"$CACHE_TRIM_DAYS" -delete 2>/dev/null || true
  success "User cache trim complete."
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
DO_MAS=0

DO_VERIFY_DISK=0
DO_REPAIR_DISK=0
DO_SMART=0

DO_BIG_SPACE=0
DO_TM_LIST=0
DO_TM_THIN=0

DO_SPOTLIGHT_STATUS=0
DO_SPOTLIGHT_REINDEX=0

DO_PERIODIC=0
DO_DNS_FLUSH=0

DO_TRIM_LOGS=0
DO_TRIM_CACHES=0

SPACE_THRESHOLD=85
TM_THIN_THRESHOLD=88
TM_THIN_BYTES=20000000000  # ~20GB request
LOG_TRIM_DAYS=30
CACHE_TRIM_DAYS=30

usage() {
  cat <<EOF
macOS Tahoe Maintenance Toolkit (safe-by-default)

Usage:
  ./maintain.sh [options]

Quick presets:
  --all-safe                 Preflight + posture report + updates list + disk verify + space reports + light trim
  --all-deep                 all-safe plus snapshot thinning, cache trim, periodic, DNS flush, Spotlight reindex (guarded)

Common options:
  --assume-yes               Non-interactive (auto-yes where possible; still avoids unsafe defaults)
  --dry-run                  Print what would run, do not change system
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
    --quiet|-q) QUIET=1; shift ;;
    --no-emoji) NO_EMOJI=1; shift ;;

    --status) DO_STATUS=1; shift ;;
    --preflight) DO_PREFLIGHT=1; shift ;;
    --report) DO_REPORT=1; shift ;;
    --security-audit) DO_SECURITY_AUDIT=1; shift ;;
    --list-macos-updates) DO_LIST_MACOS_UPDATES=1; shift ;;
    --install-macos-updates) DO_INSTALL_MACOS_UPDATES=1; shift ;;
    --brew) DO_BREW=1; shift ;;
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

info "Log file: $LOG_FILE"
info "Dry run: ${DRY_RUN}"
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

  (( DO_TRIM_LOGS )) && trim_user_logs
  (( DO_TRIM_CACHES )) && trim_user_caches
fi

END_TIME=$(date +%s)
RUNTIME=$(( END_TIME - START_TIME ))
success "Done in ${RUNTIME}s. Log: ${LOG_FILE}"
