"""Test configuration.

Ensure the src/ layout is importable in tests without requiring an installed package.
This keeps local dev/test iterations fast and avoids editable-install edge cases.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

# Prepend so local sources win over any site-packages installation.
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
