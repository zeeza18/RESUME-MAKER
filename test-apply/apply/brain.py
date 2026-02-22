"""
Universal OpenAI-powered automation brain.
Maintains conversation history and generates Playwright code dynamically.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class UniversalBrain:
    """
    Universal OpenAI brain that:
    - Maintains conversation history (memory)
    - Receives full page extraction
    - Generates Playwright code for any action
    - Handles cookies/policies automatically
    - Has creative liberty for open-ended questions
    """

    def __init__(self, logger, config):
        """Initialize the brain."""
        self.logger = logger
        self.config = config
        self.api_key = self._load_api_key()
        self.client = None
        self.conversation_history = []  # Memory of what's been done

        if self.api_key:
            self._initialize_client()
        else:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env")

    def _load_api_key(self) -> Optional[str]:
        """Load OpenAI API key from .env file."""
        current_env = Path(__file__).parent.parent / ".env"
        parent_env = Path(__file__).parent.parent.parent / ".env"

        # Load from parent first (if exists)
        if parent_env.exists():
            from dotenv import load_dotenv
            load_dotenv(parent_env)

        # Load from current directory (if exists) - this will override parent
        if current_env.exists():
            from dotenv import load_dotenv
            load_dotenv(current_env)

        api_key = os.getenv('OPENAI_API_KEY')

        if api_key:
            self.logger.info("OK OpenAI API key loaded")
            return api_key
        else:
            self.logger.error("X OpenAI API key not found in environment")
            return None

    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("OK OpenAI API client initialized")
        except ImportError:
            self.logger.error("openai package not installed. Run: pip install openai")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def decide_next_action(
        self,
        url: str,
        everything: Dict[str, Any],
        iteration: int
    ) -> Dict[str, Any]:
        """
        Ask OpenAI what to do next based on full page extraction.

        Args:
            url: Current URL
            full_page_text: Full text content of page
            buttons: List of all buttons with attributes
            links: List of all links with attributes
            inputs: List of all input fields with attributes
            iteration: Current iteration number

        Returns:
            {
                "status": "continue|success|stuck|human_needed",
                "reasoning": "why this action",
                "playwright_code": "code to execute",
                "description": "what this does"
            }
        """
        self.logger.info("="*60)
        self.logger.info(f"ITERATION {iteration}: Asking OpenAI for decision...")
        self.logger.info("="*60)

        # Build context for OpenAI with EVERYTHING
        context = self._build_context(url, everything, iteration)

        # DEBUG: Save prompt sent to OpenAI
        self.logger.save_iteration_debug(iteration, "prompt", context)

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": context
        })

        # Keep only last 6 messages (3 turns) - balance between memory and token limit
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]

        # Ask OpenAI
        response = self._ask_openai()

        # DEBUG: Save OpenAI's response
        self.logger.save_iteration_debug(iteration, "response", response)

        # Parse response
        action = self._parse_response(response)

        # Add OpenAI's response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        self.logger.info("="*60)
        self.logger.info(f"OpenAI Decision: {action.get('status')}")
        self.logger.info(f"Reasoning: {action.get('reasoning')}")
        self.logger.info("="*60)

        return action

    def _build_context(
        self,
        url: str,
        everything: Dict[str, Any],
        iteration: int
    ) -> str:
        """Build context from EVERYTHING extracted."""
        profile = self.config.get_profile()

        # Get stats
        stats = everything['stats']
        clickables = everything['clickables'][:20]  # Reduced to 20 for token limit
        fillables = everything['fillables'][:15]  # Reduced to 15 for token limit
        text = everything['text_content'][:2000]  # Reduced to 2000 chars for token limit
        iframes = everything.get('iframes', [])

        # Format clickables as JSON
        clickables_json = json.dumps([
            {
                'tag': c['tag'],
                'text': c['text'][:100],
                'id': c['id'],
                'classes': c['classes'],
                'role': c['role'],
                'aria_label': c['aria_label'],
                'data_attrs': {k: v for k, v in c['all_attributes'].items() if k.startswith('data-')},
            }
            for c in clickables
        ], indent=2)

        # Format fillables as JSON
        fillables_json = json.dumps([
            {
                'tag': f['tag'],
                'text': f['text'][:100],
                'id': f['id'],
                'name': f['name'],
                'type': f['type'],
                'placeholder': f['placeholder'],
                'required': f['required'],
                'aria_label': f['aria_label'],
            }
            for f in fillables
        ], indent=2)

        # Profile (including password for login forms + extracted resume data)
        profile_str = f"""NAME: {profile.get('name', 'N/A')}
