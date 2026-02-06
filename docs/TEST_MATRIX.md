# mac-maintenance — Test Matrix (P0)

Goal: systematically validate all 18 maintenance operations end-to-end.

This document is the canonical checklist for ship readiness.

## Run modes

- **Dry-ish (safe)**: runs each operation via `upkeep.sh` with `--dry-run --output-json` to validate:
  - command wiring / flags
  - dependency detection
  - non-interactive safety (no blocking prompts)
  - JSON output parsing

- **Real (on machine)**: runs each operation via the **daemon queue path** (web UI/API → queue → daemon → upkeep.sh) to validate end-to-end behavior.

## Operations

| Operation ID | Name | Dry-ish | Real | Notes |
|---|---|---:|---:|---|
| macos-check | Check macOS Updates | ⬜ | ⬜ | |
| macos-install | Install macOS Updates | ⬜ | ⬜ | |
| brew-update | Update Homebrew | ⬜ | ⬜ | |
| brew-cleanup | Cleanup Homebrew | ⬜ | ⬜ | |
| mas-update | Update App Store Apps | ⬜ | ⬜ | |
| disk-verify | Verify Disk | ⬜ | ⬜ | |
| disk-repair | Repair Disk | ⬜ | ⬜ | |
| smart-check | Check SMART Status | ⬜ | ⬜ | |
| trim-logs | Trim User Logs | ⬜ | ⬜ | |
| trim-caches | Trim User Caches | ⬜ | ⬜ | |
| browser-cache | Clear Browser Caches | ⬜ | ⬜ | |
| dev-cache | Clear Developer Caches | ⬜ | ⬜ | |
| thin-tm | Thin Time Machine Snapshots | ⬜ | ⬜ | |
| spotlight-status | Check Spotlight Status | ⬜ | ⬜ | |
| spotlight-reindex | Rebuild Spotlight Index | ⬜ | ⬜ | |
| dns-flush | Flush DNS Cache | ⬜ | ⬜ | |
| mail-optimize | Optimize Mail Database | ⬜ | ⬜ | |
| space-report | Disk Space Report | ⬜ | ⬜ | |

## Results artifacts

- `docs/test-matrix/dryish-results.json`
- `docs/test-matrix/real-results.json`

