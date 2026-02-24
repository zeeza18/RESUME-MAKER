#!/usr/bin/env python3
"""
Tool 2: Resume Tailor
Uses Anthropic Claude API to tailor resume based on JD keywords and feedback
"""

import json
import os
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResumeTailor:
    """Tailor resume based on JD keywords using Anthropic Claude"""

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
    
    def tailor_resume(self, original_resume, keywords, job_description, feedback=None, round_number=1):
        """
        Tailor resume based on JD keywords and optional feedback
        
        Args:
            original_resume (str): The resume content from the previous round or original submission\r\n            keywords (dict): Keywords from Tool 1 (contains keywords, needs, results)\r\n            job_description (str): Full job description text for context\r\n            feedback (str): Optional feedback from previous evaluation\r\n            round_number (int): Current iteration number (1 for the first pass)\r\n            
        Returns:
            dict: Contains tailored resume and change log
        """
        
        print("🎨 Tailoring Resume with Claude Sonnet...")

        # --- Personal info from config.json ---
        config = self._load_config()
        personal_block = ""
        if config:
            personal_block = (
                "CANDIDATE PERSONAL INFO — copy these values exactly into the resume header, do not alter them:\n"
                f"  Name:      {config.get('name', '')}\n"
                f"  Phone:     {config.get('phone', '')}\n"
                f"  Email:     {config.get('email', '')}\n"
                f"  LinkedIn:  {config.get('linkedin', '')}\n"
                f"  Portfolio: {config.get('portfolio', '')}\n"
                f"  GitHub:    {config.get('github', '')}\n"
                f"  Location:  {config.get('location', '')}\n\n"
            )

        # --- Count structural constraints from original resume ---
        bullet_markers = re.compile(r'^\s*[•\-–]\s', re.MULTILINE)
        total_bullets = len(bullet_markers.findall(original_resume))

        # Count projects: lines immediately after "PROJECTS" header up to next blank line or end
        project_header_pattern = re.compile(r'(?:^|\n)([\w\s\-|]+)\n\s*[•\-–]', re.MULTILINE)
        projects_section_match = re.search(r'(?i)PROJECTS?\s*\n(.*)', original_resume, re.DOTALL)
        project_count = 0
        if projects_section_match:
            projects_text = projects_section_match.group(1)
            # Each project starts with a non-bullet line followed by bullets
            project_count = len(re.findall(r'(?:^|\n)([^\n•\-–][^\n]+)\n\s*[•\-–]', projects_text))

        # --- Per-block bullet word limits ---
        block_limits = self._compute_per_block_word_limits(original_resume)
        block_limit_lines = ""
        if block_limits:
            block_limit_lines = (
                "  • Per-block bullet word limits — count words before submitting:\n"
                + "\n".join(
                    f'      "{header[:60]}" → {bullet_count} bullets → max {word_limit} words/bullet'
                    for header, bullet_count, word_limit in block_limits
                )
                + "\n    KEYWORD RULE: never drop a JD keyword to hit the word limit — if a bullet exceeds the limit, shorten filler words, not keywords.\n"
            )

        structural_constraints = (
            f"STRUCTURAL CONSTRAINTS — you MUST satisfy all of these or the output is invalid:\n"
            f"  • Total bullets in output: exactly {total_bullets} (count yours before submitting)\n"
            f"  • Projects count: exactly {project_count} projects — do NOT remove or merge any\n"
            f"  • Every project must keep ALL its original bullets\n"
            f"  • Section order must match the original resume exactly\n"
            f"{block_limit_lines}\n"
        )

        # --- Build user message ---
        round_label = f"Round {round_number}" if round_number else "Current Round"
        previous_round_label = "original submission" if not round_number or round_number <= 1 else f"Round {round_number - 1} output"

        keywords_snapshot = "\n".join([
            f"Keywords: {', '.join([k for k in keywords.get('keywords', []) if k]) or 'None provided'}",
            f"Needs: {', '.join([k for k in keywords.get('needs', []) if k]) or 'None provided'}",
            f"Results: {', '.join([k for k in keywords.get('results', []) if k]) or 'None provided'}",
        ])

        user_message = (
            f"{round_label} keyword insertion task. Insert missing JD keywords into the resume below. Do not rewrite anything else.\n\n"
            f"{personal_block}"
            f"{structural_constraints}"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"PREVIOUS RESUME ({previous_round_label.upper()}):\n{original_resume}\n\n"
            f"JD KEYWORD SNAPSHOT:\n{keywords_snapshot}\n"
        )

        if feedback:
            previous_round_number = round_number - 1 if round_number and round_number > 1 else 1
            user_message += (
                f"\nEVALUATION FEEDBACK FROM ROUND {previous_round_number}:\n"
                f"{feedback}\n"
            )

        user_message += "\nInsert the missing keywords listed above into the resume. Copy every other word exactly. Output the full resume then the change log."

        prompt_key = 'round1' if not round_number or round_number <= 1 else 'evaluation'
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
            tailored_content = response.content[0].text

            print("✅ Resume tailoring complete!")

            # Parse the response to separate resume and change log
            parsed_result = self._parse_tailoring_response(tailored_content)

            return parsed_result

        except Exception as e:
            print(f"❌ Error calling Claude for resume tailoring: {e}")
            # Return fallback result
            return {
                "tailored_resume": original_resume,
                "change_log": [f"Error occurred during tailoring: {str(e)}"],
            }
    
    def _compute_per_block_word_limits(self, resume_text: str) -> list:
        """
        Parse the resume into individual blocks (each experience entry or project).
        A block = a non-bullet header line followed by one or more bullet lines.
        Word limit rule:
          block has > 4 bullets  → 22 words max per bullet
          block has <= 4 bullets → 28 words max per bullet
        Returns list of (header_str, bullet_count, word_limit).
        """
        bullet_re = re.compile(r'^\s*[•\-–]\s')
        # Section headers to skip (they are not individual exp/project entries)
        section_re = re.compile(
            r'^\s*(EXPERIENCE|EDUCATION|PROJECTS?|SKILLS?|SUMMARY|CERTIFICATIONS?|AWARDS?|PUBLICATIONS?|VOLUNTEERING?)\s*$',
            re.IGNORECASE,
        )

        blocks = []
        current_header = None
        current_bullets = 0

        for line in resume_text.splitlines():
            stripped = line.strip()
            if not stripped:
                if current_header is not None and current_bullets > 0:
                    blocks.append((current_header, current_bullets))
                current_header = None
                current_bullets = 0
            elif bullet_re.match(line):
                if current_header is not None:
                    current_bullets += 1
            else:
                # Non-bullet, non-empty line
                if current_header is not None and current_bullets > 0:
                    blocks.append((current_header, current_bullets))
                if not section_re.match(stripped):
                    current_header = stripped
                    current_bullets = 0
                else:
                    current_header = None
                    current_bullets = 0

        # Flush last block
        if current_header is not None and current_bullets > 0:
            blocks.append((current_header, current_bullets))

        return [
            (header, count, 22 if count > 4 else 28)
            for header, count in blocks
        ]

    def _strip_fences(self, text: str) -> str:
        """Remove markdown code-block fences GPT-4o sometimes wraps output in."""
        # Strip leading/trailing ``` fences (with optional language tag)
        text = re.sub(r'^```[a-z]*\n?', '', text.strip(), flags=re.IGNORECASE)
        text = re.sub(r'\n?```$', '', text.strip())
        return text.strip()

    def _parse_tailoring_response(self, response):
        """
        Parse OpenAI response to extract tailored resume and change log.
        Strips markdown fences and handles any Change Log header variant.
        """
        try:
            # Strip outer markdown code fences first
            clean = self._strip_fences(response)

            # Match the change log section header (flexible casing/markdown)
            change_log_pattern = re.compile(
                r'(?:^|\n)((?:#+\s*|\*{1,2})?(?:Change\s+Log|CHANGE\s+LOG|Changes\s+Made|CHANGES\s+MADE)(?:\*{0,2}):?)',
                re.IGNORECASE,
            )
            match = change_log_pattern.search(clean)

            if match:
                split_idx = match.start()
                tailored_resume = clean[:split_idx].strip()
                change_log_text = clean[split_idx:].strip()
            else:
                tailored_resume = clean
                change_log_text = "No change log provided"

            # Strip any fence that crept into the resume section only
            tailored_resume = self._strip_fences(tailored_resume)

            # Extract individual change log bullet items
            change_log = []
            for line in change_log_text.split('\n'):
                line = line.strip()
                if line and (
                    line.startswith('✅') or line.startswith('⚠️') or
                    line.startswith('🌀') or line.startswith('-') or
                    line.startswith('•')
                ):
                    change_log.append(line)

            return {
                "tailored_resume": tailored_resume,
                "change_log": change_log,
            }

        except Exception as e:
            print(f"⚠️  Warning: Could not parse tailoring response - {e}")
            return {
                "tailored_resume": self._strip_fences(response),
                "change_log": [f"Parsing error: {str(e)}"],
            }
    
    def save_tailored_resume(self, tailored_data, filename="tailored_resume.txt"):
        """Save the tailored resume and change log to file"""
        try:
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("TAILORED RESUME\n")
                f.write("=" * 50 + "\n\n")
                f.write(tailored_data.get('tailored_resume', ''))
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("CHANGE LOG\n")
                f.write("=" * 50 + "\n")
                for change in tailored_data.get('change_log', []):
                    f.write(f"{change}\n")

            print(f"📁 Tailored resume saved to {filepath}")

        except Exception as e:
            print(f"⚠️  Warning: Could not save tailored resume - {e}")

# Test function
if __name__ == "__main__":
    # Test the resume tailor
    tailor = ResumeTailor()
    
    # Test with sample data
    sample_resume = """
    John Doe
    Software Engineer
    
    Experience:
    ABC Company — New York | 2022-2024
    • Built web applications using Python and React
    • Improved system performance by 50%
    """
    
    sample_keywords = {
        "keywords": ["Python", "React", "TypeScript", "async programming"],
        "needs": ["scalable systems", "performance optimization"],
        "results": ["improved efficiency", "reduced costs"]
    }
    
    sample_job_description = """We are hiring a senior engineer to build AI-driven products using Python, TypeScript, and cloud-native tooling."""

    result = tailor.tailor_resume(sample_resume, sample_keywords, sample_job_description)
    print("Test Result:", result)
    tailor.save_tailored_resume(result)





