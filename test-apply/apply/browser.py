"""
Playwright browser management and navigation.
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Route
from typing import Optional, Callable, List, Dict, Any
import json
import time


class BrowserManager:
    """Manages Playwright browser instance and navigation."""

    def __init__(self, config, logger):
        """
        Initialize browser manager.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.network_responses: List[Dict[str, Any]] = []
        self._response_handler: Optional[Callable] = None

    def start(self):
        """Start browser instance."""
        self.logger.info("Starting browser...")

        self.playwright = sync_playwright().start()

        browser_type = self.config.get('browser.browser_type', 'chromium')
        headless = self.config.get('browser.headless', False)
        slow_mo = self.config.get('browser.slow_mo', 100)

        # Launch browser
        if browser_type == 'chromium':
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                slow_mo=slow_mo
            )
        elif browser_type == 'firefox':
            self.browser = self.playwright.firefox.launch(
                headless=headless,
                slow_mo=slow_mo
            )
        elif browser_type == 'webkit':
            self.browser = self.playwright.webkit.launch(
                headless=headless,
                slow_mo=slow_mo
            )
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")

        # Create context
        viewport = self.config.get('browser.viewport', {'width': 1280, 'height': 720})
        self.context = self.browser.new_context(
            viewport=viewport,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Create page
        self.page = self.context.new_page()

        # Set timeouts
        page_timeout = self.config.get('automation.page_timeout', 30000)
        self.page.set_default_timeout(page_timeout)

        # Setup network interception
        self._setup_network_interception()

        self.logger.info(f"Browser started ({browser_type}, headless={headless})")

    def _setup_network_interception(self):
        """Setup network response interception."""

        def handle_response(response):
            """Handle network response."""
            url = response.url

            # Filter relevant responses (JSON data)
            content_type = response.headers.get('content-type', '')

            if 'application/json' in content_type or 'text/json' in content_type:
                try:
                    data = response.json()

                    self.network_responses.append({
                        'url': url,
                        'status': response.status,
                        'data': data
                    })

                    # Log to file
                    self.logger.save_network_response(url, data)
                    self.logger.debug(f"Captured JSON response from {url}")

                except Exception as e:
                    self.logger.debug(f"Could not parse JSON from {url}: {e}")

        self.page.on('response', handle_response)

    def navigate(self, url: str, wait_until: str = 'domcontentloaded') -> bool:
        """
        Navigate to URL.

        Args:
            url: Target URL
            wait_until: Wait condition ('load', 'domcontentloaded', 'networkidle')
                       Default is 'domcontentloaded' to avoid timeout with tracking scripts

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Navigating to {url}")
            self.network_responses.clear()

            self.page.goto(url, wait_until=wait_until, timeout=60000)

            # Wait for dynamic content and JavaScript to execute
            time.sleep(2)

            self.logger.info(f"Navigation complete: {self.page.url}")
            return True

        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    def wait_for_navigation(self, timeout: Optional[int] = None):
        """
        Wait for navigation to complete.

        Args:
            timeout: Optional timeout in milliseconds
        """
        if timeout is None:
            timeout = self.config.get('automation.page_timeout', 30000)

        try:
            self.page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception as e:
            self.logger.debug(f"Wait for navigation timeout: {e}")

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url if self.page else ""

    def get_current_title(self) -> str:
        """Get current page title."""
        return self.page.title() if self.page else ""

    def get_html(self) -> str:
        """Get full page HTML content."""
        return self.page.content() if self.page else ""

    def scroll_to_load_lazy(self, max_scrolls: Optional[int] = None) -> int:
        """
        Scroll GRADUALLY to load lazy content - small increments.

        Args:
            max_scrolls: Maximum scroll attempts (safety limit)

        Returns:
            Number of scrolls performed
        """
        if max_scrolls is None:
            max_scrolls = self.config.get('automation.max_scroll_attempts', 100)  # Increased for REALLY large pages

        self.logger.info("Scrolling gradually to load page content...")

        scrolls = 0
        last_height = 0
        unchanged_count = 0

        # Get initial height
        current_height = self.page.evaluate("document.body.scrollHeight")
        last_height = current_height

        # Scroll gradually in small increments
        for i in range(max_scrolls):
            # Get current scroll position and page height
            scroll_y = self.page.evaluate("window.scrollY")
            page_height = self.page.evaluate("document.body.scrollHeight")
            viewport_height = self.page.evaluate("window.innerHeight")

            self.logger.debug(f"Scroll {i+1}: Position={scroll_y}, Height={page_height}")

            # Check if we've reached the bottom
            if scroll_y + viewport_height >= page_height - 100:  # Within 100px of bottom
                # Check if height changed
                if page_height == last_height:
                    unchanged_count += 1
                    self.logger.debug(f"At bottom, height unchanged ({unchanged_count}/5)")
                    if unchanged_count >= 5:  # Wait longer to ensure iframes/lazy content loads
                        self.logger.info(f"Page fully loaded after {scrolls} scrolls")
                        break
                else:
                    self.logger.debug(f"New content loaded! Height: {last_height} -> {page_height}")
                    unchanged_count = 0
                    last_height = page_height

            # Scroll down by 25% of viewport (smaller, gradual scrolls)
            scroll_amount = int(viewport_height * 0.25)
            self.page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")

            # Shorter wait time for smoother scrolling
            time.sleep(0.8)
            scrolls += 1

        # Scroll back to top gradually
        self.page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.5)

        self.logger.info(f"Page fully loaded - {scrolls} scrolls completed")
        return scrolls

    def take_screenshot(self, path: str):
        """
        Take screenshot.

        Args:
            path: Screenshot file path
        """
        if self.page:
            self.page.screenshot(path=path)
            self.logger.debug(f"Screenshot saved: {path}")

    def stop(self):
        """Stop browser instance."""
        self.logger.info("Stopping browser...")

        if self.page:
            self.page.close()

        if self.context:
            self.context.close()

        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()

        self.logger.info("Browser stopped")
