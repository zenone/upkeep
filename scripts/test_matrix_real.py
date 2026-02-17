#!/usr/bin/env python3
"""Run a "real" (non-dry-run) pass of daemon-queued operations.

This exercises the production path:
  API -> /var/local/upkeep-jobs/*.job.json -> root daemon -> upkeep.sh

Notes
- This is intentionally *not* committed output. Results are written under
  docs/test-matrix/ which is gitignored.
- We avoid macOS update installation by default (can be disruptive / reboot).
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow running from repo root without install
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from upkeep.api.maintenance import MaintenanceAPI  # type: ignore

OUT_DIR = REPO / "docs" / "test-matrix"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def main() -> int:
    api = MaintenanceAPI()

    # Operations to run (exclude macos-install by default).
    ops = [
        "macos-check",
        "brew-update",
        "brew-cleanup",
        "mas-update",
        "disk-verify",
        # disk-repair is more disruptive; include but keep early enough to catch issues.
        "disk-repair",
        "smart-check",
        "trim-logs",
        "trim-caches",
        "thin-tm",
        "spotlight-status",
        # spotlight-reindex is heavy but should be safe; include.
        "spotlight-reindex",
        "dns-flush",
        "periodic",
        "space-report",
        "browser-cache",
        "dev-cache",
        "mail-optimize",
    ]

    # Allow opting into macos-install via env
    if os.getenv("INCLUDE_MACOS_INSTALL") == "1":
        ops.insert(1, "macos-install")

    results: list[dict] = []
    failures: list[str] = []

    print(f"Real pass starting @ {utc_now_iso()}")
    print(f"Operations: {', '.join(ops)}")

    for i, op_id in enumerate(ops, 1):
        print(f"\n==> real: {op_id} ({i}/{len(ops)})")
        started = time.time()
        try:
            # Use per-op timeout from API metadata if present, else 30 min.
            op_meta = api.get_operation(op_id)
            timeout = int(op_meta.get("timeout_seconds") or 1800)
        except Exception:
            timeout = 1800

        try:
            res = api.execute_operation(op_id, timeout=timeout)
        except Exception as e:
            res = {
                "operation_id": op_id,
                "status": "error",
                "error": str(e),
                "exit_code": None,
            }

        duration = time.time() - started
        res["operation_id"] = op_id
        res["duration_seconds"] = round(duration, 3)
        results.append(res)

        ok = (res.get("status") in ("success", "completed", "ok")) or (res.get("exit_code") == 0)
        if not ok:
            failures.append(op_id)
            print(f"!! FAIL: {op_id} status={res.get('status')} exit={res.get('exit_code')} err={res.get('error')}")
        else:
            print(f"✓ OK: {op_id} ({int(duration)}s)")

    out = {
        "kind": "real",
        "started_at": utc_now_iso(),
        "ops": ops,
        "failures": failures,
        "results": results,
    }

    out_path = OUT_DIR / "real-results.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")

    print("\nSummary")
    print(f"- total: {len(ops)}")
    print(f"- failures: {len(failures)}")
    if failures:
        print("- failed ops:")
        for f in failures:
            print(f"  - {f}")
    print(f"\nResults written: {out_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
