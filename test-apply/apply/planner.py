"""
Goal-driven planning and decision making.
Now powered by Claude API!
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from .claude_brain import ClaudeBrain


class State(Enum):
    """Application states."""
    INITIAL = "initial"
    JOB_LISTING = "job_listing"
    SIGN_IN = "sign_in"
    SIGN_UP = "sign_up"
    FORM_FILL = "form_fill"
    REVIEW = "review"
    SUBMIT = "submit"
    CONFIRMATION = "confirmation"
    BLOCKED = "blocked"
    CAPTCHA = "captcha"
    UNKNOWN = "unknown"


class Planner:
    """Plans actions to achieve the goal of submitting an application."""

    def __init__(self, config, logger):
        """
        Initialize planner.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.current_state = State.INITIAL
        self.visited_urls = set()
        self.action_history = []
        self.claude_brain = ClaudeBrain(logger, config)

    def analyze_and_plan(self, url: str, text_data: Dict[str, Any],
                        dom_data: Dict[str, Any],
                        network_data: Dict[str, Any],
                        iteration: int) -> List[Dict[str, Any]]:
        """
        Analyze current page state and plan next actions using Claude API.

        CLAUDE-POWERED APPROACH:
        1. Extract everything from page
        2. Send to Claude with goal
        3. Claude analyzes and returns Playwright code
        4. Execute what Claude decided

        Args:
            url: Current URL
            text_data: Extracted text data
            dom_data: DOM element data
            network_data: Network response data
            iteration: Current iteration number

        Returns:
            List of actions to perform
        """
        self.visited_urls.add(url)

        # ASK CLAUDE WHAT TO DO
        action = self.claude_brain.decide_next_action(url, dom_data, text_data, iteration)

        if action:
            return [action]

        # Fallback
        self.logger.warning("Claude returned no action")
        return [{'action_type': 'wait', 'reasoning': 'No action from Claude'}]

    def _find_goal_actions(self, dom_data: Dict[str, Any],
                          text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find actions that directly move toward the goal (application submission).

        Returns:
            List of goal-relevant actions, empty if none found
        """
        actions = []
        buttons = dom_data.get('buttons', [])
        links = dom_data.get('links', [])

        self.logger.debug(f"Searching for goal actions in {len(buttons)} buttons and {len(links)} links")

        # Log all buttons for debugging
        for i, button in enumerate(buttons[:10], 1):  # First 10
            self.logger.debug(
                f"  Button {i}: text='{button.get('text')}', "
                f"purpose={button.get('purpose')}, "
                f"disabled={button.get('disabled')}"
            )

        # Priority order for goal-relevant buttons
        goal_keywords = [
            ('apply', 5),           # "Apply Now", "Apply for this job"
            ('continue', 4),        # "Continue Application"
            ('submit', 4),          # "Submit Application"
            ('next', 3),            # "Next Step"
            ('save and continue', 5),
            ('proceed', 3),
        ]

        # Find buttons that match goal keywords
        candidates = []
        for button in buttons:
            text = button.get('text', '').lower().strip()
            purpose = button.get('purpose', '')

            # Skip disabled buttons
            if button.get('disabled'):
                self.logger.debug(f"  Skipping disabled button: '{button.get('text')}'")
                continue

            # Skip empty buttons
            if not text:
                continue

            # Check for goal keywords
            for keyword, priority in goal_keywords:
                if keyword in text or keyword == purpose:
                    candidates.append((priority, button, keyword, 'button'))
                    self.logger.debug(f"  ✓ Candidate found: '{text}' matches '{keyword}' (priority {priority})")
                    break

        # Also check links for "Apply" actions
        for link in links[:20]:  # First 20 links
            text = link.get('text', '').lower().strip()
            href = link.get('href', '').lower()

            if not text:
                continue

            # Check for apply in text or href
            if 'apply' in text or '/apply' in href:
                candidates.append((6, link, 'apply', 'link'))  # Higher priority for explicit apply links
                self.logger.debug(f"  ✓ Apply link found: '{text}' (href: {href})")

        # Sort by priority (highest first)
        candidates.sort(key=lambda x: x[0], reverse=True)

        self.logger.debug(f"Total goal action candidates: {len(candidates)}")

        # Take the highest priority action
        if candidates:
            priority, element, keyword, element_type = candidates[0]
            self.logger.info(f"[GOAL ACTION] '{element.get('text')}' (type: {element_type}, keyword: {keyword})")

            if element_type == 'button':
                actions.append({
                    'type': 'CLICK_BUTTON',
                    'data': element,
                    'reason': f'Goal action: click "{element.get("text")}"'
                })
            else:  # link
                actions.append({
                    'type': 'CLICK_LINK',
                    'text': element.get('text'),
                    'reason': f'Goal action: click link "{element.get("text")}"'
                })
        else:
            self.logger.debug("No goal actions found")

        return actions

    def _needs_authentication(self, dom_data: Dict[str, Any],
                             text_data: Dict[str, Any]) -> bool:
        """
        Check if authentication is blocking progress.
        Only return True if auth is REQUIRED, not just available.
        """
        # Check for explicit "sign in required" messages
        text = text_data.get('full_text', '').lower()

        blocking_phrases = [
            'sign in to apply',
            'login to continue',
            'you must sign in',
            'you must log in',
            'authentication required',
            'please log in to apply'
        ]

        if any(phrase in text for phrase in blocking_phrases):
            return True

        # Check if the ONLY action available is sign in
        buttons = dom_data.get('buttons', [])
        button_purposes = [btn.get('purpose') for btn in buttons]

        # If there are other action buttons, auth is not blocking
        action_buttons = ['apply', 'next', 'continue', 'submit']
        has_action_buttons = any(purpose in action_buttons for purpose in button_purposes)

        if has_action_buttons:
            return False  # Auth available but not required

        # Only if signin is the ONLY option
        has_signin = 'signin' in button_purposes
        return has_signin and not has_action_buttons

    def _has_fillable_forms(self, dom_data: Dict[str, Any]) -> bool:
        """Check if there are fillable forms on the page."""
        inputs = dom_data.get('inputs', [])

        # Ignore pure login forms (email + password only)
        input_purposes = [inp.get('purpose') for inp in inputs]

        # If we have more than just email/password, it's a fillable form
        non_auth_inputs = [p for p in input_purposes
                          if p not in ['email', 'password', 'unknown']]

        return len(non_auth_inputs) > 0

    def _plan_authentication(self, dom_data: Dict[str, Any],
                            text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan authentication actions."""
        return self._plan_signin(dom_data)

    def _determine_state(self, url: str, text_data: Dict[str, Any],
                        dom_data: Dict[str, Any]) -> State:
        """
        Determine current application state.

        Args:
            url: Current URL
            text_data: Text extraction data
            dom_data: DOM extraction data

        Returns:
            Current state
        """
        # Check text-based state first
        page_state = text_data.get('page_state', 'UNKNOWN')
        key_phrases = text_data.get('key_phrases', [])

        if page_state == 'CONFIRMATION' or 'application_submitted' in key_phrases:
            return State.CONFIRMATION

        if page_state == 'CAPTCHA' or 'captcha_detected' in key_phrases:
            return State.CAPTCHA

        if page_state == 'REVIEW' or 'review_step' in key_phrases:
            return State.REVIEW

        if page_state == 'SIGN_IN' or 'signin_required' in key_phrases:
            return State.SIGN_IN

        if page_state == 'SIGN_UP' or 'signup_required' in key_phrases:
            return State.SIGN_UP

        if page_state == 'FORM_FILL' or 'application_form' in key_phrases:
            return State.FORM_FILL

        # Check DOM elements
        inputs = dom_data.get('inputs', [])
        buttons = dom_data.get('buttons', [])

        # Look for specific button purposes
        button_purposes = [btn.get('purpose') for btn in buttons]

        if 'apply' in button_purposes:
            # If we have an apply button but no form inputs, it's likely a job listing
            if len(inputs) == 0:
                return State.JOB_LISTING
            else:
                return State.FORM_FILL

        if 'signin' in button_purposes:
            return State.SIGN_IN

        if 'signup' in button_purposes:
            return State.SIGN_UP

        if 'submit' in button_purposes:
            # Submit button with no inputs = review page
            if len(inputs) == 0:
                return State.REVIEW
            else:
                return State.FORM_FILL

        if 'next' in button_purposes and len(inputs) > 0:
            return State.FORM_FILL

        # Check URL patterns
        if any(pattern in url.lower() for pattern in ['/job/', '/position/', '/careers/']):
            return State.JOB_LISTING

        return State.UNKNOWN

    def _plan_for_state(self, state: State, text_data: Dict[str, Any],
                       dom_data: Dict[str, Any],
                       network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Plan actions for the current state.

        Args:
            state: Current state
            text_data: Text data
            dom_data: DOM data
            network_data: Network data

        Returns:
            List of planned actions
        """
        if state == State.CONFIRMATION:
            return [{'type': 'SUCCESS', 'reason': 'Application confirmation detected'}]

        if state == State.CAPTCHA:
            return [{'type': 'WAIT_HUMAN', 'reason': 'CAPTCHA detected'}]

        if state == State.BLOCKED:
            return [{'type': 'FAIL', 'reason': 'Blocked by error or access issue'}]

        if state == State.JOB_LISTING:
            return self._plan_job_listing(dom_data)

        if state == State.SIGN_IN:
            return self._plan_signin(dom_data)

        if state == State.SIGN_UP:
            return self._plan_signup(dom_data)

        if state == State.FORM_FILL:
            return self._plan_form_fill(dom_data)

        if state == State.REVIEW:
            return self._plan_review(dom_data)

        # Unknown state - try to explore
        return self._plan_exploration(dom_data)

    def _plan_job_listing(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan actions for job listing page."""
        buttons = dom_data.get('buttons', [])

        # Find "Apply" or "Easy Apply" button
        for button in buttons:
            purpose = button.get('purpose', '')
            text = button.get('text', '').lower()

            if purpose == 'apply' or 'apply' in text:
                return [{
                    'type': 'CLICK_BUTTON',
                    'data': button,
                    'reason': 'Click apply button'
                }]

        # No apply button found, look for links
        links = dom_data.get('links', [])
        for link in links:
            text = link.get('text', '').lower()
            if 'apply' in text:
                return [{
                    'type': 'CLICK_LINK',
                    'text': link.get('text'),
                    'reason': 'Click apply link'
                }]

        return [{'type': 'FAIL', 'reason': 'No apply button found on job listing'}]

    def _plan_signin(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan actions for sign-in page."""
        profile = self.config.get_profile()
        password = self.config.get_password()

        if not password:
            return [{'type': 'FAIL', 'reason': 'Password required but not provided'}]

        actions = []
        inputs = dom_data.get('inputs', [])

        # Find email and password fields
        email_input = None
        password_input = None

        for inp in inputs:
            purpose = inp.get('purpose', '')
            if purpose == 'email' and not email_input:
                email_input = inp
            elif purpose == 'password' and not password_input:
                password_input = inp

        if email_input:
            actions.append({
                'type': 'FILL_INPUT',
                'data': email_input,
                'value': profile.get('email'),
                'reason': 'Fill email field'
            })

        if password_input:
            actions.append({
                'type': 'FILL_INPUT',
                'data': password_input,
                'value': password,
                'reason': 'Fill password field'
            })

        # Find sign-in button
        buttons = dom_data.get('buttons', [])
        for button in buttons:
            if button.get('purpose') == 'signin':
                actions.append({
                    'type': 'CLICK_BUTTON',
                    'data': button,
                    'reason': 'Click sign-in button'
                })
                break

        if not actions:
            return [{'type': 'FAIL', 'reason': 'Could not find sign-in form fields'}]

        return actions

    def _plan_signup(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan actions for sign-up page."""
        # Check if we should create an account or switch to sign-in
        links = dom_data.get('links', [])

        # Look for "already have an account" / "sign in" link
        for link in links:
            text = link.get('text', '').lower()
            if 'sign in' in text or 'log in' in text:
                return [{
                    'type': 'CLICK_LINK',
                    'text': link.get('text'),
                    'reason': 'Switch to sign-in (assuming account exists)'
                }]

        # Otherwise, plan sign-up (similar to sign-in)
        return self._plan_signin(dom_data)  # Reuse sign-in logic

    def _plan_form_fill(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan actions for form filling."""
        profile = self.config.get_profile()
        actions = []
        inputs = dom_data.get('inputs', [])

        # Mapping of input purposes to profile fields
        field_mapping = {
            'email': profile.get('email'),
            'given-name': profile.get('first_name'),
            'family-name': profile.get('last_name'),
            'tel': profile.get('phone'),
            'linkedin': profile.get('linkedin_url'),
            'github': profile.get('github_url'),
            'url': profile.get('portfolio_url'),
        }

        # Fill inputs
        for inp in inputs:
            purpose = inp.get('purpose', '')
            input_type = inp.get('type', '')

            # Skip password fields (already authenticated)
            if purpose == 'password':
                continue

            # Handle file uploads
            if input_type == 'file' or purpose in ['resume', 'cover-letter']:
                if purpose == 'resume' or 'resume' in inp.get('label', '').lower():
                    resume_path = profile.get('resume_path')
                    if resume_path:
                        actions.append({
                            'type': 'UPLOAD_FILE',
                            'data': inp,
                            'value': resume_path,
                            'reason': 'Upload resume'
                        })
                elif purpose == 'cover-letter' or 'cover' in inp.get('label', '').lower():
                    cover_path = profile.get('cover_letter_path')
                    if cover_path:
                        actions.append({
                            'type': 'UPLOAD_FILE',
                            'data': inp,
                            'value': cover_path,
                            'reason': 'Upload cover letter'
                        })
                continue

            # Fill text inputs
            if purpose in field_mapping and field_mapping[purpose]:
                actions.append({
                    'type': 'FILL_INPUT',
                    'data': inp,
                    'value': field_mapping[purpose],
                    'reason': f'Fill {purpose} field'
                })

        # Find next/submit button
        buttons = dom_data.get('buttons', [])
        for button in buttons:
            purpose = button.get('purpose', '')
            if purpose in ['next', 'submit', 'apply']:
                actions.append({
                    'type': 'CLICK_BUTTON',
                    'data': button,
                    'reason': f'Click {purpose} button to proceed'
                })
                break

        if not actions:
            return [{'type': 'WAIT', 'reason': 'No actionable fields found'}]

        return actions

    def _plan_review(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan actions for review page."""
        buttons = dom_data.get('buttons', [])

        # Look for submit button
        for button in buttons:
            purpose = button.get('purpose', '')
            text = button.get('text', '').lower()

            if purpose == 'submit' or 'submit' in text or 'confirm' in text:
                return [{
                    'type': 'CLICK_BUTTON',
                    'data': button,
                    'reason': 'Submit application'
                }]

        return [{'type': 'FAIL', 'reason': 'No submit button found on review page'}]

    def _plan_exploration(self, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan exploratory actions when state is unknown."""
        # Look for promising buttons
        buttons = dom_data.get('buttons', [])

        promising_texts = ['apply', 'continue', 'next', 'start', 'begin']

        for button in buttons:
            text = button.get('text', '').lower()
            for keyword in promising_texts:
                if keyword in text:
                    return [{
                        'type': 'CLICK_BUTTON',
                        'data': button,
                        'reason': f'Explore: click "{button.get("text")}"'
                    }]

        return [{'type': 'WAIT', 'reason': 'Unknown state, no clear action'}]

    def should_continue(self, iteration: int) -> bool:
        """
        Check if we should continue the automation loop.

        Args:
            iteration: Current iteration number

        Returns:
            True if should continue
        """
        max_iterations = self.config.get('automation.max_iterations', 50)

        if iteration >= max_iterations:
            self.logger.warning(f"Reached maximum iterations ({max_iterations})")
            return False

        return True
