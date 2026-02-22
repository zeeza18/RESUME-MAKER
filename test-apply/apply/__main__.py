"""
Main CLI entry point for the job application automation tool.
V1: Universal OpenAI-driven automation.
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

from .config import Config
from .logger import ApplicationLogger
from .browser import BrowserManager
from .extractors import (
    NetworkExtractor,
    DOMExtractor,
    TextExtractor,
    UniversalExtractor,
    CompleteUniversalExtractor,
    PullEverythingExtractor
)
from .brain import UniversalBrain
from .executor import CodeExecutor
from .detect import Detector
from .captcha_solver import CaptchaSolver


class ApplicationAutomation:
    """Main automation orchestrator."""

    def __init__(self, url: str, config_path: str = None):
        """
        Initialize automation.

        Args:
            url: Target URL to start automation
            config_path: Optional path to config file
        """
        self.target_url = url

        # Initialize components
        self.config = Config(config_path)

        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(__file__).parent.parent / "runs" / timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.logger = ApplicationLogger(self.run_dir, self.config)
        self.browser = BrowserManager(self.config, self.logger)
        self.pull_everything = PullEverythingExtractor(self.logger)  # PULLS EVERYTHING!
        self.brain = UniversalBrain(self.logger, self.config)
        self.executor = CodeExecutor(self.logger, self.config)
        self.detector = Detector(self.logger)
        self.captcha_solver = CaptchaSolver(self.logger, self.config)

        self.iteration = 0
        self.final_status = None
        self.final_reason = None

    def run(self):
        """Execute the automation."""
        try:
            # Validate configuration
            if not self.config.validate():
                self.logger.error("Configuration validation failed")
                self._save_final_status("FAILED", "Invalid configuration", {})
                return False

            self.logger.info("=" * 60)
            self.logger.info("Job Application Automation Started")
            self.logger.info(f"Target URL: {self.target_url}")
            self.logger.info(f"Run directory: {self.run_dir}")
            self.logger.info("=" * 60)

            # Start browser
            self.browser.start()

            # Navigate to target URL
            if not self.browser.navigate(self.target_url):
                self._save_final_status("FAILED", "Failed to navigate to target URL", {})
                return False

            # Wait for page to fully load (dynamic - adapts to each site)
            self.logger.info("Waiting for page to fully load...")
            try:
                # Wait for network to be idle (no requests for 500ms)
                self.browser.page.wait_for_load_state('networkidle', timeout=30000)
                self.logger.info("Page fully loaded (network idle)")
            except Exception as e:
                self.logger.warning(f"Network idle timeout, continuing anyway: {e}")

            # Additional buffer for any remaining JavaScript
            import time
            time.sleep(2)

            # Main automation loop
            success = self._automation_loop()

            return success

        except KeyboardInterrupt:
            self.logger.warning("Automation interrupted by user")
            self._save_final_status("INTERRUPTED", "User cancelled", {})
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            self._save_final_status("FAILED", f"Unexpected error: {e}", {})
            return False

        finally:
            # Cleanup
            self.browser.stop()
            self.logger.info("=" * 60)
            self.logger.info("Automation completed")
            self.logger.info(f"Run artifacts saved to: {self.run_dir}")
            self.logger.info("=" * 60)

    def _automation_loop(self) -> bool:
        """
        Universal automation loop: Extract → OpenAI → Execute → Repeat

        Returns:
            True if successful
        """
        max_iterations = self.config.get('automation.max_iterations', 50)

        while self.iteration < max_iterations:
            self.iteration += 1

            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ITERATION {self.iteration}")
            self.logger.info(f"URL: {self.browser.get_current_url()}")
            self.logger.info(f"{'='*60}")

            # Wait for page to stabilize
            time.sleep(2)

            # Scroll to load ALL content (JD, buttons, forms, etc.)
            num_scrolls = self.browser.scroll_to_load_lazy()
            self.logger.info(f"Scrolled {num_scrolls} times to load page content")

            # Wait for any remaining dynamic content
            time.sleep(1)

            # STEP 1: EXTRACT EVERYTHING
            extraction = self._extract_page()

            # Save artifacts
            self._save_artifacts(extraction)

            # DEBUG: Save extraction summary
            ev = extraction['everything']
            iframe_summary = ""
            if ev.get('iframes'):
                iframe_lines = []
                for iframe in ev['iframes']:
                    iframe_lines.append(
                        f"  - {iframe['iframe_name']}: {iframe['stats']['clickable_count']} clickables, "
                        f"{iframe['stats']['fillable_count']} fillables"
                    )
                iframe_summary = f"\n- Iframes: {len(ev['iframes'])}\n" + "\n".join(iframe_lines)

            extraction_debug = f"""URL: {self.browser.get_current_url()}

