#!/usr/bin/env python3
"""
Tool 1: Keyword Extractor
Uses OpenAI API to extract keywords, needs, and results from Job Description
"""

import json
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KeywordExtractor:
    """Extract keywords from Job Description using OpenAI"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = "gpt-4o"  # Best OpenAI model

        self.system_prompt = self._load_prompt('tool1_prompt.txt')

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / 'prompt' / filename
        try:
            return prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Prompt file '{filename}' is missing in {prompt_path.parent}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unable to load prompt '{filename}': {exc}") from exc
    
    def extract_keywords(self, job_description):
        """
        Extract keywords from job description using Claude

        Args:
            job_description (str): The job description text

        Returns:
            dict: Contains keywords, needs, and results
        """

        print("🤖 Analyzing Job Description with GPT-4o...")

        try:
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Please analyze this Job Description:\n\n{job_description}"}
                ]
            )

            # Extract the response
            analysis = response.choices[0].message.content

            print("✅ GPT-4o analysis complete!")
            
            # Parse the response (you might want to improve this parsing)
            parsed_result = self._parse_openai_response(analysis)
            
            return parsed_result
            
        except Exception as e:
            print(f"❌ Error calling OpenAI: {e}")
            # Return fallback result
            return {
                "company_name": "UNKNOWN_COMPANY",
                "keywords": ["Error occurred during keyword extraction"],
                "needs": ["Please check OpenAI API key and connection"],
                "results": ["Manual keyword extraction may be needed"],
                "raw_analysis": f"Error: {str(e)}"
            }
    
    def _parse_openai_response(self, analysis):
        """Parse OpenAI response into structured format."""
        result = {
            "company_name": "UNKNOWN_COMPANY",
            "job_title": "",
            "keywords": [],
            "needs": [],
            "results": [],
            "raw_analysis": analysis,
        }

        try:
            _INVALID_NAMES = {'', 'N_A', 'NA', 'NONE', 'UNKNOWN', 'UNKNOWN_COMPANY',
                               'UNNAMED', 'UNNAMED_COMPANY', 'NOT_MENTIONED', 'NOT_PROVIDED',
                               'NOT_SPECIFIED', 'COMPANY_NAME', 'EXACT_COMPANY_NAME'}

            # --- Extract JSON block (handles single-line and multi-line output) ---
            json_block_match = re.search(r'\{.*?\}', analysis, re.DOTALL)
            raw_json_str = json_block_match.group(0) if json_block_match else ''
            print(f"[TOOL1 DEBUG] Raw JSON block from GPT-4o: {raw_json_str!r}")

            # Try json.loads first (most robust), fall back to regex
            meta = {}
            if raw_json_str:
                try:
                    meta = json.loads(raw_json_str)
                except json.JSONDecodeError:
                    # Fallback: simple key-value regex directly on full response
                    cn = re.search(r'"company_name"\s*:\s*"([^"]*)"', analysis)
                    jt = re.search(r'"job_title"\s*:\s*"([^"]*)"', analysis)
                    if cn:
                        meta['company_name'] = cn.group(1)
                    if jt:
                        meta['job_title'] = jt.group(1)

            raw_name = meta.get('company_name', '').strip()
            print(f"[TOOL1 DEBUG] Extracted company_name = {raw_name!r}")
            normalized = re.sub(r'[^A-Z0-9]', '_', raw_name.upper()).strip('_')
            if normalized and normalized not in _INVALID_NAMES:
                result['company_name'] = normalized

            raw_title = meta.get('job_title', '').strip()
            if raw_title:
                result['job_title'] = raw_title

            # --- Strip code fences and JSON block from body ---
            # Remove ```json ... ``` or ``` ... ``` fences
            clean_analysis = re.sub(r'```[a-z]*\s*', '', analysis, flags=re.IGNORECASE)
            clean_analysis = clean_analysis.replace('```', '')
            # Remove the JSON object itself (anywhere in the text, not just at start)
            clean_analysis = re.sub(r'\{[^{}]*"company_name"[^{}]*\}', '', clean_analysis, flags=re.DOTALL)
            # Strip markdown bold markers (**text** or __text__)
            clean_analysis = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', clean_analysis)
            clean_analysis = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', clean_analysis)
            body = clean_analysis.strip()

            # --- Normalize: if sections appear inline on one line, split them onto separate lines ---
            # e.g. "Keywords: a - b - c Needs: d - e Results: f - g"
            for section_header in ('Keywords:', 'Needs:', 'Results:'):
                body = re.sub(
                    r'(?<!\n)(' + re.escape(section_header) + r')',
                    r'\n\1',
                    body,
                    flags=re.IGNORECASE,
                )

            # --- Parse keyword / needs / results sections ---
            # Section header pattern: optional whitespace, optional *, then the word, then colon
            section_re = re.compile(
                r'^\s*\*{0,2}(keywords|needs|results)\*{0,2}\s*:(.*)$',
                re.IGNORECASE,
            )
            current_section = None
            for line in body.split('\n'):
                line = line.strip()
                if not line:
                    continue

                header_match = section_re.match(line)
                if header_match:
                    current_section = header_match.group(1).lower()
                    inline = header_match.group(2).strip()
                    if inline:
                        # inline may be "- item1 - item2" or "item1, item2"
                        self._parse_inline_items(inline, result[current_section])
                    continue

                # Skip markdown fence artifacts and bare JSON lines
                if re.match(r'^`{1,3}', line) or re.match(r'^\s*[{}\[\]]', line):
                    continue

                if current_section and current_section in result:
                    clean = line.lstrip('•-– ').strip()
                    if clean:
                        # If this line contains an embedded next-section header inline,
                        # split it and process the remainder as a new section
                        sub_match = re.search(
                            r'\*{0,2}(keywords|needs|results)\*{0,2}\s*:',
                            clean, re.IGNORECASE,
                        )
                        if sub_match:
                            before = clean[:sub_match.start()].strip().lstrip('•-– ').strip()
                            if before:
                                result[current_section].append(before)
                            current_section = sub_match.group(1).lower()
                            after = clean[sub_match.end():].strip()
                            if after:
                                self._parse_inline_items(after, result[current_section])
                        else:
                            result[current_section].append(clean)

            # Fallback if nothing parsed
            if not any(result[k] for k in ['keywords', 'needs', 'results']):
                sentences = [s.strip() for s in analysis.split('.') if s.strip()]
                result['keywords'] = sentences[:10]

        except Exception as e:
            print(f"⚠️  Warning: Could not parse OpenAI response - {e}")
            result['keywords'] = [analysis[:200]]

        return result
    
    def _parse_inline_items(self, text: str, target: list) -> None:
        """
        Parse a string that may contain items separated by ' - ', ',' or newlines
        and append cleaned items to target list.
        Examples handled:
          "- item1 - item2 - item3"
          "item1, item2, item3"
          "item1"
        """
        # Try dash-separated first (most common from GPT-4o inline output)
        if ' - ' in text or text.startswith('- '):
            parts = re.split(r'\s+-\s+', text.lstrip('- '))
        else:
            # Fall back to comma-separated
            parts = text.split(',')
        for part in parts:
            clean = part.strip().lstrip('•-– ').strip()
            if clean and not re.match(r'^`{1,3}', clean):
                target.append(clean)

    def save_analysis(self, analysis, filename="keyword_analysis.txt"):
        """Save the keyword analysis to text file and keyword_analysis.json."""
        try:
            output_dir = Path(__file__).resolve().parent.parent / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            # --- human-readable text file ---
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("KEYWORD EXTRACTION ANALYSIS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"COMPANY NAME: {analysis.get('company_name', 'UNKNOWN_COMPANY')}\n")
                f.write("=" * 50 + "\n\n")
                f.write("KEYWORDS:\n")
                for keyword in analysis.get('keywords', []):
                    f.write(f"• {keyword}\n")
                f.write("\nNEEDS:\n")
                for need in analysis.get('needs', []):
                    f.write(f"• {need}\n")
                f.write("\nRESULTS:\n")
                for result in analysis.get('results', []):
                    f.write(f"• {result}\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write("RAW ANALYSIS:\n")
                f.write(analysis.get('raw_analysis', ''))
            print(f"📁 Analysis saved to {filepath}")

            # --- machine-readable JSON (used by download endpoint for filename) ---
            json_path = output_dir / 'keyword_analysis.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "company_name": analysis.get('company_name', 'UNKNOWN_COMPANY'),
                    "job_title": analysis.get('job_title', ''),
                    "keywords": analysis.get('keywords', []),
                    "needs": analysis.get('needs', []),
                    "results": analysis.get('results', []),
                }, f, indent=2)
            print(f"📁 Analysis JSON saved to {json_path}")

        except Exception as e:
            print(f"⚠️  Warning: Could not save analysis - {e}")

# Test function
if __name__ == "__main__":
    # Test the keyword extractor
    extractor = KeywordExtractor()
    
    # Test with sample JD
    sample_jd = """
    We are seeking a Senior Software Engineer with 5+ years of experience in Python, React, and AWS.
    Responsibilities include developing scalable web applications, optimizing database performance,
    and collaborating with cross-functional teams. Required: Bachelor's degree in Computer Science,
    proficiency in SQL, experience with Docker and Kubernetes.
    """
    
    result = extractor.extract_keywords(sample_jd)
    print("Test Result:", result)
    extractor.save_analysis(result)

