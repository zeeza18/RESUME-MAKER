"""FPDF rendering helpers."""

from __future__ import annotations

from typing import Dict, List

try:
    from fpdf import FPDF  # type: ignore
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "The 'fpdf2' package is required. Install it with 'pip install fpdf2' and rerun this script."
    ) from exc

from .constants import (
    BODY_FONT_SIZE,
    CONTENT_WIDTH,
    HEADING_FONT_SIZE,
    LINE_HEIGHT,
    MARGIN,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    SMALL_GAP,
)
from .text_utils import to_ascii


class ResumePDF(FPDF):
    """Lightweight PDF helper for resume layout."""

    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False, margin=MARGIN)
        self.add_page()
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_font("Helvetica", "", BODY_FONT_SIZE)
        self.set_text_color(20, 20, 20)

    def ensure_space(self, needed: float) -> None:
        if self.get_y() + needed > PAGE_HEIGHT - MARGIN:
            self.add_page()

    def write_header(self, name: str, tagline: str, contacts: List[str]) -> None:
        self.set_xy(MARGIN, MARGIN)
        self.set_font("Helvetica", "B", 18)
        self.cell(CONTENT_WIDTH, 10, to_ascii(name), ln=1)

        self.set_font("Helvetica", "", 11)
        if tagline:
            self.cell(CONTENT_WIDTH, 6, to_ascii(tagline), ln=1)

        if contacts:
            self.set_font("Helvetica", "", 9)
            contact_line = " | ".join(to_ascii(contact) for contact in contacts)
            self.multi_cell(CONTENT_WIDTH, 5, contact_line, border=0)

        self.ln(4)

    def write_section_title(self, title: str) -> None:
        self.ensure_space(10)
        self.set_font("Helvetica", "B", HEADING_FONT_SIZE)
        self.cell(CONTENT_WIDTH, 6, title.upper(), ln=1)
        y = self.get_y()
        self.set_draw_color(80, 88, 120)
        self.set_line_width(0.4)
        self.line(MARGIN, y, PAGE_WIDTH - MARGIN, y)
        self.ln(SMALL_GAP)

    def write_two_column(self, left: str, right: str = "", bold_left: bool = False) -> None:
        left = to_ascii(left)
        right = to_ascii(right)
        left_width = CONTENT_WIDTH * 0.68
        right_width = CONTENT_WIDTH - left_width

        self.ensure_space(LINE_HEIGHT * 2)
        start_x = self.get_x()
        start_y = self.get_y()

        self.set_font("Helvetica", "B" if bold_left else "", BODY_FONT_SIZE)
        self.multi_cell(left_width, LINE_HEIGHT, left, border=0)
        left_height = self.get_y() - start_y

        self.set_xy(start_x + left_width, start_y)
        self.set_font("Helvetica", "", BODY_FONT_SIZE)
        if right:
            self.multi_cell(right_width, LINE_HEIGHT, right, border=0, align="R")
            right_height = self.get_y() - start_y
        else:
            right_height = left_height

        self.set_y(start_y + max(left_height, right_height))
        self.ln(0.5)

    def write_bullets(self, bullets: List[str]) -> None:
        for bullet in bullets:
            bullet_text = to_ascii(bullet)
            if not bullet_text:
                continue
            self.ensure_space(LINE_HEIGHT * 2)
            self.set_x(MARGIN)
            self.cell(4, LINE_HEIGHT, "-", border=0)
            self.set_x(MARGIN + 4)
            self.multi_cell(CONTENT_WIDTH - 4, LINE_HEIGHT, bullet_text, border=0)

    def write_skills(self, skills: List[Dict[str, str]]) -> None:
        self.set_font("Helvetica", "", BODY_FONT_SIZE)
        for skill in skills:
            label = to_ascii(skill.get("category", "")).rstrip(":")
            items = to_ascii(skill.get("items", ""))
            line = f"{label + ': ' if label else ''}{items}" if items else label
            self.multi_cell(CONTENT_WIDTH, LINE_HEIGHT, line, border=0)


def render_resume(pdf: ResumePDF, data: Dict[str, object]) -> None:
    pdf.write_header(data["name"], data["tagline"], data["contacts"])
    sections: Dict[str, List[Dict[str, str]]] = data["sections"]

    education = sections.get("education", [])
    if education:
        pdf.write_section_title("Education")
        for entry in education:
            pdf.write_two_column(entry["institution"], entry["location"], bold_left=True)
            pdf.write_two_column(entry["degree"], entry["dates"])
            pdf.ln(1)

    experience = sections.get("experience", [])
    if experience:
        pdf.write_section_title("Experience")
        for role in experience:
            pdf.write_two_column(role["title"], role["dates"], bold_left=True)
            pdf.write_two_column(role["company"], role["location"])
            pdf.write_bullets(role.get("bullets", []))
            pdf.ln(1)

    projects = sections.get("projects", [])
    if projects:
        pdf.write_section_title("Projects")
        for project in projects:
            pdf.write_two_column(project["name"], project["dates"], bold_left=True)
            if project["details"]:
                pdf.write_two_column(project["details"], "")
            pdf.write_bullets(project.get("bullets", []))
            pdf.ln(1)

    skills = sections.get("skills", [])
    if skills:
        pdf.write_section_title("Technical Skills")
        pdf.write_skills(skills)
