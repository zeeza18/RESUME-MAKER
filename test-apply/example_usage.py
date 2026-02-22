"""
Example usage of the job application automation tool.

This script demonstrates how to use the tool programmatically
instead of via the CLI.
"""

from pathlib import Path
from apply.config import Config
from apply.logger import ApplicationLogger
from apply.browser import BrowserManager
from apply.extractors import NetworkExtractor, DOMExtractor, TextExtractor
from apply.planner import Planner
from apply.actor import Actor
from apply.detect import Detector
from datetime import datetime


def main():
    """Example usage."""

    # Target URL for job application
    target_url = "https://example.com/jobs/apply"

    print("="*60)
    print("Job Application Automation - Example Usage")
    print("="*60)

    # 1. Load configuration
    print("\n1. Loading configuration...")
    config = Config()  # Uses config.yaml by default

    if not config.validate():
        print("ERROR: Configuration validation failed!")
        print("Please check config.yaml and ensure all required fields are filled.")
        return

    print("   ✓ Configuration loaded successfully")

    # 2. Setup logging
    print("\n2. Setting up logging...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(__file__).parent / "runs" / f"example_{timestamp}"
    logger = ApplicationLogger(run_dir, config)
    print(f"   ✓ Run directory: {run_dir}")

    # 3. Initialize components
    print("\n3. Initializing components...")
    browser = BrowserManager(config, logger)
    network_extractor = NetworkExtractor(logger)
    dom_extractor = DOMExtractor(logger)
    text_extractor = TextExtractor(logger)
    planner = Planner(config, logger)
    actor = Actor(config, logger)
    detector = Detector(logger)
    print("   ✓ All components initialized")

    # 4. Start browser
    print("\n4. Starting browser...")
    browser.start()
    print("   ✓ Browser started")

    try:
        # 5. Navigate to target
        print(f"\n5. Navigating to {target_url}...")
        if not browser.navigate(target_url):
            print("   ✗ Navigation failed!")
            return

        print("   ✓ Navigation successful")

        # 6. Extract page content
        print("\n6. Extracting page content...")

        html = browser.get_html()
        text_data = text_extractor.extract(html)
        dom_data = dom_extractor.extract(browser.page, html)
        network_data = network_extractor.extract(browser.network_responses)

        print(f"   ✓ Extracted {len(text_data['full_text'])} chars of text")
        print(f"   ✓ Found {len(dom_data['inputs'])} inputs")
        print(f"   ✓ Found {len(dom_data['buttons'])} buttons")
        print(f"   ✓ Captured {network_data.get('total_responses', 0)} network responses")

        # 7. Detect page state
        print("\n7. Detecting page state...")
        page_state = text_data.get('page_state', 'UNKNOWN')
        print(f"   ✓ Detected state: {page_state}")

        key_phrases = text_data.get('key_phrases', [])
        if key_phrases:
            print(f"   ✓ Key phrases: {', '.join(key_phrases)}")

        # 8. Check for CAPTCHA
        print("\n8. Checking for CAPTCHA...")
        if detector.detect_captcha(browser.page, html, text_data):
            print("   ⚠ CAPTCHA detected!")
            print("   → Manual intervention would be required")
        else:
            print("   ✓ No CAPTCHA detected")

        # 9. Plan actions
        print("\n9. Planning next actions...")
        actions = planner.analyze_and_plan(
            browser.get_current_url(),
            text_data,
            dom_data,
            network_data
        )

        print(f"   ✓ Planned {len(actions)} actions:")
        for i, action in enumerate(actions, 1):
            action_type = action.get('type')
            reason = action.get('reason', '')
            print(f"      {i}. {action_type}: {reason}")

        # 10. Save artifacts
        print("\n10. Saving artifacts...")
        logger.save_html(html, "example_page")
        logger.save_elements(dom_data, "example_elements")
        print(f"   ✓ Artifacts saved to {run_dir}")

        print("\n" + "="*60)
        print("Example completed successfully!")
        print("="*60)
        print(f"\nRun artifacts: {run_dir}")
        print("\nTo run a full automation, use:")
        print(f"  python -m apply {target_url}")

    finally:
        # Cleanup
        print("\nCleaning up...")
        browser.stop()
        print("✓ Browser stopped")


if __name__ == "__main__":
    main()
