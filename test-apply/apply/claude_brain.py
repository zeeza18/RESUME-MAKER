"""
OpenAI-powered decision making - The Brain of the automation.
Uses OpenAI API to analyze extracted page content and generate Playwright code.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ClaudeBrain:
    """
    Uses OpenAI API to make intelligent decisions.
    Sends extracted page content to OpenAI and gets back Playwright code to execute.
    """

    def __init__(self, logger, config):
        """
        Initialize OpenAI brain.

        Args:
            logger: Logger instance
            config: Configuration object
        """
        self.logger = logger
        self.config = config
        self.api_key = self._load_api_key()
        self.client = None
        self.goal = "Submit a job application"

        if self.api_key:
            self._initialize_client()
        else:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env")

    def _load_api_key(self) -> Optional[str]:
        """Load OpenAI API key from .env file."""
        # Check current directory first
        current_env = Path(__file__).parent.parent / ".env"

        # Check parent directory (RESUME-MAKER root)
        parent_env = Path(__file__).parent.parent.parent / ".env"

        self.logger.debug(f"Looking for .env at: {parent_env}")

        # Load from parent first (if exists)
        if parent_env.exists():
            from dotenv import load_dotenv
            load_dotenv(parent_env)
            self.logger.info(f"Loaded .env from {parent_env}")

        # Load from current directory (if exists) - this will override parent
        if current_env.exists():
            from dotenv import load_dotenv
            load_dotenv(current_env)
            self.logger.info(f"Loaded .env from {current_env}")

        # Try to get API key
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

    def decide_next_action(self, url: str, dom_data: Dict[str, Any],
                          text_data: Dict[str, Any],
                          iteration: int) -> Dict[str, Any]:
        """
        Ask OpenAI what to do next based on extracted page content.

        Args:
            url: Current URL
            dom_data: Extracted DOM elements
            text_data: Extracted text content
            iteration: Current iteration number

        Returns:
            Action to take with Playwright code
        """
        self.logger.info("=" * 60)
        self.logger.info("BRAIN: ASKING OPENAI FOR DECISION...")
        self.logger.info("=" * 60)

        # Prepare page context for OpenAI
        context = self._build_context(url, dom_data, text_data, iteration)

        # Ask OpenAI
        response = self._ask_openai(context)

        # Parse response
        action = self._parse_response(response)

        self.logger.info("=" * 60)
        self.logger.info(f"TARGET: OPENAI'S DECISION: {action.get('action_type')}")
        self.logger.info(f"NOTE: Reasoning: {action.get('reasoning')}")
        self.logger.info("=" * 60)

        return action

    def _build_context(self, url: str, dom_data: Dict[str, Any],
                      text_data: Dict[str, Any], iteration: int) -> str:
        """Build context string to send to Claude."""

        buttons = dom_data.get('buttons', [])
        links = dom_data.get('links', [])
        inputs = dom_data.get('inputs', [])
        page_text = text_data.get('full_text', '')

        # Limit text length
        if len(page_text) > 3000:
            page_text = page_text[:3000] + "..."

        # Build button list
        button_list = []
        for i, btn in enumerate(buttons[:20], 1):  # First 20
            text = btn.get('text', '').strip()
            if text:
                disabled = " [DISABLED]" if btn.get('disabled') else ""
                button_list.append(f"{i}. '{text}'{disabled}")

        # Build link list
        link_list = []
        for i, link in enumerate(links[:20], 1):  # First 20
            text = link.get('text', '').strip()
            href = link.get('href', '')
            if text:
                link_list.append(f"{i}. '{text}' -> {href}")

        # Build input list
        input_list = []
        for i, inp in enumerate(inputs[:15], 1):  # First 15
            label = inp.get('label', '')
            placeholder = inp.get('placeholder', '')
            input_type = inp.get('type', 'text')
            purpose = inp.get('purpose', 'unknown')
            required = " [REQUIRED]" if inp.get('required') else ""

            desc = label or placeholder or f"[{input_type}]"
            input_list.append(f"{i}. {desc} (type: {input_type}, purpose: {purpose}){required}")

        # Build context
        context = f"""ITERATION: {iteration}

GOAL: {self.goal}

CURRENT URL: {url}

PAGE CONTENT:

BUTTONS AVAILABLE ({len(buttons)} total, showing first 20):
{chr(10).join(button_list) if button_list else "(none)"}

LINKS AVAILABLE ({len(links)} total, showing first 20):
{chr(10).join(link_list) if link_list else "(none)"}

FORM INPUTS AVAILABLE ({len(inputs)} total):
{chr(10).join(input_list) if input_list else "(none)"}

PAGE TEXT EXCERPT:
{page_text}

---

Based on this page content, what should I do next to achieve the goal: "{self.goal}"?

Analyze the page and tell me:
1. What action to take (click button, fill form, click link, etc.)
2. Specific Playwright code to execute
3. Your reasoning

Return your response as JSON only (no other text):
{{
    "action_type": "click_button|fill_input|click_link|upload_file|submit",
    "reasoning": "why you chose this action",
    "playwright_code": "exact playwright code to execute",
    "element_identifier": "text or label of element",
    "fill_data": {{"field_purpose": "value"}} (only if filling form)
}}
"""

        return context

    def _ask_openai(self, context: str) -> str:
        """Send context to OpenAI and get response."""

        self.logger.debug("Sending request to OpenAI API...")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Latest GPT-4 model
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at web automation using Playwright.
Your job is to analyze extracted web page content and decide what action to take to achieve a goal.
You must return valid JSON only, no other text.
Be precise with Playwright selectors. Use text-based selectors when possible (e.g., page.get_by_role('button', name='Apply')).
If you see a goal-relevant action (like "Apply" button), prioritize it.
If authentication is required, handle it.
If forms need filling, identify required fields.
Be strategic and goal-oriented."""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=2000,
                temperature=0  # Deterministic for consistent decisions
            )

            response_text = response.choices[0].message.content
            self.logger.debug(f"OpenAI response: {response_text[:200]}...")

            return response_text

        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            raise

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI's JSON response into action."""

        try:
            # Extract JSON from response (in case OpenAI added explanation)
            if '{' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                action = json.loads(json_str)
            else:
                raise ValueError("No JSON found in OpenAI's response")

            # Validate required fields
            required = ['action_type', 'reasoning']
            for field in required:
                if field not in action:
                    raise ValueError(f"Missing required field: {field}")

            return action

        except Exception as e:
            self.logger.error(f"Failed to parse OpenAI response: {e}")
            self.logger.error(f"Raw response: {response}")

            # Return a fallback action
            return {
                'action_type': 'wait',
                'reasoning': f'Failed to parse OpenAI response: {e}',
                'playwright_code': None
            }
