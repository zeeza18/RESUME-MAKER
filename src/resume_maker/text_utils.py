"""Utility helpers for cleansing and normalising resume text."""

from __future__ import annotations

import unicodedata
from typing import Callable, Dict, List, Tuple

from .constants import BOLD_PATTERN, LINK_PATTERN, SECTION_PATTERN, UNICODE_REPLACEMENTS


def convert_links(text: str) -> str:
    def repl(match) -> str:
        label, url = match.group(1), match.group(2)
        return f"{label}: {url}"

    return LINK_PATTERN.sub(repl, text)


def strip_bold(text: str) -> str:
    return BOLD_PATTERN.sub(lambda m: m.group(1), text)


def to_ascii(text: str) -> str:
    for original, replacement in UNICODE_REPLACEMENTS.items():
        text = text.replace(original, replacement)
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii")


def cleanse_line(line: str) -> str:
    line = convert_links(line)
    line = strip_bold(line)
    line = to_ascii(line)
    return " ".join(line.split()).strip()


def is_section_heading(line: str) -> bool:
    return bool(SECTION_PATTERN.match(line))


def dedupe_list(
    items: List[Dict[str, str]], key_fn: Callable[[Dict[str, str]], Tuple]
) -> List[Dict[str, str]]:
    seen: set[Tuple] = set()
    unique: List[Dict[str, str]] = []
    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
