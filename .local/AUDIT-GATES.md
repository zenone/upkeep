# AUDIT-GATES.md — Upkeep macOS Maintenance Toolkit
# Living registry of verifiable invariants. One gate per major design decision.
# Format: run the command → if output is non-empty, the gate FAILS.
# Rule: add a gate in the SAME commit as the design decision (doc-as-commit rule).

## How to run all gates
```bash
bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/tools/bash/BASH/upkeep
```

---

## U-001 — Script refuses to run as root
**Invariant:** `upkeep.sh` must always exit early if run as root. Uses sudo internally only for specific sub-tasks.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
if 'run as root' not in content.lower():
    print('MISSING: root execution guard not found in upkeep.sh')
"
```
**Pass:** zero output

---

## U-002 — DRY_RUN respected in all trim operations
**Invariant:** `trim_user_logs` and `trim_user_caches` must check `DRY_RUN` before executing any deletion.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
for fn in ['trim_user_logs', 'trim_user_caches']:
    start = content.find(fn + '()')
    if start == -1:
        print(f'MISSING function: {fn}')
        continue
    chunk = content[start:start+3000]
    if 'DRY_RUN' not in chunk:
        print(f'MISSING DRY_RUN check in {fn}')
"
```
**Pass:** zero output

---

## U-003 — validate_safe_path called before rm -rf in destructive functions
**Invariant:** Symlink attack prevention — `validate_safe_path()` must be called in every function that performs `rm -rf` on a user-supplied or derived path.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
if 'validate_safe_path' not in content:
    print('MISSING: validate_safe_path function not found in upkeep.sh')
else:
    for fn in ['trim_user_logs', 'trim_user_caches', 'clear_messages_caches', 'remove_aerial_wallpaper_videos']:
        start = content.find(fn + '()')
        if start == -1:
            continue
        chunk = content[start:start+3000]
        if 'validate_safe_path' not in chunk:
            print(f'MISSING: validate_safe_path not called in {fn}')
"
```
**Pass:** zero output

---

## U-004 — Confirmation required before every destructive operation
**Invariant:** No destructive action (delete, clean, wipe) may execute without a `confirm()` call or an `ASSUME_YES` bypass — both must be present. Silent deletion is never acceptable.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
missing = []
if 'confirm ' not in content and 'confirm(' not in content:
    missing.append('confirm() function usage')
if 'ASSUME_YES' not in content:
    missing.append('ASSUME_YES flag (non-interactive bypass)')
if missing:
    print('MISSING confirmation gates:', missing)
"
```
**Pass:** zero output

---

## U-005 — Log files and log directory restricted to owner
**Invariant:** Log directory gets `chmod 700`, log files get `chmod 600`. Logs may contain sensitive command output (disk paths, process names, etc.).
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
missing = []
if 'chmod 600' not in content:
    missing.append('chmod 600 on log files')
if 'chmod 700' not in content:
    missing.append('chmod 700 on log directory')
if missing:
    print('MISSING log permission hardening:', missing)
"
```
**Pass:** zero output

---

## U-006 — check_disk_safety_thresholds called before trim operations
**Invariant:** `trim_user_logs` and `trim_user_caches` must call `check_disk_safety_thresholds` before deleting anything — prevents blind deletion when disk is already healthy or critically full.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
if 'check_disk_safety_thresholds' not in content:
    print('MISSING: check_disk_safety_thresholds function not found')
else:
    for fn in ['trim_user_logs', 'trim_user_caches']:
        start = content.find(fn + '()')
        if start == -1:
            print(f'MISSING function: {fn}')
            continue
        chunk = content[start:start+2000]
        if 'check_disk_safety_thresholds' not in chunk:
            print(f'MISSING: check_disk_safety_thresholds not called in {fn}')
"
```
**Pass:** zero output

---

## U-007 — Upkeep logs isolated to ~/Library/Logs/upkeep/
**Invariant:** `LOG_DIR` must point to `~/Library/Logs/upkeep/`. Nimbus logs (`~/.nimbus/logs/`) and system logs (`/var/log/`) must never overlap with Upkeep log output.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
if 'Library/Logs/upkeep' not in content:
    print('MISSING: LOG_DIR does not reference ~/Library/Logs/upkeep/')
"
```
**Pass:** zero output

---

## U-008 — Schedule runner uses venv Python, not system Python
**Invariant:** `~/.upkeep/bin/upkeep-run-schedule` must invoke the project's `.venv` Python — not `/usr/bin/python3` or system Python. Ensures consistent dependency versions.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
import os
runner = os.path.expanduser('~/.upkeep/bin/upkeep-run-schedule')
if not os.path.exists(runner):
    print('MISSING: upkeep-run-schedule not found at ~/.upkeep/bin/')
else:
    content = open(runner).read()
    if '.venv/bin/python' not in content and '.venv' not in content:
        print('MISSING: schedule runner does not reference .venv Python')
"
```
**Pass:** zero output

---

## U-009 — No orphan schedule plists in ~/Library/LaunchAgents/
**Invariant:** Every `com.upkeep.schedule.*.plist` in `~/Library/LaunchAgents/` must correspond to an active schedule ID in `~/.upkeep/schedules.json`. Orphans fire silently and no-op but clutter LaunchAgents.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
import json, os, glob
schedules_path = os.path.expanduser('~/.upkeep/schedules.json')
if not os.path.exists(schedules_path):
    print('MISSING: ~/.upkeep/schedules.json not found')
else:
    schedules = json.load(open(schedules_path))
    active_ids = {s['id'] for s in schedules}
    plists = glob.glob(os.path.expanduser('~/Library/LaunchAgents/com.upkeep.schedule.*.plist'))
    for p in plists:
        sched_id = os.path.basename(p).replace('com.upkeep.schedule.', '').replace('.plist', '')
        if sched_id not in active_ids:
            print(f'ORPHAN plist: {os.path.basename(p)}')
"
```
**Pass:** zero output

---

## U-010 — strict bash mode in upkeep.sh (set -Eeuo pipefail)
**Invariant:** `upkeep.sh` must run with `set -Eeuo pipefail`. Prevents silent failures from unchecked return codes or unset variables — the root cause of several historic "it ran but did nothing" bugs.
**Command (gate fails if output non-empty):**
```bash
python3 -c "
content = open('/Users/szenone/Code/tools/bash/BASH/upkeep/upkeep.sh').read()
# Must appear near the top (within first 50 lines)
top = '\n'.join(content.split('\n')[:50])
if 'set -Eeuo pipefail' not in top and 'set -eEuo pipefail' not in top:
    print('MISSING: set -Eeuo pipefail not found in first 50 lines of upkeep.sh')
"
```
**Pass:** zero output
