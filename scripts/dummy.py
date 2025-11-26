#!/usr/bin/env python3
"""
Standalone tester for Tool 4 (LaTeX formatter).

Reads the finalized resume from `output/final_tailored_resume.txt`,
passes it through `LatexResumeFormatter`, and writes the resulting
LaTeX to `output/dummy_main.tex` without touching the real `main.tex`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.tool4 import LatexResumeFormatter


def load_final_resume(resume_path: Path) -> str:
    if not resume_path.exists():
        raise FileNotFoundError(
            f"Could not find '{resume_path}'. Run the main pipeline first "
            "or supply a custom resume file path."
        )
    content = resume_path.read_text(encoding="utf-8").strip()
    if len(content) < 50:
        raise ValueError(
            f"The resume content in '{resume_path}' is too short "
            "for LaTeX conversion."
        )
    return content


def main(args: list[str]) -> int:
    resume_path = Path(args[1]) if len(args) > 1 else Path("output/final_tailored_resume.txt")
    output_path = Path(args[2]) if len(args) > 2 else Path("output/dummy_main.tex")

    try:
        final_resume = load_final_resume(resume_path)
    except Exception as exc:
        print(f"[Tool4 Dummy] Input error: {exc}")
        return 1

    try:
        formatter = LatexResumeFormatter()
        # Optional hint: re-use current main.tex so the model sees the structure
        template_hint_path = Path("main.tex")
        template_hint = template_hint_path.read_text(encoding="utf-8") if template_hint_path.exists() else ""

        result = formatter.format_to_latex(final_resume, template_hint=template_hint)
        latex_doc = result.get("latex_document", "")

        if not latex_doc:
            print("[Tool4 Dummy] LaTeX generation failed:")
            print(result.get("raw_response", "No additional details"))
            return 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        formatter.save_latex(latex_doc, output_path, create_backup=False)
        print(f"[Tool4 Dummy] LaTeX saved to {output_path}")
        return 0

    except Exception as exc:
        print(f"[Tool4 Dummy] Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
