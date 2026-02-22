"""
Detection utilities for CAPTCHA, challenges, and success states.
"""

from typing import Optional, Dict, Any
from playwright.sync_api import Page


class Detector:
    """Detects page states, challenges, and success conditions."""

    def __init__(self, logger):
        """
        Initialize detector.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def handle_cookie_consent(self, page: Page) -> bool:
        """
        Detect and handle cookie consent dialogs.

        Args:
            page: Playwright page

        Returns:
            True if cookie dialog was handled
        """
        self.logger.debug("Checking for cookie consent dialogs...")

        # Common cookie consent button selectors
        cookie_selectors = [
            # Text-based (most reliable)
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept all")',
            'button:has-text("I Accept")',
            'button:has-text("I Agree")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Allow all")',
            'a:has-text("Accept")',
            'a:has-text("Accept All")',
            # ID-based
            '#onetrust-accept-btn-handler',
            '#accept-cookies',
            '#cookie-accept',
            '#cookieAccept',
            '#acceptCookies',
            # Class-based (common patterns)
            '.cookie-accept',
            '.accept-cookies',
            '.cookies-accept-button',
            '[class*="cookie"][class*="accept"]',
            '[class*="consent"][class*="accept"]',
            # ARIA-based
            '[aria-label*="Accept"]',
            '[aria-label*="accept"]',
        ]

        for selector in cookie_selectors:
            try:
                elements = page.locator(selector).all()
                if elements and len(elements) > 0:
                    # Check if visible
                    if elements[0].is_visible(timeout=1000):
                        self.logger.info(f"Clicking cookie consent button: {selector}")
                        elements[0].click(timeout=3000)
                        page.wait_for_timeout(1000)  # Wait for dialog to close
                        return True
            except Exception as e:
                self.logger.debug(f"Cookie selector {selector} not found or not clickable: {e}")
                continue

        return False

    def detect_captcha(self, page: Page, html: str, text_data: Dict[str, Any]) -> bool:
        """
        Detect if CAPTCHA or anti-bot challenge is present.

        Args:
            page: Playwright page
            html: HTML content
            text_data: Extracted text data

        Returns:
            True if CAPTCHA detected
        """
        # First, try to handle cookie consent (not a blocker)
        try:
            self.handle_cookie_consent(page)
        except Exception as e:
            self.logger.debug(f"Cookie consent handling error: {e}")

        # Check text content
        if 'captcha_detected' in text_data.get('key_phrases', []):
            self.logger.warning("CAPTCHA detected in page text")
            return True

        # Check for common CAPTCHA iframes
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            'iframe[title*="reCAPTCHA"]',
            'iframe[title*="hCaptcha"]',
            '[class*="captcha"]',
            '[id*="captcha"]',
            '.cf-challenge-running',  # Cloudflare
            '#challenge-running',
            '[data-callback*="recaptcha"]',
            '#challenge-body',  # Cloudflare
            '.challenge-running',
        ]

        for selector in captcha_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    self.logger.warning(f"CAPTCHA detected: {selector}")
                    return True
            except Exception:
                pass

        # Check for Cloudflare challenge
        if 'Checking your browser' in html or 'Just a moment' in html:
            if 'cloudflare' in html.lower() or 'cf-browser-verification' in html.lower():
                self.logger.warning("Cloudflare challenge detected")
                # Wait a bit for it to complete automatically
                self.logger.info("Waiting for Cloudflare challenge to complete...")
                page.wait_for_timeout(5000)
                # Check if still on challenge page
                new_html = page.content()
                if 'Checking your browser' in new_html:
                    return True  # Still on challenge page
                else:
                    self.logger.info("Cloudflare challenge passed automatically")
                    return False

        # Check for other bot detection
        bot_indicators = [
            'verify you are human',
            'security check',
            'unusual activity',
            'automated request',
            'please verify',
            'datadome',
            'perimeter',
            'distil'
        ]

        text_lower = text_data.get('full_text', '').lower()
        for indicator in bot_indicators:
            if indicator in text_lower:
                self.logger.warning(f"Bot challenge detected: {indicator}")
                return True

        return False

    def detect_success(self, url: str, text_data: Dict[str, Any],
                      network_data: Dict[str, Any]) -> Optional[str]:
        """
        Detect if application was successfully submitted.

        Args:
            url: Current URL
            text_data: Extracted text data
            network_data: Network response data

        Returns:
            Success message if detected, None otherwise
        """
        # Check page state (most reliable)
        if text_data.get('page_state') == 'CONFIRMATION':
            return "Application confirmation page detected"

        # Check key phrases (very reliable)
        if 'application_submitted' in text_data.get('key_phrases', []):
            return "Application submitted confirmation found in text"

        # Check URL for success patterns (reliable)
        success_url_patterns = [
            '/success',
            '/confirmation',
            '/thank-you',
            '/submitted',
            '/complete',
            '/application-submitted'
        ]

        for pattern in success_url_patterns:
            if pattern in url.lower():
                return f"Success URL pattern detected: {pattern}"

        # Check network responses (less reliable - must be specific)
        if network_data:
            # Only check job_data responses (application-related)
            for response in network_data.get('job_data', []):
                data = response.get('data', {})
                response_url = response.get('url', '').lower()

                # Must be application-related endpoint
                if not any(keyword in response_url for keyword in ['application', 'apply', 'submit']):
                    continue

                if isinstance(data, dict):
                    # Look for explicit application submission indicators
                    if data.get('applicationSubmitted') is True:
                        return "Application submitted status in API response"

                    if data.get('submitted') is True and 'application' in str(data).lower():
                        return "Application submitted status in API response"

                    # Check status field
                    status = data.get('applicationStatus') or data.get('status', '')
                    if isinstance(status, str):
                        status = status.lower()
                        if status in ['submitted', 'complete', 'accepted']:
                            return f"Application status: {status}"

        return None

    def detect_blocking_issue(self, page: Page, text_data: Dict[str, Any]) -> Optional[str]:
        """
        Detect issues that block progress.

        Args:
            page: Playwright page
            text_data: Extracted text data

        Returns:
            Blocking issue description if detected, None otherwise
        """
        # Check for error messages
        if 'error_detected' in text_data.get('key_phrases', []):
            # Try to extract specific error
            text = text_data.get('full_text', '')

            error_keywords = ['error:', 'invalid', 'required']
            for keyword in error_keywords:
                if keyword in text.lower():
                    # Extract surrounding text
                    idx = text.lower().find(keyword)
                    error_msg = text[max(0, idx-50):min(len(text), idx+150)]
                    return f"Error detected: {error_msg}"

            return "Error detected on page"

        # Check for session expiration
        text_lower = text_data.get('full_text', '').lower()
        if any(phrase in text_lower for phrase in ['session expired', 'logged out', 'timeout']):
            return "Session expired"

        # Check for access denied
        if any(phrase in text_lower for phrase in ['access denied', 'unauthorized', 'forbidden']):
            return "Access denied"

        return None

    def detect_page_type(self, url: str, text_data: Dict[str, Any],
                        dom_data: Dict[str, Any]) -> str:
        """
        Detect the type of page we're currently on.

        Args:
            url: Current URL
            text_data: Extracted text data
            dom_data: DOM element data

        Returns:
            Page type identifier
        """
        # First check text-based state
        page_state = text_data.get('page_state', 'UNKNOWN')
        if page_state != 'UNKNOWN':
            return page_state

        # Check DOM elements
        inputs = dom_data.get('inputs', [])
        buttons = dom_data.get('buttons', [])

        # Check for login page
        has_email = any(inp.get('purpose') == 'email' for inp in inputs)
        has_password = any(inp.get('purpose') == 'password' for inp in inputs)
        has_signin_button = any(btn.get('purpose') == 'signin' for btn in buttons)

        if has_email and has_password and has_signin_button:
            return 'SIGN_IN'

        # Check for signup page
        has_signup_button = any(btn.get('purpose') == 'signup' for btn in buttons)
        if has_email and has_password and has_signup_button:
            return 'SIGN_UP'

        # Check for application form
        has_apply_button = any(btn.get('purpose') == 'apply' for btn in buttons)
        has_submit_button = any(btn.get('purpose') == 'submit' for btn in buttons)
        has_next_button = any(btn.get('purpose') == 'next' for btn in buttons)

        if len(inputs) > 0 and (has_apply_button or has_submit_button or has_next_button):
            return 'FORM_FILL'

        # Check for review page
        if has_submit_button and len(inputs) == 0:
            return 'REVIEW'

        # Check URL patterns
        if '/apply' in url.lower():
            return 'APPLICATION'

        if any(pattern in url.lower() for pattern in ['/job/', '/position/', '/career/']):
            return 'JOB_LISTING'

        return 'UNKNOWN'

    def wait_for_human_intervention(self, page: Page, reason: str, timeout: int = 300):
        """
        Wait for human to complete a manual task (e.g., CAPTCHA).

        Args:
            page: Playwright page
            reason: Reason for waiting
            timeout: Maximum wait time in seconds

        Returns:
            True if page changed, False if timeout
        """
        self.logger.warning(f"HUMAN INTERVENTION REQUIRED: {reason}")
        self.logger.warning(f"Please complete the task in the browser. Waiting up to {timeout} seconds...")

        initial_url = page.url

        # Wait for URL change or timeout
        try:
            page.wait_for_url(lambda url: url != initial_url, timeout=timeout * 1000)
            self.logger.info("Page changed, resuming automation")
            return True
        except Exception:
            self.logger.warning("Wait timeout exceeded")
            return False
