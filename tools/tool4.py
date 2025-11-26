#!/usr/bin/env python3
"""
Tool 4: LaTeX Resume Formatter
Converts the finalized tailored resume into LaTeX using the reference template.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict
import re

import openai
from dotenv import load_dotenv

# Load environment variables so OPENAI_API_KEY is available
load_dotenv()


class LatexResumeFormatter:
    """Generate a LaTeX resume document from the finalized tailored resume."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = openai.OpenAI(api_key=api_key)
        self.system_prompt = self._load_prompt("tool4_prompt.txt")

        # Preload template example so we can reference it without re-reading on every call
        self.template_example = self._load_template_example()

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "prompt" / filename
        try:
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Prompt file '{filename}' is missing in {prompt_path.parent}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Unable to load prompt '{filename}': {exc}") from exc

    def _load_template_example(self) -> Optional[str]:
        """
        Load the current LaTeX template from main.tex so Tool 4 can mirror the structure.
        Returns None if the file is missing; Tool 4 prompt already embeds the template skeleton.
        """
        template_path = Path(__file__).resolve().parent.parent / "main.tex"
        if template_path.exists():
            try:
                return template_path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def format_to_latex(self, final_resume: str, template_hint: Optional[str] = None) -> Dict[str, str]:
        """
        Use OpenAI to convert the final tailored resume text into LaTeX.

        Args:
            final_resume: The completed tailored resume text from Tool 2.
            template_hint: Optional string containing the reference template.

        Returns:
            Dict with keys `latex_document` and `raw_response`.
        """

        if not final_resume or len(final_resume.strip()) < 50:
            raise ValueError("Final resume content is too short or empty for LaTeX conversion.")

        user_template = template_hint or self.template_example or ""
        user_message = (
            "FINAL_RESUME:\n"
            f"{final_resume.strip()}\n\n"
            "REFERENCE_TEMPLATE:\n"
            f"{user_template.strip()}"
        )

        print("Generating LaTeX resume with OpenAI (Tool 4)...")

        raw_content = ""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4000,
                temperature=0.1,
            )

            raw_content = response.choices[0].message.content or ""
            latex_doc = self._extract_latex_source(raw_content)
            print("LaTeX resume generation complete.")

            # Basic sanity check to ensure output looks like LaTeX
            if not latex_doc.startswith("\\documentclass"):
                raise ValueError(
                    "Generated LaTeX does not start with \\documentclass. Please review the raw response."
                )

            return {
                "latex_document": latex_doc,
                "raw_response": latex_doc,
            }

        except Exception as exc:
            print(f"Error calling OpenAI for LaTeX formatting: {exc}")
            return {
                "latex_document": "",
                "raw_response": raw_content or f"Error: {str(exc)}",
            }

    def _extract_latex_source(self, content: str) -> str:
        """Strip code fences or prose and isolate the LaTeX document."""
        if not content:
            return ""

        cleaned = content.strip()

        # Handle markdown code fences ```latex ... ```
        fence_match = re.search(r"```(?:latex)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        # If prose precedes \documentclass, slice from there
        doc_start = cleaned.find("\\documentclass")
        if doc_start != -1:
            cleaned = cleaned[doc_start:].strip()

        # Ensure we end at \end{document}
        doc_end = cleaned.lower().rfind("\\end{document}")
        if doc_end != -1:
            cleaned = cleaned[: doc_end + len("\\end{document}")].strip()

        return cleaned

    def save_latex(self, latex_document: str, output_path: Path, create_backup: bool = True) -> None:
        """
        Persist the generated LaTeX document to disk.

        Args:
            latex_document: Full LaTeX source returned by Tool 4.
            output_path: Path where the LaTeX file should be written.
            create_backup: Whether to create a timestamped backup if the file already exists.
        """
        if not latex_document or not latex_document.strip():
            raise ValueError("Cannot save empty LaTeX document.")

        try:
            if create_backup and output_path.exists():
                from datetime import datetime

                backup_dir = output_path.parent / "backup"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"{output_path.stem}_{timestamp}.tex"
                backup_path.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(latex_document, encoding="utf-8")
            print(f"LaTeX resume saved to {output_path}")
        except Exception as exc:
            raise RuntimeError(f"Unable to save LaTeX document to {output_path}: {exc}") from exc


if __name__ == "__main__":
    formatter = LatexResumeFormatter()
    sample_resume = """
    Heading:
    Jane Doe | Applied AI Engineer | jane@example.com | 555-555-5555

    Experience:
    Company X — AI Engineer (2024-Present)
    - Built AI agents with Python and LangChain improving response accuracy by 25%
    """
    result = formatter.format_to_latex(sample_resume)
    latex_sample_path = Path(__file__).resolve().parent.parent / "output" / "sample_resume.tex"
    latex_sample_path.parent.mkdir(exist_ok=True)
    if result["latex_document"]:
        formatter.save_latex(result["latex_document"], latex_sample_path, create_backup=False)