EMAIL: {profile.get('email', 'N/A')}
PHONE: {profile.get('phone', 'N/A')}
PASSWORD: {profile.get('password', 'N/A')}
LOCATION: {profile.get('location', 'Chicago, IL')}
LINKEDIN: {profile.get('linkedin_url', 'N/A')}
RESUME PATH: {profile.get('resume_path', 'N/A')}
VISA STATUS: {profile.get('visa_status', 'F1 Student')}
WORK AUTHORIZATION: {profile.get('work_authorization', 'Requires Sponsorship')}
SPONSORSHIP NEEDED: {profile.get('sponsorship_needed', 'Yes')}
DEGREE: {profile.get('degree', 'Masters in Artificial Intelligence')}
UNIVERSITY: {profile.get('university', 'DePaul University')}
GRADUATION: {profile.get('graduation_month', 'November')} {profile.get('graduation_year', '2025')}

BACKGROUND: AI Engineer, 3yrs exp, Python/ML/GenAI, State Street (current)

USE PROFILE DATA above to fill forms AND tailor answers."""

        # Format iframe info
        iframe_info = ""
        if iframes:
            iframe_summary = []
            for iframe in iframes:
                iframe_summary.append(f"  - {iframe['iframe_name']} ({iframe['stats']['clickable_count']} clickables, {iframe['stats']['fillable_count']} fillables)")
            iframe_info = f"""
IFRAMES DETECTED (Job application systems like Greenhouse, Lever, Workday):
{chr(10).join(iframe_summary)}
NOTE: Elements from iframes are INCLUDED in the clickables/fillables below.
To interact with iframe elements, check the 'iframe_index' field and use: page.frames[INDEX].locator(...)
"""

        # Build context
        context = f"""ITERATION: {iteration}
URL: {url}

YOUR PROFILE:
{profile_str}

PAGE SUMMARY:
- Total elements: {stats['total_elements']}
- Clickable elements: {stats['clickable_count']} (buttons, links, etc.)
- Fillable elements: {stats['fillable_count']} (inputs, textareas, etc.)
- Iframes: {stats.get('iframe_count', 0)} (job application forms may be in iframes)
{iframe_info}
CLICKABLE ELEMENTS (buttons, links, anything clickable):
{clickables_json}

FILLABLE ELEMENTS (inputs, textareas, selects):
{fillables_json}

FULL PAGE TEXT:
{text}

---

TASK: Apply to this job successfully.

Based on the page content above, decide the next action.

IMPORTANT RULES:
1. **BATCH FILLING - CRITICAL FOR EFFICIENCY:**
   - Fill approximately 3 fields at once in ONE iteration (not just 1 field!)
   - Generate MULTI-LINE playwright_code that fills multiple fields
   - Example:
     page.fill('input[name="first_name"]', 'Mohammed')
     page.fill('input[name="last_name"]', 'Azeezulla')
     page.fill('input[name="email"]', 'mohammedazeezulla6996@gmail.com')
   - After filling 3 fields, click Next/Continue if available
   - This reduces iterations and saves tokens!

2. **DON'T REPEAT ACTIONS** - Check conversation history, if you just filled a field, DON'T fill it again

3. **MOVE FORWARD FAST** - After filling 3 fields, look for Next/Continue/Submit buttons and CLICK THEM

4. **Accept cookies first** if you see cookie/policy prompts

5. **CAPTCHA:** IGNORE CAPTCHA iframes/elements UNLESS they BLOCK your action
   - If you can fill forms/click buttons → Do it first
   - Only return "human_needed" if CAPTCHA actively prevents progress

