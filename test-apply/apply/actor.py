"""
Action execution: clicking, filling forms, uploading files.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from playwright.sync_api import Page, ElementHandle, Locator
import time


class Actor:
    """Executes actions on the page."""

    def __init__(self, config, logger):
        """
        Initialize actor.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

    def click_button(self, page: Page, button_data: Dict[str, Any]) -> bool:
        """
        Click a button by semantic data.

        Args:
            page: Playwright page
            button_data: Button information from DOM extraction

        Returns:
            True if successful
        """
        text = button_data.get('text', '')
        aria_label = button_data.get('aria_label', '')

        self.logger.action('CLICK', {'text': text, 'aria_label': aria_label})

        try:
            # Try multiple strategies
            clicked = False

            # Strategy 1: By text content
            if text:
                try:
                    # Try exact match first
                    locator = page.get_by_role('button', name=text, exact=True)
                    if locator.count() > 0:
                        locator.first.click(timeout=5000)
                        clicked = True
                except Exception:
                    pass

                if not clicked:
                    try:
                        # Try partial match
                        locator = page.get_by_text(text, exact=False)
                        if locator.count() > 0:
                            locator.first.click(timeout=5000)
                            clicked = True
                    except Exception:
                        pass

            # Strategy 2: By ARIA label
            if not clicked and aria_label:
                try:
                    locator = page.get_by_label(aria_label)
                    if locator.count() > 0:
                        locator.first.click(timeout=5000)
                        clicked = True
                except Exception:
                    pass

            if clicked:
                # Wait for any navigation or dynamic updates
                time.sleep(self.config.get('automation.action_delay', 1000) / 1000)
                self.logger.info(f"Clicked button: {text}")
                return True

            self.logger.warning(f"Could not click button: {text}")
            return False

        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    def fill_input(self, page: Page, input_data: Dict[str, Any], value: str) -> bool:
        """
        Fill an input field.

        Args:
            page: Playwright page
            input_data: Input information from DOM extraction
            value: Value to fill

        Returns:
            True if successful
        """
        label = input_data.get('label', '')
        placeholder = input_data.get('placeholder', '')
        name = input_data.get('name', '')
        input_id = input_data.get('id', '')

        self.logger.action('FILL', {
            'label': label,
            'placeholder': placeholder,
            'name': name,
            'value': '***' if 'password' in str(input_data.get('purpose', '')).lower() else value
        })

        try:
            filled = False

            # Strategy 1: By label
            if label:
                try:
                    locator = page.get_by_label(label, exact=False)
                    if locator.count() > 0:
                        locator.first.fill(value, timeout=5000)
                        filled = True
                except Exception:
                    pass

            # Strategy 2: By placeholder
            if not filled and placeholder:
                try:
                    locator = page.get_by_placeholder(placeholder, exact=False)
                    if locator.count() > 0:
                        locator.first.fill(value, timeout=5000)
                        filled = True
                except Exception:
                    pass

            # Strategy 3: By name attribute
            if not filled and name:
                try:
                    locator = page.locator(f'[name="{name}"]')
                    if locator.count() > 0:
                        locator.first.fill(value, timeout=5000)
                        filled = True
                except Exception:
                    pass

            # Strategy 4: By ID
            if not filled and input_id:
                try:
                    locator = page.locator(f'#{input_id}')
                    if locator.count() > 0:
                        locator.first.fill(value, timeout=5000)
                        filled = True
                except Exception:
                    pass

            if filled:
                time.sleep(0.3)  # Small delay for validation
                self.logger.info(f"Filled input: {label or placeholder or name}")
                return True

            self.logger.warning(f"Could not fill input: {label or placeholder or name}")
            return False

        except Exception as e:
            self.logger.error(f"Fill failed: {e}")
            return False

    def upload_file(self, page: Page, input_data: Dict[str, Any], file_path: str) -> bool:
        """
        Upload a file to an input.

        Args:
            page: Playwright page
            input_data: Input information
            file_path: Path to file to upload

        Returns:
            True if successful
        """
        if not Path(file_path).exists():
            self.logger.error(f"File not found: {file_path}")
            return False

        label = input_data.get('label', '')
        name = input_data.get('name', '')

        self.logger.action('UPLOAD', {'label': label, 'name': name, 'file': file_path})

        try:
            uploaded = False

            # Strategy 1: By label
            if label:
                try:
                    locator = page.get_by_label(label, exact=False)
                    if locator.count() > 0:
                        locator.first.set_input_files(file_path, timeout=5000)
                        uploaded = True
                except Exception:
                    pass

            # Strategy 2: By name
            if not uploaded and name:
                try:
                    locator = page.locator(f'input[type="file"][name="{name}"]')
                    if locator.count() > 0:
                        locator.first.set_input_files(file_path, timeout=5000)
                        uploaded = True
                except Exception:
                    pass

            # Strategy 3: Any file input
            if not uploaded:
                try:
                    locator = page.locator('input[type="file"]')
                    if locator.count() > 0:
                        locator.first.set_input_files(file_path, timeout=5000)
                        uploaded = True
                except Exception:
                    pass

            if uploaded:
                time.sleep(1)  # Wait for upload to process
                self.logger.info(f"Uploaded file: {Path(file_path).name}")
                return True

            self.logger.warning(f"Could not upload file to: {label or name}")
            return False

        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return False

    def select_option(self, page: Page, input_data: Dict[str, Any], value: str) -> bool:
        """
        Select an option from a dropdown/select element.

        Args:
            page: Playwright page
            input_data: Select element information
            value: Value or label to select

        Returns:
            True if successful
        """
        label = input_data.get('label', '')
        name = input_data.get('name', '')

        self.logger.action('SELECT', {'label': label, 'name': name, 'value': value})

        try:
            selected = False

            # Strategy 1: By label
            if label:
                try:
                    locator = page.get_by_label(label, exact=False)
                    if locator.count() > 0:
                        locator.first.select_option(label=value, timeout=5000)
                        selected = True
                except Exception:
                    # Try by value instead
                    try:
                        locator.first.select_option(value=value, timeout=5000)
                        selected = True
                    except Exception:
                        pass

            # Strategy 2: By name
            if not selected and name:
                try:
                    locator = page.locator(f'select[name="{name}"]')
                    if locator.count() > 0:
                        try:
                            locator.first.select_option(label=value, timeout=5000)
                            selected = True
                        except Exception:
                            locator.first.select_option(value=value, timeout=5000)
                            selected = True
                except Exception:
                    pass

            if selected:
                time.sleep(0.3)
                self.logger.info(f"Selected option: {value}")
                return True

            self.logger.warning(f"Could not select option: {value}")
            return False

        except Exception as e:
            self.logger.error(f"Select failed: {e}")
            return False

    def click_link(self, page: Page, link_text: str) -> bool:
        """
        Click a link by text.

        Args:
            page: Playwright page
            link_text: Link text to click

        Returns:
            True if successful
        """
        self.logger.action('CLICK_LINK', {'text': link_text})

        try:
            locator = page.get_by_role('link', name=link_text, exact=False)

            if locator.count() > 0:
                locator.first.click(timeout=5000)
                time.sleep(self.config.get('automation.action_delay', 1000) / 1000)
                self.logger.info(f"Clicked link: {link_text}")
                return True

            self.logger.warning(f"Could not find link: {link_text}")
            return False

        except Exception as e:
            self.logger.error(f"Click link failed: {e}")
            return False
