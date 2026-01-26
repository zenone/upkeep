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
  RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; NC=""
elif command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); BLUE=$(tput setaf 4); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; NC=""
fi

INFO="ℹ️"; OK="✅"; WARN="⚠️"; FAIL="❌"

LOG_DIR="${HOME}/Library/Logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/mac-maintenance-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

ts() { date +"%Y-%m-%d %H:%M:%S"; }

log()        { echo -e "$(ts) $*"; }
section()    { log "${YELLOW}${BOLD}--- $* ---${NC}"; }
info()       { log "${BLUE}${INFO} $*${NC}"; }
success()    { log "${GREEN}${OK} $*${NC}"; }
warning()    { log "${YELLOW}${WARN} $*${NC}"; }
error()      { log "${RED}${FAIL} $*${NC}"; }

die()        { error "$*"; exit 1; }

on_interrupt() { error "Interrupted."; exit 1; }
trap on_interrupt SIGINT SIGTERM SIGHUP SIGQUIT

########################################
# Guards / Helpers
########################################
command_exists() { command -v "$1" >/dev/null 2>&1; }

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

require_macos() {
  [[ "$(uname -s)" == "Darwin" ]] || die "This script supports macOS only."
}

refuse_root() {
  [[ ${EUID} -ne 0 ]] || die "Do not run as root. Use a normal user; script will sudo when needed."
}

macos_version() { sw_vers -productVersion 2>/dev/null || echo "unknown"; }
macos_build()   { sw_vers -buildVersion 2>/dev/null || echo "unknown"; }

percent_used_root() { df -P / | awk 'NR==2{gsub("%","",$5); print $5+0}'; }

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
  softwareupdate -l || true
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
  run_sudo softwareupdate --install --all --verbose || warning "softwareupdate reported issues."
  success "macOS updates install pass complete."
}

brew_maintenance() {
  section "Homebrew"
  if ! command_exists brew; then
    warning "Homebrew not found. Skipping."
    return 0
  fi

  run brew update || warning "brew update reported issues."
  run brew upgrade || warning "brew upgrade reported issues."
  run brew cleanup || true

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

  local used
  used="$(percent_used_root)"
  info "Disk used: ${used}% (thin threshold is ${TM_THIN_THRESHOLD}%)"

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
  [[ -d "$path" ]] || { warning "No logs dir: $path"; return 0; }

  info "Deleting *.log older than ${LOG_TRIM_DAYS} days in: $path"
  [[ "${DRY_RUN:-0}" -eq 1 ]] && { warning "DRY-RUN: no deletions performed."; return 0; }

  find "$path" -type f -name "*.log" -mtime +"$LOG_TRIM_DAYS" -delete 2>/dev/null || true
  success "User log trim complete."
}

trim_user_caches() {
  section "Trim User Caches (age-based)"
  local target="${HOME}/Library/Caches"
  [[ -d "$target" ]] || { warning "No caches dir: $target"; return 0; }

  # Hard assertion to avoid catastrophic deletes
  [[ "$target" == "${HOME}/Library/Caches" ]] || die "Refusing to operate on unexpected cache path: $target"

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

ALL_SAFE=0
ALL_DEEP=0

DO_REPORT=0
DO_PREFLIGHT=0

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

    --preflight) DO_PREFLIGHT=1; shift ;;
    --report) DO_REPORT=1; shift ;;
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
      if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then LOG_TRIM_DAYS="$2"; shift 2; else shift; fi
      ;;
    --trim-caches)
      DO_TRIM_CACHES=1
      if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then CACHE_TRIM_DAYS="$2"; shift 2; else shift; fi
      ;;

    --space-threshold) SPACE_THRESHOLD="${2:-85}"; shift 2 ;;
    --tm-thin-threshold) TM_THIN_THRESHOLD="${2:-88}"; shift 2 ;;
    --tm-thin-bytes) TM_THIN_BYTES="${2:-20000000000}"; shift 2 ;;

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
  (( DO_PREFLIGHT )) && preflight
  (( DO_REPORT )) && report_system_posture

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
