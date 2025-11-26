"""Command-line interface for the resume generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build_resume_pdf
from .constants import DEFAULT_INPUT, DEFAULT_OUTPUT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a formatted PDF from the tailored resume text."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the tailored resume text file (defaults to round 3 output).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write the generated PDF (defaults to output/tailored_resume_best.pdf).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = build_resume_pdf(args.input.resolve(), args.output.resolve())
    print(f"? PDF created at {output_path}")
