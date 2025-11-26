"""Shared configuration for the resume generator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

DEFAULT_INPUT = Path("output/tailored_resume_round_3.txt")
DEFAULT_OUTPUT = Path("output/tailored_resume_best.pdf")
PAGE_WIDTH = 210  # A4 width in mm
PAGE_HEIGHT = 297
MARGIN = 18
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN * 2)
LINE_HEIGHT = 5.0
BODY_FONT_SIZE = 9.0
HEADING_FONT_SIZE = 11.0
SMALL_GAP = 2.0

SECTION_PATTERN = re.compile(r"^\*\*([A-Z][A-Z\s/&-]+)\*\*$")
BOLD_PATTERN = re.compile(r"\*\*(.*?)\*\*")
LINK_PATTERN = re.compile(r"\[(.*?)\]\((.*?)\)")
BULLET_PREFIX = "- "

UNICODE_REPLACEMENTS: Dict[str, str] = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2022": BULLET_PREFIX,
    "\u2023": BULLET_PREFIX,
    "\u2212": "-",  # minus sign
    "\u00b2": "^2",
    "\u00d7": "x",
    "\u2713": "-",
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\xa0": " ",  # non-breaking space
    "\uf0b7": BULLET_PREFIX,
    "\ufffd": "-",
}
