#!/usr/bin/env python3
"""Tool 3: Resume Evaluator with Original Detailed Prompt"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Dict, List

import openai
from dotenv import load_dotenv

load_dotenv()


class ResumeEvaluator:
    """Evaluate tailored resume against JD requirements using OpenAI"""
    
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = openai.OpenAI(api_key=api_key)
        
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

        print("Evaluating resume with OpenAI...")

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
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=2500,
                temperature=0.3,
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
        """Parse OpenAI evaluation response into structured format"""
        
        try:
            result = {
                "score": 0,
                "keyword_analysis": {"found": [], "missing": [], "weak": []},
                "experience_evaluation": "",
                "ats_optimization": "",
                "requirements_check": {"met": [], "missing": [], "partial": []},
                "feedback": "",
                "recommendations": [],
                "raw_evaluation": response
            }
            
            # Extract score
            lines = response.split('\n')
            for line in lines:
                if 'SCORE:' in line.upper() or '/100' in line:
                    score_match = re.search(r'(\d+)(?:/100)?', line)
                    if score_match:
                        result["score"] = int(score_match.group(1))
                    break
            
            # Extract sections
            current_section = None
            section_content = []
            
            for line in lines:
                line = line.strip()
                
                if 'KEYWORD ANALYSIS' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'keyword_analysis_text'
                    section_content = []
                elif 'EXPERIENCE EVALUATION' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'experience_evaluation'
                    section_content = []
                elif 'ATS OPTIMIZATION' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'ats_optimization'
                    section_content = []
                elif 'REQUIREMENTS CHECK' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'requirements_text'
                    section_content = []
                elif 'IMPROVEMENT FEEDBACK' in line.upper() or 'FEEDBACK' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'feedback'
                    section_content = []
                elif 'RECOMMENDATIONS' in line.upper():
                    if current_section:
                        result[current_section] = '\n'.join(section_content)
                    current_section = 'recommendations_text'
                    section_content = []
                elif current_section and line:
                    section_content.append(line)
            
            # Add final section
            if current_section and section_content:
                result[current_section] = '\n'.join(section_content)
            
            # Parse keyword analysis
            if 'keyword_analysis_text' in result:
                keyword_text = result['keyword_analysis_text']
                
                # Try bracket format first
                found_match = re.search(r'Keywords Found:\s*\[(.*?)\]', keyword_text, re.IGNORECASE | re.DOTALL)
                if found_match:
                    found_keywords = [k.strip() for k in found_match.group(1).split(',') if k.strip() and k.strip().lower() != 'none']
                    result["keyword_analysis"]["found"] = found_keywords
                
                missing_match = re.search(r'Missing Keywords:\s*\[(.*?)\]', keyword_text, re.IGNORECASE | re.DOTALL)
                if missing_match:
                    missing_keywords = [k.strip() for k in missing_match.group(1).split(',') if k.strip() and k.strip().lower() != 'none']
                    result["keyword_analysis"]["missing"] = missing_keywords
                
                weak_match = re.search(r'Weak Keywords:\s*\[(.*?)\]', keyword_text, re.IGNORECASE | re.DOTALL)
                if weak_match:
                    weak_keywords = [k.strip() for k in weak_match.group(1).split(',') if k.strip() and k.strip().lower() != 'none']
                    result["keyword_analysis"]["weak"] = weak_keywords
                
                # Alternative: colon-separated format
                if not any([found_match, missing_match, weak_match]):
                    for line in keyword_text.split('\n'):
                        line = line.strip()
                        if 'keywords found' in line.lower() and ':' in line:
                            keywords_part = line.split(':', 1)[1].strip()
                            keywords = [k.strip() for k in keywords_part.split(',') if k.strip() and k.strip().lower() != 'none']
                            result["keyword_analysis"]["found"] = keywords
                        elif 'missing keywords' in line.lower() and ':' in line:
                            keywords_part = line.split(':', 1)[1].strip()
                            keywords = [k.strip() for k in keywords_part.split(',') if k.strip() and k.strip().lower() != 'none']
                            result["keyword_analysis"]["missing"] = keywords
                        elif 'weak keywords' in line.lower() and ':' in line:
                            keywords_part = line.split(':', 1)[1].strip()
                            keywords = [k.strip() for k in keywords_part.split(',') if k.strip() and k.strip().lower() != 'none']
                            result["keyword_analysis"]["weak"] = keywords
            
            # Parse requirements check
            if 'requirements_text' in result:
                req_text = result['requirements_text']
                
                met_match = re.search(r'Met Requirements:\s*\[(.*?)\]', req_text, re.IGNORECASE | re.DOTALL)
                if met_match:
                    met_reqs = [r.strip() for r in met_match.group(1).split(',') if r.strip() and r.strip().lower() != 'none']
                    result["requirements_check"]["met"] = met_reqs
                
                missing_req_match = re.search(r'Missing Requirements:\s*\[(.*?)\]', req_text, re.IGNORECASE | re.DOTALL)
                if missing_req_match:
                    missing_reqs = [r.strip() for r in missing_req_match.group(1).split(',') if r.strip() and r.strip().lower() != 'none']
                    result["requirements_check"]["missing"] = missing_reqs
                
                partial_match = re.search(r'Partially Met:\s*\[(.*?)\]', req_text, re.IGNORECASE | re.DOTALL)
                if partial_match:
                    partial_reqs = [r.strip() for r in partial_match.group(1).split(',') if r.strip() and r.strip().lower() != 'none']
                    result["requirements_check"]["partial"] = partial_reqs
            
            # Parse recommendations
            if 'recommendations_text' in result:
                rec_text = result['recommendations_text']
                recommendations = []
                for line in rec_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                        clean_rec = re.sub(r'^[-•\d.]+\s*', '', line).strip()
                        if clean_rec:
                            recommendations.append(clean_rec)
                result['recommendations'] = recommendations
            
            return result
            
        except Exception as e:
            print(f"Warning: Could not parse evaluation response - {e}")
            return {
                "score": 0,
                "keyword_analysis": {"found": [], "missing": [], "weak": []},
                "experience_evaluation": response,
                "ats_optimization": "Parsing error occurred",
                "requirements_check": {"met": [], "missing": [], "partial": []},
                "feedback": "Could not parse structured feedback",
                "recommendations": ["Please check raw evaluation for details"],
                "raw_evaluation": response
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
                
                f.write("KEYWORD ANALYSIS:\n")
                f.write("-" * 30 + "\n")
                ka = evaluation_data.get('keyword_analysis', {})
                f.write(f"Found: {', '.join(ka.get('found', []))}\n")
                f.write(f"Missing: {', '.join(ka.get('missing', []))}\n")
                f.write(f"Weak: {', '.join(ka.get('weak', []))}\n\n")
                
                f.write("EXPERIENCE EVALUATION:\n")
                f.write("-" * 30 + "\n")
                f.write(evaluation_data.get('experience_evaluation', 'No experience evaluation available') + "\n\n")
                
                f.write("ATS OPTIMIZATION:\n")
                f.write("-" * 30 + "\n")
                f.write(evaluation_data.get('ats_optimization', 'No ATS analysis available') + "\n\n")
                
                f.write("IMPROVEMENT FEEDBACK:\n")
                f.write("-" * 30 + "\n")
                f.write(evaluation_data.get('feedback', 'No feedback available') + "\n\n")
                
                f.write("RECOMMENDATIONS:\n")
                f.write("-" * 30 + "\n")
                for i, rec in enumerate(evaluation_data.get('recommendations', []), 1):
                    f.write(f"{i}. {rec}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("RAW EVALUATION:\n")
                f.write("=" * 50 + "\n")
                f.write(evaluation_data.get('raw_evaluation', ''))
            
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

