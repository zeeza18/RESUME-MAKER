"""Backward-compatible entrypoint for the resume generator CLI."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from resume_maker.cli import main


if __name__ == "__main__":
    main()
