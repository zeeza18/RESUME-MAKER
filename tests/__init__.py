from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))
