# CHANGELOG

All notable changes between the original `upkeep.sh` script and the current **macOS Tahoe Maintenance Toolkit** are documented here.

This project follows a pragmatic versioning model:
- Major versions reflect **philosophical or architectural shifts**
- Minor versions reflect **feature additions**
- Patch versions reflect **bug fixes or safety improvements**

---

## [3.0.0] – Web Dashboard & Scheduling
### _Modern interface, automation, and comprehensive guidance_

### 🌐 Web Dashboard
- **Modern browser-based interface** at localhost:8080
- Real-time system metrics (CPU, memory, disk, processes)
- Live operation progress with elapsed time and ETA
- Skip/cancel controls during operation execution
- Copy output to clipboard when done

### ✨ Quick Start Wizard
Six presets for different maintenance scenarios:
- 🚀 **Quick Clean** (3 ops, ~5 min) - Fast cache cleanup
- 🔧 **Weekly Routine** (8 ops, ~15 min) - Standard maintenance
- 🏥 **Full Checkup** (12 ops, ~30 min) - Comprehensive check
- 💻 **Developer** (6 ops, ~20 min) - Dev caches (20-60GB savings)
- 🔒 **Security** (5 ops, ~10 min) - Updates + integrity
- 🎯 **Custom** - Pick your own operations

### 📅 Scheduling System
Seven schedule templates with launchd integration:
- ⭐ Essential Weekly Maintenance
- 🧹 Light Daily Cleanup
- 🔧 Deep Monthly Maintenance
- 📦 Software Updates Weekly
- 💻 Developer Cleanup Monthly
- 🔒 Security Focus Weekly
- 💾 Storage Recovery

### 🔧 New Operations (20 total)
- **dev-tools-cache** - Clear npm, pip, Go, Cargo, Composer caches

### 📖 Operation Guidance
Every operation now includes:
- **WHY**: Problems it solves, context
- **WHAT**: Expected outcomes, timeline, side effects
- **WHEN**: Recommended run scenarios

### 🩺 Doctor/Preflight
- Automatic dependency checking before operations
- Actionable fix suggestions for missing tools
- One-click fixes where possible

### ⏱️ Smart ETA
- Historical operation timing
- Per-operation typical duration display
- Batch ETA calculation

### 📊 Storage Analyzer
- Visual breakdown of disk usage
- Largest files/directories list
- Move to Trash or permanent delete
- Category breakdown

### 🔒 Security
- Secure launchd daemon for privileged operations
- No password handling in web API
- Sudo vulnerability checks (CVE-2025-32462, CVE-2025-32463)

### 🛠️ Technical Improvements
- TypeScript frontend with full type checking
- FastAPI backend with Pydantic models
- 47 automated test suites
- ShellCheck compliant bash script

---

## [2.0.0] – macOS Tahoe Maintenance Toolkit  
### _Architectural rewrite & safety-first redesign_

### ⚠️ Breaking Changes
- Script **refuses to run as root**
- Aggressive cache deletion behavior removed
- Shell rc files are no longer sourced
- Destructive actions now require explicit confirmation
- Default execution mode is **audit-only**, not modification

---

### 🧠 Philosophy Shift
**Before:**  
- “Do maintenance” as a single action  
- Heavy cleanup regardless of system state  

**Now:**  
- Audit → decide → act  
- Maintenance is symptom-driven, not ritual-based  
- Safer-than-OnyX defaults with explicit opt-in for heavy tasks  

---

### 🧱 Core Architecture Changes
- Introduced modular, single-responsibility functions
- Centralized logging, confirmation, and execution wrappers
- Added strict bash mode: `set -Eeuo pipefail`
- Added signal handling and clean exit paths
- Introduced structured CLI flags and presets

---

### 🔐 Security Improvements
- Hard path assertions before any delete operation
- Removed `rm -rf` on broad directories
- Eliminated `source ~/.zshrc` and similar patterns
- Added dry-run support for all operations
- Explicit sudo boundaries for privileged commands
- Refuses execution on non-macOS systems

---

### 🧪 Safety & Reliability Enhancements
- Preflight checks:
  - Disk space pressure
  - Power source (AC vs battery)
  - Network reachability
- Guarded execution for:
  - Disk repair
  - Snapshot thinning
  - Spotlight reindex
  - Periodic scripts
  - DNS flush

---

### 📊 New System Visibility Features
- System posture report:
  - macOS version & build
  - Hardware summary
  - Storage overview
  - Security posture (FileVault, Gatekeeper, Firewall, SIP)
- Disk usage hotspot reporting (top space consumers)
- SMART status (best-effort)
- Spotlight indexing status
- Time Machine local snapshot listing

---

### 🔄 Update Management Improvements
- macOS updates:
  - List-only by default
  - Install only when explicitly requested
- Homebrew maintenance:
  - update / upgrade / cleanup
  - `brew doctor` summary
- Optional App Store updates via `mas`

---

### 🧹 Cleanup Behavior Changes
#### Removed
- Full cache directory wipes
- Blanket log deletion

#### Added
- Age-based log trimming (default: 30 days)
- Age-based cache trimming (files only, not directories)
- User confirmation before any cleanup
- Threshold-aware snapshot thinning

---

### 🚀 New Execution Presets
- `--all-safe`
  - Preflight
  - System report
  - Disk verification
  - Update listing
  - Space analysis
  - Light cleanup

- `--all-deep`
  - Includes all-safe
  - Snapshot thinning
  - Cache trimming
  - Periodic scripts
  - DNS flush
  - Spotlight reindex

---

### 🧰 New CLI Features
- `--dry-run` (no system changes)
- `--assume-yes` (non-interactive automation)
- Fine-grained task flags for all modules
- Tunable thresholds for disk pressure and cleanup age
- Full `--help` documentation

---

### 📝 Logging Improvements
- Timestamped logs per run
- Centralized log directory:
~/Library/Logs/upkeep-YYYYMMDD-HHMMSS.log- Clear RUN vs DRY-RUN indicators
- Consistent success/warning/error markers

---

## [1.x.x] – Original Script (Uploaded Version)

### Characteristics
- Monolithic execution flow
- Mixed audit and destructive actions
- Aggressive cache deletion
- Implicit assumptions about environment
- Limited logging and no dry-run capability
- Sourced user shell configuration
- No confirmation gates for heavy actions

### Known Risks (Resolved in 2.0.0)
- Potential catastrophic deletes if variables resolved unexpectedly
- Cache and index rebuild churn causing performance regressions
- Non-deterministic behavior due to sourced rc files
- Lack of safety rails for disk repair or snapshot removal

---

## Upgrade Notes

This is a **deliberate, opinionated rewrite**, not a patch release.

If you relied on:
- “One command nukes everything” behavior  
- Forced cache rebuilds  
- Silent destructive cleanup  

You must now **explicitly request** those behaviors.

This change is intentional.

---

## Future Roadmap (Not Implemented Yet)

- Symptom-driven recommendation mode
- Automated health scoring
- Optional BATS test suite
- CI ShellCheck integration
- Optional GUI wrapper
- Signed / notarized distribution

---

**Bottom line:**  
Version 2.0.0 turns a useful personal script into a **maintainable, explainable, and safe system tool**.