EXTRACTION SUMMARY:
- Total elements: {ev['stats']['total_elements']}
- Clickable elements: {ev['stats']['clickable_count']}
- Fillable elements: {ev['stats']['fillable_count']}{iframe_summary}

CLICKABLES (first 10):
{self._format_clickables(ev['clickables'][:10])}

FILLABLES (first 10):
{self._format_fillables(ev['fillables'][:10])}

PAGE TEXT (first 1000 chars):
{ev['text_content'][:1000]}...
"""
            self.logger.save_iteration_debug(self.iteration, "extraction", extraction_debug)

            # Log what we found
            stats = extraction['everything']['stats']
            self.logger.info(
                f"PULLED: {stats['total_elements']} elements, "
                f"{stats['clickable_count']} clickables, "
                f"{stats['fillable_count']} fillables"
            )

            # STEP 2: ASK OPENAI WHAT TO DO (with EVERYTHING!)
            action = self.brain.decide_next_action(
                url=self.browser.get_current_url(),
                everything=extraction['everything'],  # EVERYTHING from the page!
                iteration=self.iteration
            )

            status = action.get('status')
            reasoning = action.get('reasoning', '')
            playwright_code = action.get('playwright_code')
            description = action.get('description', '')

            self.logger.info(f"Status: {status}")
            self.logger.info(f"Reasoning: {reasoning}")

            # STEP 3: HANDLE STATUS
            if status == 'success':
                self._save_final_status(
                    "SUCCESS",
                    reasoning,
                    {'iteration': self.iteration}
                )
                return True

            elif status == 'stuck':
                self._save_final_status(
                    "STUCK",
                    reasoning,
                    {'iteration': self.iteration}
                )
                return False

            elif status == 'human_needed':
                self.logger.warning(f"CAPTCHA/Human intervention needed: {reasoning}")

                # Try to auto-solve CAPTCHA with 2Captcha
                if 'captcha' in reasoning.lower() or 'recaptcha' in reasoning.lower():
                    self.logger.info("Attempting automatic CAPTCHA solving with 2Captcha...")

                    solution = self.captcha_solver.detect_and_solve(
                        self.browser.page,
                        self.browser.get_current_url()
                    )

                    if solution:
                        # Submit solution
                        if self.captcha_solver.submit_solution(self.browser.page, solution):
                            self.logger.info("CAPTCHA solved automatically! Continuing...")
                            time.sleep(3)  # Wait for CAPTCHA to process
                            continue
                        else:
                            self.logger.warning("Failed to submit CAPTCHA solution")

                    # If auto-solve failed, fall back to manual
                    self.logger.warning("Auto-solve failed, waiting for manual intervention...")

                # Manual intervention (either CAPTCHA failed or other reason)
                if not self.detector.wait_for_human_intervention(
                    self.browser.page,
                    reasoning,
                    timeout=300
                ):
                    self._save_final_status(
                        "BLOCKED",
                        f"Human intervention timeout: {reasoning}",
                        {'iteration': self.iteration}
                    )
                    return False

                # Continue after solved
                self.logger.info("Intervention complete, continuing...")
                continue

            elif status == 'continue':
                # STEP 4: EXECUTE PLAYWRIGHT CODE
                if playwright_code:
                    success = self.executor.execute(
                        self.browser.page,
                        playwright_code,
                        description,
                        iteration=self.iteration
                    )

                    if not success['success']:
                        self.logger.warning(f"Execution failed: {success.get('error')}")
                        # Continue anyway, OpenAI will see the result next iteration

                    # Wait for page to update
                    time.sleep(2)
                else:
                    self.logger.warning("No Playwright code provided, continuing...")

            else:
                self.logger.warning(f"Unknown status: {status}")

        # Max iterations reached
        self._save_final_status(
            "TIMEOUT",
            "Maximum iterations reached without completion",
            {'iteration': self.iteration}
        )
        return False

    def _extract_page(self) -> dict:
        """
        PULL EVERYTHING from the page - no filtering, no assumptions.

        Returns:
            Dictionary with extraction results
        """
        self.logger.debug("PULLING EVERYTHING from page...")

        # Get HTML
        html = self.browser.get_html()

        # PULL EVERYTHING - no exceptions!
        everything = self.pull_everything.pull_everything(self.browser.page, html)

        return {
            'html': html,
            'everything': everything  # EVERYTHING!
        }

    def _save_artifacts(self, extraction: dict):
        """Save extraction artifacts."""
        # Save HTML snapshot
        self.logger.save_html(extraction['html'], f"page_iter{self.iteration}")

        # Save EVERYTHING extraction
        if 'everything' in extraction:
            self.logger.save_universal_extraction(extraction['everything'], self.iteration)

    def _format_clickables(self, clickables: list) -> str:
        """Format clickable elements for debug."""
        lines = []
        for i, elem in enumerate(clickables, 1):
            text = elem.get('text', '')[:50]
            tag = elem.get('tag', '')
            lines.append(f"{i}. <{tag}> '{text}' (id={elem.get('id', 'N/A')})")
        return '\n'.join(lines) if lines else "(none)"

    def _format_fillables(self, fillables: list) -> str:
        """Format fillable elements for debug."""
        lines = []
        for i, elem in enumerate(fillables, 1):
            tag = elem.get('tag', '')
            elem_type = elem.get('type', '')
            name = elem.get('name', '')
            req = " [REQ]" if elem.get('required') else ""
            lines.append(f"{i}. <{tag} type={elem_type}> name={name}{req}")
        return '\n'.join(lines) if lines else "(none)"


    def _format_elements_debug(self, elements: list) -> str:
        """Format elements for debug output."""
        lines = []
        for i, elem in enumerate(elements[:30], 1):
            text = elem.get('text', '')
            id_attr = elem.get('id', '')
            class_attr = elem.get('class', '')
            disabled = " [DISABLED]" if elem.get('disabled') else ""
            lines.append(f"{i}. '{text}'{disabled} (id={id_attr}, class={class_attr})")
        return '\n'.join(lines) if lines else "(none)"

    def _format_links_debug(self, links: list) -> str:
        """Format links for debug output."""
        lines = []
        for i, link in enumerate(links[:30], 1):
            text = link.get('text', '')
            href = link.get('href', '')[:80]
            lines.append(f"{i}. '{text}' -> {href}")
        return '\n'.join(lines) if lines else "(none)"

    def _format_inputs_debug(self, inputs: list) -> str:
        """Format inputs for debug output."""
        lines = []
        for i, inp in enumerate(inputs[:25], 1):
            label = inp.get('label', '')
            placeholder = inp.get('placeholder', '')
            input_type = inp.get('type', 'text')
            name = inp.get('name', '')
            required = " [REQUIRED]" if inp.get('required') else ""
            desc = label or placeholder or f"[{input_type}]"
            lines.append(f"{i}. {desc} (type={input_type}, name={name}){required}")
        return '\n'.join(lines) if lines else "(none)"

    def _save_final_status(self, status: str, reason: str, details: dict):
        """Save final run status."""
        self.final_status = status
        self.final_reason = reason
        self.logger.save_final_status(status, reason, details)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automated job application tool using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m apply https://example.com/jobs/123
  python -m apply https://example.com/careers/apply --config my_config.yaml

Environment:
  Set JOB_APP_PASSWORD environment variable to avoid password prompt.
  Copy config.example.yaml to config.yaml and fill in your details.
        """
    )

    parser.add_argument(
        'url',
        help='Target job application URL'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration YAML file (default: config.yaml)',
        default=None
    )

    args = parser.parse_args()

    # Run automation
    automation = ApplicationAutomation(args.url, args.config)
    success = automation.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
