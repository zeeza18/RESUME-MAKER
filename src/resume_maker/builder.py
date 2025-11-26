"""Bridge the parsing and PDF renderer layers."""

from __future__ import annotations

from pathlib import Path

from .parser import parse_resume_text
from .pdf_renderer import ResumePDF, render_resume


def build_resume_pdf(input_path: Path, output_path: Path) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(f"Could not find resume text at {input_path}.")

    text = input_path.read_text(encoding="utf-8")
    parsed = parse_resume_text(text)

    pdf = ResumePDF()
    render_resume(pdf, parsed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))  # type: ignore[arg-type]
    return output_path
