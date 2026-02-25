#!/usr/bin/env python3
"""Tool 3: Resume Evaluator with Original Detailed Prompt"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Dict, List

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ResumeEvaluator:
    """Evaluate tailored resume against JD requirements using OpenAI"""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # GPT-4o for evaluation

        self.system_prompt = self._load_prompt('tool3_prompt.txt')

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / 'prompt' / filename
        try:
            return prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Prompt file '{filename}' is missing in {prompt_path.parent}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unable to load prompt '{filename}': {exc}") from exc

    def evaluate_resume(
        self,
        job_description: str,
        tailored_resume: str,
        keywords: Dict[str, List[str]],
    ) -> Dict[str, object]:
        """Call OpenAI to evaluate the resume and return structured result"""

        print("Evaluating resume with GPT-4o...")

        user_message = f"""Please evaluate this tailored resume against the job description:

JOB DESCRIPTION:
{job_description}

TAILORED RESUME:
{tailored_resume}

REFERENCE KEYWORDS (from Tool 1):
Keywords: {', '.join(keywords.get('keywords', []))}
Needs: {', '.join(keywords.get('needs', []))}
Results: {', '.join(keywords.get('results', []))}

Please provide a comprehensive evaluation with specific feedback for improvement."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            evaluation_content = response.choices[0].message.content
            print("Resume evaluation complete.")
            return self._parse_evaluation_response(evaluation_content)

        except Exception as exc:
            print(f"Error calling OpenAI for resume evaluation: {exc}")
            return {
                "score": 0,
                "keyword_analysis": {"found": [], "missing": [], "weak": []},
                "experience_evaluation": f"Error occurred during evaluation: {str(exc)}",
                "ats_optimization": "Could not evaluate due to error",
                "requirements_check": {"met": [], "missing": [], "partial": []},
                "feedback": f"Evaluation failed due to error: {str(exc)}",
                "recommendations": ["Please check OpenAI API connection and try again"],
                "raw_evaluation": f"Error: {str(exc)}"
            }

    def _parse_evaluation_response(self, response: str) -> Dict[str, object]:
        """Parse the compact evaluation format produced by tool3_prompt.txt."""
        try:
            result = {
                "score": 0,
                "keyword_analysis": {"found": [], "missing": [], "weak": [], "orphaned": []},
                "feedback": "",
                "recommendations": [],
                "raw_evaluation": response,
            }

            # Score
            score_match = re.search(r'SCORE:\s*(\d+)', response, re.IGNORECASE)
            if score_match:
                result["score"] = int(score_match.group(1))

            # MISSING KEYWORDS section
            missing_block = re.search(
                r'MISSING KEYWORDS:\n(.*?)(?=\nWEAK KEYWORDS|\nORPHANED SKILLS|\nGENUINE GAPS|\nACTION ITEMS|$)',
                response, re.DOTALL | re.IGNORECASE,
            )
            if missing_block:
                for line in missing_block.group(1).splitlines():
                    line = line.strip().lstrip('- ')
                    if line:
                        result["keyword_analysis"]["missing"].append(line)

            # WEAK KEYWORDS section
            weak_block = re.search(
                r'WEAK KEYWORDS:\n(.*?)(?=\nORPHANED SKILLS|\nGENUINE GAPS|\nACTION ITEMS|$)',
                response, re.DOTALL | re.IGNORECASE,
            )
            if weak_block:
                for line in weak_block.group(1).splitlines():
                    line = line.strip().lstrip('- ')
                    if line:
                        result["keyword_analysis"]["weak"].append(line)

            # ORPHANED SKILLS section (skills in Skills but not in Experience/Projects)
            orphaned_block = re.search(
                r'ORPHANED SKILLS.*?:\n(.*?)(?=\nGENUINE GAPS|\nACTION ITEMS|$)',
                response, re.DOTALL | re.IGNORECASE,
            )
            if orphaned_block:
                for line in orphaned_block.group(1).splitlines():
                    line = line.strip().lstrip('- ')
                    if line:
                        result["keyword_analysis"]["orphaned"].append(line)

            # GENUINE GAPS → feedback field (passed to next round)
            gaps_block = re.search(
                r'GENUINE GAPS.*?:\n(.*?)(?=\nACTION ITEMS|$)',
                response, re.DOTALL | re.IGNORECASE,
            )
            if gaps_block:
                result["feedback"] = gaps_block.group(1).strip()

            # ACTION ITEMS → recommendations field (also passed to next round)
            actions_block = re.search(
                r'ACTION ITEMS.*?:\n(.*?)(?=\nIMPORTANT FOR NEXT|$)',
                response, re.DOTALL | re.IGNORECASE,
            )
            if actions_block:
                for line in actions_block.group(1).splitlines():
                    line = line.strip()
                    if line:
                        clean = re.sub(r'^\d+\.\s*', '', line).strip()
                        if clean:
                            result["recommendations"].append(clean)

            return result

        except Exception as e:
            print(f"Warning: Could not parse evaluation response - {e}")
            return {
                "score": 0,
                "keyword_analysis": {"found": [], "missing": [], "weak": []},
                "feedback": response,
                "recommendations": [],
                "raw_evaluation": response,
            }

    def save_evaluation(self, evaluation_data: Dict[str, object], filename: str = "resume_evaluation.txt") -> None:
        """Save the evaluation results to file"""
        try:
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("RESUME EVALUATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"OVERALL SCORE: {evaluation_data.get('score', 0)}/100\n\n")

                ka = evaluation_data.get('keyword_analysis', {})

                f.write("MISSING KEYWORDS:\n")
                f.write("-" * 30 + "\n")
                for item in ka.get('missing', []):
                    f.write(f"- {item}\n")
                f.write("\n")

                f.write("WEAK KEYWORDS:\n")
                f.write("-" * 30 + "\n")
                for item in ka.get('weak', []):
                    f.write(f"- {item}\n")
                f.write("\n")

                f.write("ORPHANED SKILLS (in Skills but not in Experience):\n")
                f.write("-" * 30 + "\n")
                for item in ka.get('orphaned', []):
                    f.write(f"- {item}\n")
                f.write("\n")

                f.write("GENUINE GAPS:\n")
                f.write("-" * 30 + "\n")
                f.write(evaluation_data.get('feedback', 'None') + "\n\n")

                f.write("ACTION ITEMS:\n")
                f.write("-" * 30 + "\n")
                for i, rec in enumerate(evaluation_data.get('recommendations', []), 1):
                    f.write(f"{i}. {rec}\n")

            print(f"Evaluation report saved to {filepath}")

        except Exception as e:
            print(f"Warning: Could not save evaluation report - {e}")


if __name__ == "__main__":
    evaluator = ResumeEvaluator()
    sample_jd = "We need a Senior Software Engineer with Python, React, and AWS experience."
    sample_resume = "Built ML models in Python and deployed to AWS with React frontend."
    sample_keywords = {
        "keywords": ["Python", "AWS", "React"],
        "needs": ["deployment", "cloud"],
        "results": ["improved accuracy"],
    }
    output = evaluator.evaluate_resume(sample_jd, sample_resume, sample_keywords)
    print(f"Score: {output['score']}/100")
    print(f"Keywords Found: {output['keyword_analysis']['found']}")
    print(f"Keywords Missing: {output['keyword_analysis']['missing']}")
    evaluator.save_evaluation(output)

