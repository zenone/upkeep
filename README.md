# macOS Tahoe Maintenance Toolkit

A **safe-by-default, guardrailed maintenance script for macOS Tahoe** (and recent macOS versions).

This tool covers the same territory as OnyX - updates, disk verification, cleanup, indexing, and system checks - but with a different philosophy:

> Audit first. Fix intentionally. Avoid ritual “optimization.”
> 

Modern macOS already performs a lot of self-maintenance. This script focuses on the things that *actually matter* while avoiding risky or unnecessary actions unless you explicitly ask for them.

---

## Why This Exists

Traditional “optimizer” tools often:

- Aggressively delete caches
- Rebuild indexes without context
- Encourage maintenance as a ritual instead of a response to symptoms

That can:

- Slow down your next reboot or login
- Cause massive cache/index rebuild churn
- Mask real root causes (disk pressure, updates, failing storage)

This toolkit takes a **systems-first approach**:

- Safe defaults
- Explicit opt-in for heavy actions
- Clear reporting so you understand *why* something is happening

---

## What It Does

### Always Safe (Default / Audit-Oriented)

- Preflight checks (disk space, power, network)
- System posture report (OS, hardware, storage, security status)
- Lists available macOS updates (does not install unless asked)
- Verifies root filesystem
- SMART status (best-effort)
- Disk usage hotspot reporting
- Lists Time Machine local snapshots
- Spotlight status check
- Light log trimming (age-based)

### Optional / Guarded Maintenance

- Install macOS updates
- Homebrew update / upgrade / cleanup
- App Store updates via `mas`
- Time Machine snapshot thinning (threshold-based)
- User cache trimming (age-based, not scorched-earth)
- Run macOS periodic scripts
- Flush DNS cache
- Rebuild Spotlight index

Every potentially disruptive action:

- Is **opt-in**
- Explains what it does
- Asks for confirmation (unless you explicitly disable prompts)

---

## Quick Start

Make the script executable:

```bash
chmod +x maintain.sh
```

Run with help output:

```markdown
./maintain.sh --help
```

## Recommended Usage (OnyX-Equivalent Guidance)

### Daily / Regular Maintenance (Sane Default)

If you want the closest **“OnyX one-click equivalent” while staying sane**, this is the run I’d actually use day-to-day on Tahoe:

```bash
./maintain.sh --all-safe --install-macos-updates --brew

```

This:

- Runs preflight checks
- Generates a system posture report
- Verifies disk health
- Lists and installs macOS updates
- Updates Homebrew packages
- Avoids heavy rebuilds and cache nukes

### When Something Is Actually Off

Only when something feels wrong (search weird, Mac crawling, disk pressure, unexplained lag):

```bash
./maintain.sh --all-deep

```

This includes deeper actions like:

- Snapshot thinning
- Cache trimming
- Periodic scripts
- DNS flush
- Spotlight reindex

All still guarded and confirmable.

---

## Common Task Examples

List available macOS updates (no changes):

```bash
./maintain.sh --list-macos-updates

```

Install macOS updates only:

```bash
./maintain.sh --install-macos-updates

```

Run Homebrew maintenance:

```bash
./maintain.sh --brew

```

Verify disk health:

```bash
./maintain.sh --verify-disk

```

Generate disk space hotspot report:

```bash
./maintain.sh --space-report

```

Rebuild Spotlight index (heavy):

```bash
./maintain.sh --spotlight-reindex

```

---

## Non-Interactive / Automation

For scripting or remote execution:

```bash
./maintain.sh --all-safe --assume-yes

```

Preview actions without changing anything:

```bash
./maintain.sh --all-safe --dry-run

```

---

## Safety & Design Principles

- ❌ Refuses to run as root
- ✅ Uses `sudo` only when required
- ❌ No `rm -rf` on broad directories
- ✅ Cache cleanup is **age-based**, not destructive
- ❌ No sourcing of shell rc files
- ✅ Strict bash mode (`set -Eeuo pipefail`)
- ✅ Hard path assertions before deletion
- ✅ Full logging to `~/Library/Logs/`

---

## Logs

Each run produces a timestamped log file:

```
~/Library/Logs/mac-maintenance-YYYYMMDD-HHMMSS.log

```

Useful for:

- Troubleshooting
- Comparing system state over time
- Verifying what actually ran

---

## Compatibility

- macOS Tahoe
- Likely compatible with recent macOS versions (Sonoma, Ventura)
- Apple Silicon & Intel
- Requires standard macOS CLI tools
- Optional integrations:
    - Homebrew (`brew`)
    - App Store CLI (`mas`)

---

## Final Thought

This script is not about “optimizing” macOS.

It’s about:

- Knowing what state your system is in
- Applying maintenance **only when it’s justified**
- Letting macOS do its job the rest of the time

Use it as a **tool**, not a ritual.

---

Enjoy. Stay intentional.