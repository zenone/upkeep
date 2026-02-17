#!/usr/bin/env python3
"""Dry-ish test matrix runner.

Runs each allowed operation in "safe" mode using maintain.sh:
- Adds --dry-run so nothing changes on disk
- Uses --output-json for structured parsing

This is intended as a preflight gate BEFORE running real operations via the daemon.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINTAIN_SH = REPO_ROOT / "maintain.sh"
OUT_DIR = REPO_ROOT / "docs" / "test-matrix"
OUT_FILE = OUT_DIR / "dryish-results.json"

# Must stay in sync with daemon/maintenance_daemon.py
ALLOWED_OPERATIONS: dict[str, tuple[list[str], int]] = {
    "macos-check": (["--list-macos-updates"], 300),
    "macos-install": (["--install-macos-updates", "--assume-yes"], 1800),
    "brew-update": (["--brew", "--assume-yes"], 900),
    "brew-cleanup": (["--brew-cleanup", "--assume-yes"], 600),
    "mas-update": (["--mas", "--assume-yes"], 1200),
    "disk-verify": (["--verify-disk"], 300),
    "disk-repair": (["--repair-disk", "--assume-yes"], 600),
    "smart-check": (["--smart"], 300),
    "trim-logs": (["--trim-logs", "30", "--assume-yes"], 300),
    "trim-caches": (["--trim-caches", "30", "--assume-yes"], 300),
    "thin-tm": (["--thin-tm-snapshots", "--assume-yes"], 300),
    "spotlight-status": (["--spotlight-status"], 300),
    "spotlight-reindex": (["--spotlight-reindex", "--assume-yes"], 300),
    "dns-flush": (["--flush-dns", "--assume-yes"], 300),
    "periodic": (["--periodic", "--assume-yes"], 300),
    "space-report": (["--space-report"], 300),
    "browser-cache": (["--browser-cache", "--assume-yes"], 300),
    "dev-cache": (["--dev-cache", "--assume-yes"], 300),
    "mail-optimize": (["--mail-optimize", "--assume-yes"], 300),
}


@dataclass
class RunResult:
    operation_id: str
    ok: bool
    exit_code: int
    duration_seconds: float
    raw_json: dict[str, Any] | None
    stdout: str
    stderr: str


def run_one(operation_id: str, args: list[str]) -> RunResult:
    cmd = [str(MAINTAIN_SH)] + args + ["--dry-run", "--output-json"]
    env = os.environ.copy()

    # Try to emulate daemon non-interactive characteristics:
    env["COLUMNS"] = "999"
    env["LINES"] = "999"

    start = time.time()
    try:
        # Even in dry-run mode, some commands (notably softwareupdate listing)
        # can hang on certain systems. Keep this bounded.
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=90)
        dur = time.time() - start
        stdout = p.stdout
        stderr = p.stderr
        exit_code = p.returncode
    except subprocess.TimeoutExpired as e:
        dur = time.time() - start
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
        exit_code = 124

    raw = None
    ok = exit_code == 0

    # In JSON mode, maintain.sh should output a JSON object on stdout.
    try:
        if stdout.strip():
            raw = json.loads(stdout)
    except Exception:
        ok = False

    # If script claims failure in JSON, treat as failure.
    if isinstance(raw, dict):
        status = raw.get("status")
        if status in {"error", "failed"}:
            ok = False

    return RunResult(
        operation_id=operation_id,
        ok=ok,
        exit_code=exit_code,
        duration_seconds=dur,
        raw_json=raw,
        stdout=stdout,
        stderr=stderr,
    )


def main() -> int:
    if not MAINTAIN_SH.exists():
        print(f"ERROR: maintain.sh not found at {MAINTAIN_SH}", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    for op_id, (args, _timeout) in ALLOWED_OPERATIONS.items():
        print(f"==> dry-ish: {op_id}")
        r = run_one(op_id, args)

        row: dict[str, Any] = {
            "operation_id": r.operation_id,
            "ok": r.ok,
            "exit_code": r.exit_code,
            "duration_seconds": round(r.duration_seconds, 3),
            "raw": r.raw_json,
        }
        results.append(row)

        if not r.ok:
            failures.append(op_id)
            # Keep enough context to debug quickly, but avoid huge logs in the JSON file.
            row["stdout_tail"] = r.stdout[-4000:]
            row["stderr_tail"] = r.stderr[-4000:]

    OUT_FILE.write_text(json.dumps({"results": results, "failures": failures}, indent=2))

    print("\nSummary")
    print(f"- total: {len(results)}")
    print(f"- failures: {len(failures)}")
    if failures:
        print("- failed ops:")
        for op in failures:
            print(f"  - {op}")
        print(f"\nResults written: {OUT_FILE}")
        return 1

    print(f"All dry-ish checks passed. Results written: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
