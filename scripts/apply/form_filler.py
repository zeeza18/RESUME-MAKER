"""Form filling logic with resume and script data."""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional


class FormFiller:
    """Manages form data and filling logic."""

    def __init__(self, resume_path: Optional[Path] = None, script_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parents[1]

        self.resume_path = resume_path or base_dir / "data" / "resume.txt"
        self.script_path = script_path or base_dir / "data" / "script.txt"

        self._resume_data = None
        self._script_answers = None
        self._tailored_resume_text: Optional[str] = None
        self._tailored_pdf_path: Optional[Path] = None

        # Standard form data
        self.standard_data = {
            "email": "mohammedazeezulla6996@gmail.com",
            "phone": "",  # Add your phone
            "linkedin": "",  # Add your LinkedIn
            "github": "",  # Add your GitHub
            "portfolio": "",
            "location": "",
            "visa_status": "Authorized to work",
            "start_date": "Immediately",
            "salary_expectation": "Negotiable",
        }

    @staticmethod
    def _extract_text_from_latex(tex_content: str) -> str:
        """Strip LaTeX commands to recover plain text from a .tex file."""
        text = tex_content
        # Remove preamble (everything before \begin{document})
        doc_start = text.find(r'\begin{document}')
        if doc_start != -1:
            text = text[doc_start + len(r'\begin{document}'):]
        doc_end = text.find(r'\end{document}')
        if doc_end != -1:
            text = text[:doc_end]
        # Strip common resume-template commands
        for cmd in (
            r'\resumeItem', r'\resumeSubheading', r'\resumeProjectHeading',
            r'\resumeItemListStart', r'\resumeItemListEnd',
            r'\resumeSubHeadingListStart', r'\resumeSubHeadingListEnd',
            r'\textbf', r'\textit', r'\emph', r'\underline', r'\small',
            r'\LARGE', r'\scshape', r'\href', r'\vspace',
        ):
            text = text.replace(cmd, '')
        # Remove \section{...} but keep the title
        text = re.sub(r'\\section\{([^}]*)\}', r'\n\1\n', text)
        # Remove remaining \command{...} keeping inner text
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        # Remove \command[...]{...} keeping inner text
        text = re.sub(r'\\[a-zA-Z]+\[[^\]]*\]\{([^}]*)\}', r'\1', text)
        # Remove leftover backslash commands
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        # Remove LaTeX special chars
        for ch in ('{', '}', '$', '\\', '\\\\'):
            text = text.replace(ch, '')
        # Remove |
        text = text.replace('|', ' | ')
        # Collapse whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def load_resume(self) -> str:
        """Load resume content. Falls back to LaTeX source if resume.txt is missing."""
        if self._resume_data is not None:
            return self._resume_data

        # Try plain text first
        if self.resume_path.exists() and self.resume_path.stat().st_size > 0:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                self._resume_data = f.read()
            return self._resume_data

        # Fallback: extract text from the LaTeX source
        project_root = Path(__file__).resolve().parents[2]
        tex_path = project_root / "docs" / "latex" / "main.tex"
        if tex_path.exists():
            with open(tex_path, 'r', encoding='utf-8') as f:
                tex_content = f.read()
            self._resume_data = self._extract_text_from_latex(tex_content)
            return self._resume_data

        self._resume_data = ""
        return self._resume_data

    def load_script_answers(self) -> Dict[str, str]:
        """Load scripted Q&A answers."""
        if self._script_answers is not None:
            return self._script_answers

        self._script_answers = {}

        if self.script_path.exists():
            with open(self.script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse Q: A: format
            current_question = None
            current_answer = []

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    if current_question and current_answer:
                        self._script_answers[current_question] = '\n'.join(current_answer).strip()
                    current_question = line[2:].strip()
                    current_answer = []
                elif line.startswith('A:'):
                    current_answer.append(line[2:].strip())
                elif current_question and line:
                    current_answer.append(line)

            if current_question and current_answer:
                self._script_answers[current_question] = '\n'.join(current_answer).strip()

        return self._script_answers

    def extract_resume_field(self, field_type: str) -> Optional[str]:
        """Extract specific field from resume."""
        resume = self.load_resume()

        patterns = {
            "name": r'^([A-Z][a-z]+ [A-Z][a-z]+)',
            "email": r'[\w\.-]+@[\w\.-]+\.\w+',
            "phone": r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}',
            "linkedin": r'linkedin\.com/in/[\w-]+',
            "github": r'github\.com/[\w-]+',
        }

        if field_type in patterns:
            match = re.search(patterns[field_type], resume, re.MULTILINE)
            if match:
                return match.group(0)

        return None

    def get_field_value(self, field_purpose: str, field_label: str = "") -> Optional[str]:
        """Get the appropriate value for a form field."""
        purpose = field_purpose.lower()
        label = field_label.lower()

        # Direct mappings
        if 'email' in purpose or 'email' in label:
            return self.standard_data.get('email') or self.extract_resume_field('email')

        if 'phone' in purpose or 'phone' in label or 'mobile' in label:
            return self.standard_data.get('phone') or self.extract_resume_field('phone')

        if 'linkedin' in purpose or 'linkedin' in label:
            return self.standard_data.get('linkedin') or self.extract_resume_field('linkedin')

        if 'github' in purpose or 'github' in label:
            return self.standard_data.get('github') or self.extract_resume_field('github')

        if 'first' in purpose and 'name' in purpose:
            name = self.extract_resume_field('name')
            return name.split()[0] if name else None

        if 'last' in purpose and 'name' in purpose:
            name = self.extract_resume_field('name')
            return name.split()[-1] if name else None

        if 'full' in purpose and 'name' in purpose or purpose == 'name':
            return self.extract_resume_field('name')

        if 'location' in purpose or 'city' in label or 'address' in label:
            return self.standard_data.get('location')

        if 'visa' in purpose or 'authorized' in label or 'work authorization' in label:
            return self.standard_data.get('visa_status')

        if 'start' in purpose or 'available' in label:
            return self.standard_data.get('start_date')

        if 'salary' in purpose or 'compensation' in label:
            return self.standard_data.get('salary_expectation')

        if 'portfolio' in purpose or 'website' in label:
            return self.standard_data.get('portfolio')

        # Check script answers for the label
        script_answers = self.load_script_answers()
        for q, a in script_answers.items():
            if q.lower() in label or label in q.lower():
                return a

        return None

    def prepare_form_data(self, detected_fields: Dict[str, str]) -> Dict[str, str]:
        """
        Prepare form data based on detected field purposes.

        Args:
            detected_fields: Map of field_purpose -> css_selector

        Returns:
            Map of css_selector -> value
        """
        form_data = {}

        for purpose, selector in detected_fields.items():
            value = self.get_field_value(purpose)
            if value:
                form_data[selector] = value

        return form_data

    def set_tailored_resume(self, text: str, pdf_path: Optional[Path] = None) -> None:
        """Set the tailored resume text and optional PDF path."""
        self._tailored_resume_text = text
        self._tailored_pdf_path = pdf_path
        # Also update cached resume data so field extraction uses tailored version
        self._resume_data = text

    def get_resume_pdf_path(self) -> Optional[Path]:
        """Get path to resume PDF for upload. Prefers tailored PDF if available."""
        # Check tailored PDF first
        if self._tailored_pdf_path and self._tailored_pdf_path.exists():
            return self._tailored_pdf_path

        base_dir = Path(__file__).resolve().parents[2]

        candidates = [
            base_dir / "docs" / "latex" / "main.pdf",
            base_dir / "output" / "resume.pdf",
            base_dir / "resume.pdf",
        ]

        for path in candidates:
            if path.exists():
                return path

        return None

    def update_standard_data(self, updates: Dict[str, str]) -> None:
        """Update standard form data."""
        self.standard_data.update(updates)
