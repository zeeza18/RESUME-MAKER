#!/usr/bin/env python3
"""
Tool 1: Keyword Extractor
Uses Claude API to extract keywords, needs, and results from Job Description
"""

import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KeywordExtractor:
    """Extract keywords from Job Description using Claude"""

    def __init__(self):
        """Initialize Claude client"""
        self.client = anthropic.Anthropic(
            api_key=os.getenv('CLAUDE_API_KEY')
        )
        self.model = "claude-opus-4-5-20251101"  # Best Claude model

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

        print("🤖 Analyzing Job Description with Claude Opus 4.5...")

        try:
            # Make API call to Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": f"Please analyze this Job Description:\n\n{job_description}"}
                ]
            )

            # Extract the response
            analysis = response.content[0].text

            print("✅ Claude analysis complete!")
            
            # Parse the response (you might want to improve this parsing)
            parsed_result = self._parse_openai_response(analysis)
            
            return parsed_result
            
        except Exception as e:
            print(f"❌ Error calling Claude: {e}")
            # Return fallback result
            return {
                "keywords": ["Error occurred during keyword extraction"],
                "needs": ["Please check Claude API key and connection"],
                "results": ["Manual keyword extraction may be needed"],
                "raw_analysis": f"Error: {str(e)}"
            }
    
    def _parse_openai_response(self, analysis):
        """
        Parse OpenAI response into structured format
        
        Args:
            analysis (str): Raw response from OpenAI
            
        Returns:
            dict: Structured keywords, needs, and results
        """
        
        # Initialize default structure
        result = {
            "keywords": [],
            "needs": [],
            "results": [],
            "raw_analysis": analysis
        }
        
        try:
            # Split response into sections
            lines = analysis.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # Detect section headers
                if line.lower().startswith('keywords:') or 'keywords' in line.lower():
                    current_section = 'keywords'
                    continue
                elif line.lower().startswith('needs:') or 'needs' in line.lower():
                    current_section = 'needs'
                    continue
                elif line.lower().startswith('results:') or 'results' in line.lower():
                    current_section = 'results'
                    continue
                
                # Add content to current section
                if line and current_section and not line.startswith('#'):
                    # Remove bullet points and clean up
                    clean_line = line.replace('•', '').replace('-', '').replace('*', '').strip()
                    if clean_line:
                        result[current_section].append(clean_line)
            
            # If parsing didn't work well, fall back to simple split
            if not any(result[key] for key in ['keywords', 'needs', 'results']):
                # Just split by sentences as keywords
                sentences = [s.strip() for s in analysis.split('.') if s.strip()]
                result['keywords'] = sentences[:10]  # Take first 10 as keywords
                result['needs'] = ["Manual parsing needed"]
                result['results'] = ["Manual parsing needed"]
            
        except Exception as e:
            print(f"⚠️  Warning: Could not parse Claude response - {e}")
            # Fallback: use the raw response as keywords
            result['keywords'] = [analysis[:200]]  # First 200 chars as single keyword
            result['needs'] = ["Parsing error occurred"]
            result['results'] = ["Please check raw_analysis"]
        
        return result
    
    def save_analysis(self, analysis, filename="keyword_analysis.txt"):
        """Save the keyword analysis to file"""
        try:
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("KEYWORD EXTRACTION ANALYSIS\n")
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

