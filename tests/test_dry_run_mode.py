import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINTAIN_SH = REPO_ROOT / "upkeep.sh"


def _run_json(args: list[str], timeout_s: int = 10) -> dict:
    proc = subprocess.run(
        [str(MAINTAIN_SH)] + args,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip(), "expected JSON output"
    return json.loads(proc.stdout)


def test_brew_cleanup_dry_run_is_bounded_and_noninteractive():
    # Historically, some ops still executed user-context commands even in --dry-run,
    # causing hangs (e.g., Homebrew auto-update / network).
    # This must stay bounded.
    data = _run_json(["--brew-cleanup", "--assume-yes", "--dry-run", "--output-json"], timeout_s=10)
    assert isinstance(data, dict)
    dry_run = data.get("dry_run")
    if dry_run is None and isinstance(data.get("summary"), dict):
        dry_run = data["summary"].get("dry_run")
    assert dry_run in (1, True)


def test_mas_update_dry_run_is_bounded_and_noninteractive():
    data = _run_json(["--mas", "--assume-yes", "--dry-run", "--output-json"], timeout_s=10)
    assert isinstance(data, dict)
    dry_run = data.get("dry_run")
    if dry_run is None and isinstance(data.get("summary"), dict):
        dry_run = data["summary"].get("dry_run")
    assert dry_run in (1, True)
