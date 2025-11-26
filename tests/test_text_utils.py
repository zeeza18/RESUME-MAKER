from __future__ import annotations

import unittest

from resume_maker.text_utils import (
    cleanse_line,
    convert_links,
    dedupe_list,
    is_section_heading,
    to_ascii,
)


class TextUtilsTests(unittest.TestCase):
    def test_convert_links_flattens_markdown_links(self) -> None:
        text = "Find me on [GitHub](https://github.com/example)"
        self.assertEqual(
            convert_links(text), "Find me on GitHub: https://github.com/example"
        )

    def test_cleanse_line_removes_markdown_and_unicode(self) -> None:
        dirty = "**Lead** Engineer \u2014 built [Site](https://example.com)"
        cleaned = cleanse_line(dirty)
        self.assertEqual(cleaned, "Lead Engineer - built Site: https://example.com")

    def test_to_ascii_replaces_special_symbols(self) -> None:
        self.assertEqual(to_ascii("Growth \u2013 10\u00d7"), "Growth - 10x")

    def test_is_section_heading_matches_expected_format(self) -> None:
        self.assertTrue(is_section_heading("**EXPERIENCE**"))
        self.assertFalse(is_section_heading("Experience"))

    def test_dedupe_list_removes_duplicate_entries(self) -> None:
        records = [
            {"title": "Engineer", "company": "A"},
            {"title": "Engineer", "company": "A"},
            {"title": "Lead", "company": "B"},
        ]
        unique = dedupe_list(records, key_fn=lambda r: (r["title"], r["company"]))
        self.assertEqual(
            unique,
            [
                {"title": "Engineer", "company": "A"},
                {"title": "Lead", "company": "B"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
