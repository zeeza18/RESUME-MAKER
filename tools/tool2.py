#!/usr/bin/env python3
"""
Tool 2: Resume Tailor
Uses Claude API to tailor resume based on JD keywords and feedback
"""

import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResumeTailor:
    """Tailor resume based on JD keywords using Claude"""

    def __init__(self):
        """Initialize Claude client"""
        self.client = anthropic.Anthropic(
            api_key=os.getenv('CLAUDE_API_KEY')
        )
        self.model = "claude-opus-4-5-20251101"  # Best Claude model

        self.prompts = {
            'round1': self._load_prompt('tool2_prompt.txt'),
            'evaluation': self._load_prompt('tool2_eval_prompt.txt')
        }

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
        
        print("🎨 Tailoring Resume with Claude Opus 4.5...")

        # Prepare the user message with full context for this round
        round_label = f"Round {round_number}" if round_number else "Current Round"
        previous_round_label = "original submission" if not round_number or round_number <= 1 else f"Round {round_number - 1} output"

        keywords_snapshot = "\n".join([
            f"Keywords: {', '.join([k for k in keywords.get('keywords', []) if k]) or 'None provided'}",
            f"Needs: {', '.join([k for k in keywords.get('needs', []) if k]) or 'None provided'}",
            f"Results: {', '.join([k for k in keywords.get('results', []) if k]) or 'None provided'}",
        ])

        user_message = (
            f"{round_label} tailoring context. Use everything below to deliver an improved resume.\n\n"
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

        user_message += "\nProduce the next-round resume and include a concise change log summarizing adjustments."

        prompt_key = 'round1' if not round_number or round_number <= 1 else 'evaluation'
        system_prompt = self.prompts[prompt_key]

        try:
            # Make API call to Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
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
                "tailored_resume": original_resume,  # Return original if error
                "change_log": [f"Error occurred during tailoring: {str(e)}"],
                "raw_response": f"Error: {str(e)}"
            }
    
    def _parse_tailoring_response(self, response):
        """
        Parse OpenAI response to extract tailored resume and change log
        
        Args:
            response (str): Raw response from OpenAI
            
        Returns:
            dict: Structured tailored resume and change log
        """
        
        try:
            # Look for change log section
            if "Change Log" in response or "✅" in response:
                # Split at change log indicators
                parts = response.split("Change Log")
                if len(parts) == 2:
                    tailored_resume = parts[0].strip()
                    change_log_text = parts[1].strip()
                else:
                    # Try other indicators
                    for indicator in ["✅ What keywords", "CHANGE LOG", "📝 Changes Made"]:
                        if indicator in response:
                            parts = response.split(indicator)
                            tailored_resume = parts[0].strip()
                            change_log_text = indicator + parts[1].strip()
                            break
                    else:
                        # No clear separator found
                        tailored_resume = response
                        change_log_text = "Could not parse change log"
            else:
                # No change log found
                tailored_resume = response
                change_log_text = "No change log provided"
            
            # Extract change log items
            change_log = []
            for line in change_log_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('✅') or line.startswith('⚠️') or line.startswith('🌀') or line.startswith('-')):
                    change_log.append(line)
            
            return {
                "tailored_resume": tailored_resume,
                "change_log": change_log,
                "raw_response": response
            }
            
        except Exception as e:
            print(f"⚠️  Warning: Could not parse tailoring response - {e}")
            return {
                "tailored_resume": response,  # Return full response as resume
                "change_log": [f"Parsing error: {str(e)}"],
                "raw_response": response
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
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("RAW RESPONSE\n")
                f.write("=" * 50 + "\n")
                f.write(tailored_data.get('raw_response', ''))
            
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





