"""
Automatic CAPTCHA solving using 2Captcha API.
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any


class CaptchaSolver:
    """Solves CAPTCHAs using 2Captcha service."""

    def __init__(self, logger, config):
        """
        Initialize CAPTCHA solver.

        Args:
            logger: Logger instance
            config: Configuration object
        """
        self.logger = logger
        self.config = config
        self.api_key = self._load_api_key()
        self.solver = None

        if self.api_key:
            self._initialize_solver()

    def _load_api_key(self) -> Optional[str]:
        """Load 2Captcha API key from environment."""
        api_key = os.getenv('TWOCAPTCHA_API_KEY')

        if api_key and api_key.strip():
            self.logger.info("OK 2Captcha API key loaded")
            return api_key
        else:
            self.logger.warning("X 2Captcha API key not found - CAPTCHA solving disabled")
            return None

    def _initialize_solver(self):
        """Initialize 2Captcha solver."""
        try:
            from twocaptcha import TwoCaptcha
            self.solver = TwoCaptcha(self.api_key)
            self.logger.info("OK 2Captcha solver initialized")
        except ImportError:
            self.logger.error("twocaptcha-python not installed. Run: pip install twocaptcha-python")
            self.solver = None
        except Exception as e:
            self.logger.error(f"Failed to initialize 2Captcha: {e}")
            self.solver = None

    def solve_recaptcha_v2(self, page_url: str, site_key: str) -> Optional[str]:
        """
        Solve reCAPTCHA v2.

        Args:
            page_url: URL of the page with CAPTCHA
            site_key: reCAPTCHA site key (data-sitekey)

        Returns:
            Solution token or None if failed
        """
        if not self.solver:
            self.logger.warning("2Captcha solver not available")
            return None

        self.logger.info("Solving reCAPTCHA v2 with 2Captcha...")
        self.logger.info(f"Page URL: {page_url}")
        self.logger.info(f"Site Key: {site_key}")

        try:
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url
            )

            solution = result.get('code')
            self.logger.info(f"CAPTCHA solved! Token: {solution[:50]}...")
            return solution

        except Exception as e:
            self.logger.error(f"2Captcha solving failed: {e}")
            return None

    def solve_hcaptcha(self, page_url: str, site_key: str) -> Optional[str]:
        """
        Solve hCaptcha.

        Args:
            page_url: URL of the page with CAPTCHA
            site_key: hCaptcha site key

        Returns:
            Solution token or None if failed
        """
        if not self.solver:
            self.logger.warning("2Captcha solver not available")
            return None

        self.logger.info("Solving hCaptcha with 2Captcha...")

        try:
            result = self.solver.hcaptcha(
                sitekey=site_key,
                url=page_url
            )

            solution = result.get('code')
            self.logger.info(f"hCaptcha solved! Token: {solution[:50]}...")
            return solution

        except Exception as e:
            self.logger.error(f"2Captcha solving failed: {e}")
            return None

    def detect_and_solve(self, page, page_url: str) -> Optional[str]:
        """
        Auto-detect CAPTCHA type and solve it.

        Args:
            page: Playwright page object
            page_url: Current page URL

        Returns:
            Solution token or None
        """
        self.logger.info("Detecting CAPTCHA type...")

        # Check for reCAPTCHA v2
        recaptcha_frame = page.locator('iframe[src*="recaptcha"]').first
        if recaptcha_frame.count() > 0:
            self.logger.info("Detected: reCAPTCHA v2")

            # Extract site key
            try:
                site_key = page.locator('.g-recaptcha').get_attribute('data-sitekey')
                if not site_key:
                    # Try alternate method
                    site_key = page.evaluate("""
                        () => {
                            const elem = document.querySelector('[data-sitekey]');
                            return elem ? elem.getAttribute('data-sitekey') : null;
                        }
                    """)

                if site_key:
                    return self.solve_recaptcha_v2(page_url, site_key)
                else:
                    self.logger.error("Could not find reCAPTCHA site key")
                    return None

            except Exception as e:
                self.logger.error(f"Error extracting reCAPTCHA site key: {e}")
                return None

        # Check for hCaptcha
        hcaptcha_frame = page.locator('iframe[src*="hcaptcha"]').first
        if hcaptcha_frame.count() > 0:
            self.logger.info("Detected: hCaptcha")

            try:
                site_key = page.locator('[data-sitekey]').first.get_attribute('data-sitekey')
                if site_key:
                    return self.solve_hcaptcha(page_url, site_key)
                else:
                    self.logger.error("Could not find hCaptcha site key")
                    return None

            except Exception as e:
                self.logger.error(f"Error extracting hCaptcha site key: {e}")
                return None

        # Check for simple "I'm not a robot" checkbox
        checkbox = page.locator('#recaptcha-anchor').first
        if checkbox.count() > 0:
            self.logger.info("Detected: reCAPTCHA v2 checkbox")
            # This also uses reCAPTCHA v2 API
            try:
                site_key = page.evaluate("""
                    () => {
                        const elem = document.querySelector('[data-sitekey]');
                        return elem ? elem.getAttribute('data-sitekey') : null;
                    }
                """)
                if site_key:
                    return self.solve_recaptcha_v2(page_url, site_key)
            except Exception as e:
                self.logger.error(f"Error with checkbox CAPTCHA: {e}")
                return None

        self.logger.warning("No supported CAPTCHA detected")
        return None

    def submit_solution(self, page, solution: str) -> bool:
        """
        Submit CAPTCHA solution to the page.

        Args:
            page: Playwright page object
            solution: CAPTCHA solution token

        Returns:
            True if successful
        """
        try:
            self.logger.info("Submitting CAPTCHA solution...")

            # For reCAPTCHA v2
            page.evaluate(f"""
                () => {{
                    const textarea = document.getElementById('g-recaptcha-response');
                    if (textarea) {{
                        textarea.innerHTML = '{solution}';
                        textarea.value = '{solution}';
                    }}
                }}
            """)

            # Trigger callback if it exists
            page.evaluate("""
                () => {
                    if (typeof grecaptcha !== 'undefined') {
                        grecaptcha.getResponse = function() { return document.getElementById('g-recaptcha-response').value; };
                    }
                }
            """)

            time.sleep(1)
            self.logger.info("CAPTCHA solution submitted successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to submit CAPTCHA solution: {e}")
            return False