6. **IFRAMES (Greenhouse, Lever, Workday, etc.):**
   - If element has 'iframe_index' in its data → It's inside an iframe
   - To interact: page.frames[INDEX].locator(...)
   - Example batch filling in iframe:
     page.frames[5].locator('input#first_name').fill('Mohammed')
     page.frames[5].locator('input#last_name').fill('Azeezulla')
     page.frames[5].locator('input#email').fill('mohammedazeezulla6996@gmail.com')

7. **Adapt to the page:**
   - See "Apply Now" button? → Click it
   - See login form? → Fill email/password and login
   - See signup form? → Fill it and create account
   - See job application form? → Fill 3 UNFILLED fields, then click Next/Submit
   - Don't assume - just react to what you see

8. **Use specific selectors:**
   - MAIN PAGE: page.get_by_role('button', name='exact text')
   - IFRAME: page.frames[INDEX].locator('selector') or page.frames[INDEX].get_by_role(...)
   - INPUTS: page.get_by_label('label') or page.locator('input[name="name"]')
   - Use id/name/type/iframe_index attributes from the element list above

9. **Fill forms with profile data** - Use name, email, phone, resume path, location, degree, etc.

10. **For questions NOT in profile** - Use resume context to tailor answers:
   - Experience questions → Reference AI Engineer with 3 years experience
   - Skills questions → Mention Python, ML, GenAI, LLMs from resume
   - Why this role → Connect your AI/ML background to job requirements
   - Open-ended → Professional answers based on your background

11. **Success detection:** If you see "Application Submitted" / "Thank you" → return "success"

Return JSON ONLY (no other text):
{{
    "status": "continue|success|stuck|human_needed",
    "reasoning": "why you chose this action and what you see on the page",
    "playwright_code": "Multi-line code filling ~3 fields then clicking Next/Submit. Example:\npage.fill('input[name=\"field1\"]', 'value1')\npage.fill('input[name=\"field2\"]', 'value2')\npage.fill('input[name=\"field3\"]', 'value3')\npage.get_by_role('button', name='Next').click()",
    "description": "brief description of what this code does"
}}
"""
        return context

    def _ask_openai(self) -> str:
        """Send context to OpenAI and get response."""
        self.logger.debug("Sending request to OpenAI API...")

        try:
            # System message with expert instructions
            system_message = """You are an expert web automation engineer using Playwright Python.

Your job is to analyze web pages and generate Playwright code to complete a job application.

Key capabilities:
- Write MULTI-LINE Playwright code to fill ~3 fields at once (efficient batch filling)
- Use page.get_by_role(), page.get_by_label(), page.get_by_placeholder()
- Handle iframes: page.frames[INDEX].locator(...) for iframe elements
- Handle cookies/policies (always accept them)
- Detect CAPTCHAs (return human_needed status)
- Fill forms intelligently using provided profile data
- Generate creative answers for open-ended questions
- Detect success (application submitted) and failure states

CRITICAL EFFICIENCY RULE: Fill approximately 3 fields per iteration using multi-line code, NOT just 1 field!
This dramatically reduces API calls and token usage.

CRITICAL: Return ONLY valid JSON. No explanations, no markdown, just JSON."""

            messages = [{"role": "system", "content": system_message}] + self.conversation_history

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1500,
                temperature=0.3  # Slightly creative for open-ended answers
            )

            response_text = response.choices[0].message.content
            self.logger.debug(f"OpenAI response: {response_text[:300]}...")

            return response_text

        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            raise

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI's JSON response."""
        try:
            # Extract JSON from response
            if '{' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                action = json.loads(json_str)
            else:
                raise ValueError("No JSON found in OpenAI's response")

            # Validate required fields
            required = ['status', 'reasoning']
            for field in required:
                if field not in action:
                    raise ValueError(f"Missing required field: {field}")

            return action

        except Exception as e:
            self.logger.error(f"Failed to parse OpenAI response: {e}")
            self.logger.error(f"Raw response: {response}")

            # Return a fallback action
            return {
                'status': 'stuck',
                'reasoning': f'Failed to parse OpenAI response: {e}',
                'playwright_code': None,
                'description': 'Parse error'
            }

    def reset_conversation(self):
        """Reset conversation history (for new job application)."""
        self.conversation_history = []
        self.logger.info("Conversation history reset")
