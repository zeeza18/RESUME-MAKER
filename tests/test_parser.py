from __future__ import annotations

import unittest

from resume_maker.parser import parse_resume_text


def sample_resume_text() -> str:
    return """John Doe
Builder | john@example.com | https://github.com/johndoe

**EDUCATION**
University of Testing
B.S. Computer Science
City, ST | 2015-2019

**EXPERIENCE**
Senior Engineer | 2021-Present
Acme Corp | Remote
- Led platform rewrite
- Improved performance by 35%

**PROJECTS**
Resume CLI | 2024
Command-line resume builder.
- Parses tailored resume text

**SKILLS**
Languages: Python, Go
Cloud: AWS, Azure
"""


class ParserTests(unittest.TestCase):
    def test_parse_resume_text_extracts_core_sections(self) -> None:
        parsed = parse_resume_text(sample_resume_text())

        self.assertEqual(parsed["name"], "John Doe")
        self.assertEqual(parsed["tagline"], "Builder")
        self.assertEqual(
            parsed["contacts"], ["john@example.com", "https://github.com/johndoe"]
        )

        sections = parsed["sections"]
        self.assertEqual(len(sections["education"]), 1)
        education = sections["education"][0]
        self.assertEqual(education["institution"], "University of Testing")
        self.assertEqual(education["degree"], "B.S. Computer Science")
        self.assertEqual(education["location"], "City, ST")
        self.assertEqual(education["dates"], "2015-2019")

        experience = sections["experience"][0]
        self.assertEqual(experience["title"], "Senior Engineer")
        self.assertEqual(experience["dates"], "2021-Present")
        self.assertEqual(experience["company"], "Acme Corp")
        self.assertEqual(experience["location"], "Remote")
        self.assertEqual(
            experience["bullets"],
            ["- Led platform rewrite", "- Improved performance by 35%"],
        )

        project = sections["projects"][0]
        self.assertEqual(project["name"], "Resume CLI")
        self.assertEqual(project["dates"], "2024")
        self.assertEqual(project["details"], "Command-line resume builder.")

        skills = sections["skills"]
        self.assertEqual(
            skills,
            [
                {"category": "Languages", "items": "Python, Go"},
                {"category": "Cloud", "items": "AWS, Azure"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
