"""Playwright browser automation for job applications."""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime


class BrowserEngine:
    """Handles Playwright browser automation for job applications."""

    def __init__(self):
        self.email = "mohammedazeezulla6996@gmail.com"
        self.screenshots_dir = Path(__file__).parent.parent / "data" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._browser = None
        self._context = None
        self._page = None

    def generate_password(self, company_name: str) -> str:
        """
        Generate password based on company name.
        Pattern: Zeeza_{first 3 letters}@6996
        """
        # Clean company name - remove spaces, special chars
        clean_name = ''.join(c.lower() for c in company_name if c.isalnum())
        prefix = clean_name[:3] if len(clean_name) >= 3 else clean_name
        return f"Zeeza_{prefix}@6996"

    async def initialize(self, headless: bool = False) -> None:
        """Initialize the browser."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=['--start-maximized']
        )
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self._page = await self._context.new_page()

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()

    async def navigate(self, url: str) -> bool:
        """Navigate to a URL."""
        try:
            await self._page.goto(url, wait_until='networkidle', timeout=30000)
            return True
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    async def take_screenshot(self, name: Optional[str] = None) -> str:
        """Take a full-page screenshot and return the path."""
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")

        screenshot_path = self.screenshots_dir / f"{name}.png"
        await self._page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)

    async def get_page_text(self) -> str:
        """Get the full visible text content of the page."""
        try:
            return await self._page.evaluate('() => document.body.innerText')
        except Exception:
            return ""

    def get_current_url(self) -> str:
        """Get the current page URL safely."""
        try:
            return self._page.url if self._page else ""
        except Exception:
            return ""

    async def get_page_content(self) -> Dict[str, Any]:
        """Get structured page content for analysis."""
        content = await self._page.evaluate('''() => {
            const forms = [];
            document.querySelectorAll('form').forEach((form, index) => {
                const fields = [];
                form.querySelectorAll('input, textarea, select').forEach(field => {
                    fields.push({
                        type: field.type || field.tagName.toLowerCase(),
                        name: field.name || field.id,
                        placeholder: field.placeholder || '',
                        label: field.labels?.[0]?.textContent?.trim() || '',
                        required: field.required,
                        value: field.value || ''
                    });
                });
                forms.push({
                    id: form.id || `form_${index}`,
                    action: form.action,
                    method: form.method,
                    fields: fields
                });
            });

            const buttons = [];
            document.querySelectorAll('button, input[type="submit"], a[href*="apply"]').forEach(btn => {
                buttons.push({
                    text: btn.textContent?.trim() || btn.value || '',
                    type: btn.type || 'button',
                    id: btn.id,
                    classes: btn.className
                });
            });

            return {
                url: window.location.href,
                title: document.title,
                forms: forms,
                buttons: buttons
            };
        }''')
        return content

    async def execute_code(self, code: str) -> Tuple[bool, str]:
        """
        Execute generated Playwright code.
        Returns (success, error_message)
        """
        try:
            # Create a local context with the page
            local_vars = {'page': self._page}

            # Execute the code
            exec(f"async def _run():\n" +
                 '\n'.join(f"    {line}" for line in code.split('\n')),
                 local_vars)

            await local_vars['_run']()
            return True, ""
        except Exception as e:
            return False, str(e)

    async def fill_field(self, selector: str, value: str) -> bool:
        """Fill a form field."""
        try:
            await self._page.fill(selector, value)
            return True
        except Exception:
            return False

    async def click_element(self, selector: str) -> bool:
        """Click an element."""
        try:
            await self._page.click(selector)
            return True
        except Exception:
            return False

    async def wait_for_navigation(self, timeout: int = 10000) -> bool:
        """Wait for page navigation."""
        try:
            await self._page.wait_for_load_state('networkidle', timeout=timeout)
            return True
        except Exception:
            return False

    async def login_if_needed(self, company: str) -> bool:
        """
        Attempt to login if a login form is detected.
        Uses the dynamic password generation.
        """
        password = self.generate_password(company)

        # Check for common login selectors
        login_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            'input[type="password"]'
        ]

        email_filled = False
        password_filled = False

        for selector in login_selectors:
            try:
                element = await self._page.query_selector(selector)
                if element:
                    input_type = await element.get_attribute('type')
                    if input_type == 'password':
                        await element.fill(password)
                        password_filled = True
                    elif 'email' in selector:
                        await element.fill(self.email)
                        email_filled = True
            except Exception:
                continue

        if email_filled and password_filled:
            # Try to find and click login/submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Log in")'
            ]
            for selector in submit_selectors:
                try:
                    await self._page.click(selector)
                    await self.wait_for_navigation()
                    return True
                except Exception:
                    continue

        return False


def run_sync(coro):
    """Helper to run async code synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
