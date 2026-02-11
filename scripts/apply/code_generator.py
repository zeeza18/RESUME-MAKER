"""Claude API for generating Playwright automation code."""

import os
from typing import Dict, Any, Optional

try:
    import anthropic
except ImportError:
    anthropic = None


class CodeGenerator:
    """Uses Claude to generate Playwright code for form filling."""

    def __init__(self):
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")

        if anthropic is None:
            raise ImportError("anthropic not installed. Run: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"  # Use Sonnet for code generation (fast + capable)

    def generate_form_code(
        self,
        page_analysis: Dict[str, Any],
        form_data: Dict[str, str],
        previous_error: Optional[str] = None,
        resume_text: str = "",
    ) -> str:
        """
        Generate Playwright code to fill and submit a form.

        Args:
            page_analysis: Analysis from VisionAnalyzer
            form_data: Dictionary of field_type -> value to fill
            previous_error: If retrying, the previous error message
            resume_text: Full resume text for answering open-ended questions
        """

        error_context = ""
        if previous_error:
            error_context = f"""

PREVIOUS ATTEMPT FAILED with error:
{previous_error}

Please generate corrected code that avoids this error. Try alternative selectors or approaches."""

        resume_context = ""
        if resume_text:
            resume_context = f"""

CANDIDATE RESUME (use this to answer any open-ended questions on the form):
{resume_text[:3000]}"""

        prompt = f"""Generate Playwright Python async code to fill this job application form.

PAGE ANALYSIS:
{page_analysis}

FORM DATA TO FILL:
{form_data}

CREDENTIALS:
- Email: mohammedazeezulla6996@gmail.com
- For any password fields, use the value from form_data if available
{resume_context}
{error_context}

REQUIREMENTS:
1. Use async/await syntax (the code will run with 'await')
2. Use robust selectors - try multiple fallbacks
3. Add appropriate waits between actions
4. Handle potential pop-ups or overlays
5. The page object is available as 'page'
6. Include error handling with try/except
7. After filling, attempt to click the submit/next button
8. For file upload fields, use page.set_input_files() with the resume_path from form_data if available

Generate ONLY the Python code, no explanations or markdown. The code should be ready to exec() directly.
Start with the actual code, no function definitions needed - just the executable statements.

Example format:
await page.wait_for_selector('input[type="email"]', timeout=5000)
await page.fill('input[type="email"]', 'mohammedazeezulla6996@gmail.com')
# ... more actions"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text.strip()

        # Clean up code if wrapped in markdown
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        return code

    def generate_login_code(
        self,
        page_analysis: Dict[str, Any],
        email: str,
        password: str,
        previous_error: Optional[str] = None
    ) -> str:
        """Generate Playwright code for login/signup."""

        error_context = ""
        if previous_error:
            error_context = f"""

PREVIOUS ATTEMPT FAILED with error:
{previous_error}

Please generate corrected code that avoids this error."""

        prompt = f"""Generate Playwright Python async code to login/signup on this job application site.

PAGE ANALYSIS:
{page_analysis}

CREDENTIALS:
Email: {email}
Password: {password}
{error_context}

REQUIREMENTS:
1. Use async/await syntax
2. Try multiple selector strategies for email/password fields
3. Handle both login and signup scenarios
4. Look for and click the appropriate submit button
5. Wait for navigation after submission
6. The page object is available as 'page'

Generate ONLY executable Python code, no explanations."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text.strip()
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        return code

    def generate_navigation_code(
        self,
        page_analysis: Dict[str, Any],
        target_action: str,
        previous_error: Optional[str] = None
    ) -> str:
        """Generate code to navigate to specific action (next page, upload, etc.)."""

        error_context = ""
        if previous_error:
            error_context = f"\n\nPREVIOUS ERROR: {previous_error}"

        prompt = f"""Generate Playwright Python async code to: {target_action}

PAGE ANALYSIS:
{page_analysis}
{error_context}

Generate ONLY executable Python async code. The page object is available as 'page'."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text.strip()
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        return code

    def answer_question(self, question: str, resume_context: str, script_answers: Dict[str, str]) -> str:
        """Generate an answer for an unknown application question."""

        # Check if we have a scripted answer
        question_lower = question.lower()
        for key, answer in script_answers.items():
            if key.lower() in question_lower:
                return answer

        # Generate answer using Claude
        prompt = f"""You are filling out a job application. Answer this question naturally and professionally.

QUESTION: {question}

RESUME CONTEXT:
{resume_context}

Provide a concise, professional answer (1-3 sentences unless more is clearly needed).
Match the tone to the question type (formal for professional questions, friendly for casual ones).
If it's a personal preference question (hobbies, interests), give a genuine-sounding answer.

Return ONLY the answer text, nothing else."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()
