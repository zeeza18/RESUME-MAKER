#!/usr/bin/env python3
"""
Tool 2: Resume Tailor
Uses Anthropic Claude API to tailor resume based on JD keywords and feedback
Now with JSON output and memory support for multi-round consistency
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResumeTailor:
    """Tailor resume based on JD keywords using Anthropic Claude with memory support"""

    def __init__(self):
        """Initialize Anthropic client"""
        self.client = Anthropic(
            api_key=os.getenv('CLAUDE_API_KEY')
        )
        self.model = "claude-sonnet-4-6"  # Claude Sonnet for resume tailoring

        self.prompts = {
            'round1': self._load_prompt('tool2_prompt.txt'),
            'evaluation': self._load_prompt('tool2_eval_prompt.txt')
        }

    def _load_config(self) -> dict:
        """Load user personal info from config.json at project root."""
        config_path = Path(__file__).resolve().parent.parent / 'config.json'
        try:
            return json.loads(config_path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / 'prompt' / filename
        try:
            return prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Prompt file '{filename}' is missing in {prompt_path.parent}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unable to load prompt '{filename}': {exc}") from exc

    def tailor_resume(
        self,
        original_resume: str,
        keywords: Dict[str, List[str]],
        job_description: str,
        feedback: Optional[str] = None,
        round_number: int = 1,
        locked_changes: Optional[List[Dict[str, Any]]] = None,
        previous_keyword_status: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Tailor resume based on JD keywords and optional feedback

        Args:
            original_resume: The resume content from the previous round or original submission
            keywords: Keywords from Tool 1 (contains keywords, needs, results)
            job_description: Full job description text for context
            feedback: Optional feedback from previous evaluation
            round_number: Current iteration number (1 for the first pass)
            locked_changes: Changes from previous rounds that improved score (DO NOT UNDO)
            previous_keyword_status: Which keywords are already inserted from previous rounds

        Returns:
            dict: Contains tailored resume, change log, keyword mappings, and analysis
        """

        print(f"[TAILOR] Round {round_number}: Tailoring Resume with Claude Sonnet...")

        # --- Personal info from config.json ---
        config = self._load_config()
        personal_block = ""
        if config:
            personal_block = (
                "CANDIDATE PERSONAL INFO — copy these values exactly into the resume header:\n"
                f"  Name:      {config.get('name', '')}\n"
                f"  Phone:     {config.get('phone', '')}\n"
                f"  Email:     {config.get('email', '')}\n"
                f"  LinkedIn:  {config.get('linkedin', '')}\n"
                f"  Portfolio: {config.get('portfolio', '')}\n"
                f"  GitHub:    {config.get('github', '')}\n"
                f"  Location:  {config.get('location', '')}\n\n"
            )

        # --- Structural constraints ---
        structural_constraints = self._build_structural_constraints(original_resume)

        # --- Keywords snapshot ---
        keywords_snapshot = (
            f"Keywords: {', '.join(keywords.get('keywords', [])) or 'None'}\n"
            f"Needs: {', '.join(keywords.get('needs', [])) or 'None'}\n"
            f"Results: {', '.join(keywords.get('results', [])) or 'None'}"
        )

        # --- Build user message ---
        user_message = self._build_user_message(
            round_number=round_number,
            personal_block=personal_block,
            structural_constraints=structural_constraints,
            job_description=job_description,
            original_resume=original_resume,
            keywords_snapshot=keywords_snapshot,
            feedback=feedback,
            locked_changes=locked_changes,
            previous_keyword_status=previous_keyword_status
        )

        # Select prompt based on round
        prompt_key = 'round1' if round_number <= 1 else 'evaluation'
        system_prompt = self.prompts[prompt_key]

        try:
            # Make API call to Anthropic Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract the response
            raw_response = response.content[0].text

            print("[OK] Resume tailoring complete!")

            # Parse the JSON response
            parsed_result = self._parse_json_response(raw_response, original_resume)

            return parsed_result

        except Exception as e:
            print(f"[ERROR] Error calling Claude for resume tailoring: {e}")
            return {
                "tailored_resume": original_resume,
                "change_log": [{"type": "error", "description": str(e)}],
                "keyword_insertions": [],
                "analysis": {},
                "keyword_status": {"successfully_inserted": [], "already_present": [], "cannot_add": []},
                "raw_response": str(e)
            }

    def _build_structural_constraints(self, resume_text: str) -> str:
        """Build structural constraints string from resume analysis."""
        bullet_markers = re.compile(r'^\s*[•\-–]\s', re.MULTILINE)
        total_bullets = len(bullet_markers.findall(resume_text))

        projects_section_match = re.search(r'(?i)PROJECTS?\s*\n(.*)', resume_text, re.DOTALL)
        project_count = 0
        if projects_section_match:
            projects_text = projects_section_match.group(1)
            project_count = len(re.findall(r'(?:^|\n)([^\n•\-–][^\n]+)\n\s*[•\-–]', projects_text))

        block_limits = self._compute_per_block_word_limits(resume_text)
        block_limit_lines = ""
        if block_limits:
            block_limit_lines = (
                "  • Per-block bullet word limits:\n"
                + "\n".join(
                    f'      "{header[:50]}..." → {count} bullets → max {limit} words/bullet'
                    for header, count, limit in block_limits[:5]  # Limit to top 5 for brevity
                )
                + "\n"
            )

        return (
            f"STRUCTURAL CONSTRAINTS:\n"
            f"  • Total bullets: exactly {total_bullets}\n"
            f"  • Projects count: exactly {project_count}\n"
            f"  • Keep ALL original bullets and projects\n"
            f"  • Section order must match original\n"
            f"{block_limit_lines}"
        )

    def _build_user_message(
        self,
        round_number: int,
        personal_block: str,
        structural_constraints: str,
        job_description: str,
        original_resume: str,
        keywords_snapshot: str,
        feedback: Optional[str],
        locked_changes: Optional[List[Dict]],
        previous_keyword_status: Optional[Dict]
    ) -> str:
        """Build the user message for the API call."""

        round_label = f"Round {round_number}"
        prev_label = "original submission" if round_number <= 1 else f"Round {round_number - 1} output"

        message_parts = [
            f"{round_label} tailoring task. Return JSON output.\n",
            personal_block,
            structural_constraints,
            f"\nJOB DESCRIPTION:\n{job_description}\n",
            f"\nCURRENT RESUME ({prev_label.upper()}):\n{original_resume}\n",
            f"\nJD KEYWORDS TO INSERT:\n{keywords_snapshot}\n"
        ]

        # Add locked changes for Round 2+
        if round_number > 1 and locked_changes:
            locked_text = "\n═══ LOCKED CHANGES (DO NOT UNDO) ═══\n"
            locked_text += "These changes improved the score. Keep them intact:\n"
            for change in locked_changes:
                locked_text += f"  • Round {change.get('round', '?')}: {change.get('description', '')}\n"
            message_parts.append(locked_text)

        # Add previous keyword status
        if previous_keyword_status:
            status_text = "\n═══ KEYWORD STATUS FROM PREVIOUS ROUNDS ═══\n"
            inserted = previous_keyword_status.get('successfully_inserted', [])
            if inserted:
                status_text += f"Already inserted (keep these): {', '.join(inserted)}\n"
            missing = previous_keyword_status.get('still_missing', [])
            if missing:
                status_text += f"Still missing (must add): {', '.join(missing)}\n"
            message_parts.append(status_text)

        # Add evaluation feedback
        if feedback:
            message_parts.append(f"\nEVALUATION FEEDBACK TO ADDRESS:\n{feedback}\n")

        message_parts.append("\nReturn your response as valid JSON only. No markdown fences.")

        return "".join(message_parts)

    def _compute_per_block_word_limits(self, resume_text: str) -> list:
        """Compute word limits per block."""
        bullet_re = re.compile(r'^\s*[•\-–]\s')
        section_re = re.compile(
            r'^\s*(EXPERIENCE|EDUCATION|PROJECTS?|SKILLS?|SUMMARY|CERTIFICATIONS?)\s*$',
            re.IGNORECASE,
        )

        blocks = []
        current_header = None
        current_bullets = 0

        for line in resume_text.splitlines():
            stripped = line.strip()
            if not stripped:
                if current_header and current_bullets > 0:
                    blocks.append((current_header, current_bullets))
                current_header = None
                current_bullets = 0
            elif bullet_re.match(line):
                if current_header:
                    current_bullets += 1
            else:
                if current_header and current_bullets > 0:
                    blocks.append((current_header, current_bullets))
                if not section_re.match(stripped):
                    current_header = stripped
                    current_bullets = 0
                else:
                    current_header = None
                    current_bullets = 0

        if current_header and current_bullets > 0:
            blocks.append((current_header, current_bullets))

        return [(h, c, 22 if c > 4 else 28) for h, c in blocks]

    def _parse_json_response(self, response: str, fallback_resume: str) -> Dict[str, Any]:
        """Parse JSON response from Claude."""
        result = {
            "tailored_resume": fallback_resume,
            "change_log": [],
            "keyword_insertions": [],
            "skills_to_add": [],
            "analysis": {},
            "keyword_status": {
                "successfully_inserted": [],
                "already_present": [],
                "cannot_add": []
            },
            "warnings": [],
            "preserved_changes": [],
            "new_fixes_applied": [],
            "raw_response": response
        }

        try:
            # Strip markdown fences
            clean = response.strip()
            clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'^```\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
            clean = clean.strip()

            # Find JSON object
            json_match = re.search(r'\{[\s\S]*\}', clean)
            if not json_match:
                raise ValueError("No JSON object found in response")

            parsed = json.loads(json_match.group(0))
            print("[TOOL2] Successfully parsed JSON response")

            # Extract all fields
            result["analysis"] = parsed.get("analysis", {})
            result["keyword_insertions"] = parsed.get("keyword_insertions", [])
            result["skills_to_add"] = parsed.get("skills_to_add", [])
            result["warnings"] = parsed.get("warnings", [])
            result["preserved_changes"] = parsed.get("preserved_changes", [])
            result["new_fixes_applied"] = parsed.get("new_fixes_applied", [])

            # Extract keyword status
            if "keyword_status" in parsed:
                ks = parsed["keyword_status"]
                result["keyword_status"]["successfully_inserted"] = ks.get("successfully_inserted", [])
                result["keyword_status"]["already_present"] = ks.get("already_present", [])
                # Handle cannot_add which may be list of objects or strings
                cannot_add = ks.get("cannot_add", [])
                result["keyword_status"]["cannot_add"] = [
                    item if isinstance(item, str) else item.get("keyword", str(item))
                    for item in cannot_add
                ]

            # Extract change log (normalize to list of dicts)
            raw_log = parsed.get("change_log", [])
            if isinstance(raw_log, list):
                for item in raw_log:
                    if isinstance(item, dict):
                        result["change_log"].append(item)
                    elif isinstance(item, str):
                        result["change_log"].append({"type": "change", "description": item})

            # Extract tailored resume
            resume_text = parsed.get("tailored_resume", "")
            if resume_text and len(resume_text) > 100:
                result["tailored_resume"] = resume_text
            else:
                print("[WARN] tailored_resume in JSON is empty or too short, using fallback")

            # Log summary
            print(f"[TOOL2] Keywords inserted: {len(result['keyword_status']['successfully_inserted'])}")
            print(f"[TOOL2] Changes logged: {len(result['change_log'])}")
            if result["warnings"]:
                print(f"[TOOL2] Warnings: {len(result['warnings'])}")

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            # Fallback: try to extract resume from non-JSON response
            result["tailored_resume"] = self._extract_resume_fallback(response, fallback_resume)
            result["change_log"] = [{"type": "error", "description": f"JSON parse error: {e}"}]

        except Exception as e:
            print(f"[ERROR] Could not parse response: {e}")
            result["change_log"] = [{"type": "error", "description": str(e)}]

        return result

    def _extract_resume_fallback(self, response: str, fallback: str) -> str:
        """Extract resume from non-JSON response as fallback."""
        # Try to find resume content between common markers
        clean = re.sub(r'^```[a-z]*\s*', '', response.strip(), flags=re.IGNORECASE)
        clean = re.sub(r'\s*```$', '', clean)

        # If it looks like a resume (has typical sections), use it
        if any(marker in clean.upper() for marker in ['EXPERIENCE', 'EDUCATION', 'SKILLS']):
            return clean

        return fallback

    def save_tailored_resume(self, tailored_data: Dict[str, Any], filename: str = "tailored_resume.txt"):
        """Save the tailored resume and structured data to files."""
        try:
            output_dir = Path(__file__).resolve().parent.parent / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save human-readable text file
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("TAILORED RESUME\n")
                f.write("=" * 50 + "\n\n")
                f.write(tailored_data.get('tailored_resume', ''))
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("CHANGE LOG\n")
                f.write("=" * 50 + "\n")
                for change in tailored_data.get('change_log', []):
                    if isinstance(change, dict):
                        f.write(f"• [{change.get('type', 'change')}] {change.get('description', '')}\n")
                    else:
                        f.write(f"• {change}\n")

                # Add keyword mappings
                insertions = tailored_data.get('keyword_insertions', [])
                if insertions:
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("KEYWORD MAPPINGS\n")
                    f.write("=" * 50 + "\n")
                    for ins in insertions:
                        f.write(f"• {ins.get('keyword', '?')}: {ins.get('target_section', '?')} - {ins.get('rationale', '')}\n")

                # Add warnings
                warnings = tailored_data.get('warnings', [])
                if warnings:
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("WARNINGS\n")
                    f.write("=" * 50 + "\n")
                    for w in warnings:
                        f.write(f"⚠️  {w}\n")

            print(f"[OK] Tailored resume saved to {filepath}")

            # Save JSON version for machine processing
            json_filename = filename.replace('.txt', '.json')
            json_path = output_dir / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                # Don't save raw_response to JSON (too large)
                save_data = {k: v for k, v in tailored_data.items() if k != 'raw_response'}
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] JSON data saved to {json_path}")

        except Exception as e:
            print(f"[WARN] Could not save tailored resume: {e}")


# Test function
if __name__ == "__main__":
    tailor = ResumeTailor()

    sample_resume = """
John Doe
Software Engineer

EXPERIENCE
ABC Company | 2022-2024
• Built web applications using Python and React
• Improved system performance by 50%

SKILLS
Languages: Python, JavaScript
"""

    sample_keywords = {
        "keywords": ["Python", "React", "TypeScript", "Kubernetes"],
        "needs": ["scalable systems", "performance optimization"],
        "results": ["improved efficiency", "reduced costs"]
    }

    sample_jd = "We are hiring a senior engineer to build AI-driven products using Python, TypeScript, Kubernetes, and GCP."

    result = tailor.tailor_resume(sample_resume, sample_keywords, sample_jd)
    print("Test Result Keys:", list(result.keys()))
    print("Keywords Inserted:", result.get('keyword_status', {}).get('successfully_inserted', []))
    tailor.save_tailored_resume(result)
