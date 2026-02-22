"""
DOM element extraction and inventory.
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from playwright.sync_api import Page, ElementHandle


class DOMExtractor:
    """Extracts structured element inventory from DOM."""

    def __init__(self, logger):
        """
        Initialize DOM extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract(self, page: Page, html: str) -> Dict[str, Any]:
        """
        Extract element inventory from page.

        Args:
            page: Playwright page instance
            html: HTML content

        Returns:
            Element inventory
        """
        self.logger.debug("Extracting DOM element inventory...")

        soup = BeautifulSoup(html, 'lxml')

        inventory = {
            'inputs': self._extract_inputs(page, soup),
            'buttons': self._extract_buttons(page, soup),
            'links': self._extract_links(page, soup),
            'forms': self._extract_forms(soup),
            'headings': self._extract_headings(soup)
        }

        self.logger.debug(
            f"DOM extraction: {len(inventory['inputs'])} inputs, "
            f"{len(inventory['buttons'])} buttons, "
            f"{len(inventory['links'])} links"
        )

        return inventory

    def _extract_inputs(self, page: Page, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all form inputs with context."""
        inputs = []

        # Find all input, textarea, select elements
        elements = soup.find_all(['input', 'textarea', 'select'])

        for elem in elements:
            input_data = {
                'tag': elem.name,
                'type': elem.get('type', 'text'),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'placeholder': elem.get('placeholder', ''),
                'aria_label': elem.get('aria-label', ''),
                'aria_labelledby': elem.get('aria-labelledby', ''),
                'required': elem.get('required') is not None,
                'autocomplete': elem.get('autocomplete', ''),
                'value': elem.get('value', ''),
                'disabled': elem.get('disabled') is not None,
                'class': ' '.join(elem.get('class', [])),
            }

            # Extract label text
            input_data['label'] = self._find_label_text(elem, soup)

            # Extract nearby context text
            input_data['context'] = self._get_context_text(elem)

            # Detect input purpose by semantic analysis
            input_data['purpose'] = self._detect_input_purpose(input_data)

            inputs.append(input_data)

        return inputs

    def _extract_buttons(self, page: Page, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all buttons and clickable elements (INCLUDING CUSTOM WEB COMPONENTS!)."""
        buttons = []

        # 1. Find button elements
        button_elements = soup.find_all(['button', 'input'])

        for elem in button_elements:
            if elem.name == 'input' and elem.get('type') not in ['submit', 'button']:
                continue

            button_data = {
                'tag': elem.name,
                'type': elem.get('type', 'button'),
                'text': elem.get_text(strip=True) or elem.get('value', ''),
                'aria_label': elem.get('aria-label', ''),
                'disabled': elem.get('disabled') is not None,
                'class': ' '.join(elem.get('class', [])),
                'role': elem.get('role', ''),
            }

            # Detect button purpose
            button_data['purpose'] = self._detect_button_purpose(button_data)

            buttons.append(button_data)

        # 2. Also find clickable divs/spans with role="button"
        clickable = soup.find_all(attrs={'role': 'button'})
        for elem in clickable:
            if elem.name not in ['button', 'input']:
                buttons.append({
                    'tag': elem.name,
                    'type': 'clickable',
                    'text': elem.get_text(strip=True),
                    'aria_label': elem.get('aria-label', ''),
                    'disabled': False,
                    'class': ' '.join(elem.get('class', [])),
                    'role': 'button',
                    'purpose': self._detect_button_purpose({'text': elem.get_text(strip=True)})
                })

        # 3. CUSTOM WEB COMPONENTS (ukg-button, ion-button, mat-button, etc.)
        for elem in soup.find_all():
            # Check if it's a custom button element
            if (elem.name.endswith('-button') or
                elem.get('data-tag-name') == 'button'):

                # Skip if already added
                if elem.name in ['button', 'input']:
                    continue

                text = elem.get_text(strip=True)
                if not text:  # Skip empty
                    continue

                buttons.append({
                    'tag': elem.name,
                    'type': 'custom-component',
                    'text': text,
                    'aria_label': elem.get('aria-label', ''),
                    'disabled': elem.get('disabled') is not None,
                    'class': ' '.join(elem.get('class', [])),
                    'role': elem.get('role', ''),
                    'purpose': self._detect_button_purpose({'text': text})
                })

        return buttons

    def _extract_links(self, page: Page, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all links."""
        links = []

        for elem in soup.find_all('a'):
            links.append({
                'href': elem.get('href', ''),
                'text': elem.get_text(strip=True),
                'aria_label': elem.get('aria-label', ''),
                'class': ' '.join(elem.get('class', [])),
            })

        return links

    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form elements."""
        forms = []

        for elem in soup.find_all('form'):
            forms.append({
                'action': elem.get('action', ''),
                'method': elem.get('method', 'get'),
                'id': elem.get('id', ''),
                'class': ' '.join(elem.get('class', [])),
            })

        return forms

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract heading elements."""
        headings = []

        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for elem in soup.find_all(tag):
                headings.append({
                    'level': tag,
                    'text': elem.get_text(strip=True)
                })

        return headings

    def _find_label_text(self, input_elem, soup: BeautifulSoup) -> str:
        """Find associated label text for an input."""
        # Check for label by 'for' attribute
        input_id = input_elem.get('id')
        if input_id:
            label = soup.find('label', attrs={'for': input_id})
            if label:
                return label.get_text(strip=True)

        # Check for parent label
        parent = input_elem.find_parent('label')
        if parent:
            return parent.get_text(strip=True)

        return ''

    def _get_context_text(self, elem) -> str:
        """Get surrounding context text for an element."""
        # Get text from parent container
        parent = elem.find_parent(['div', 'fieldset', 'section'])
        if parent:
            text = parent.get_text(strip=True)
            # Limit to reasonable length
            return text[:200] if len(text) > 200 else text

        return ''

    def _detect_input_purpose(self, input_data: Dict[str, Any]) -> str:
        """
        Detect the semantic purpose of an input field.

        Returns:
            Purpose string (email, password, name, phone, etc.)
        """
        # Check autocomplete attribute (most reliable)
        autocomplete = input_data.get('autocomplete', '').lower()
        if autocomplete:
            return autocomplete

        # Check type
        input_type = input_data.get('type', '').lower()
        if input_type in ['email', 'password', 'tel', 'url']:
            return input_type

        # Check name attribute
        name = input_data.get('name', '').lower()
        label = input_data.get('label', '').lower()
        placeholder = input_data.get('placeholder', '').lower()
        aria = input_data.get('aria_label', '').lower()

        combined_text = f"{name} {label} {placeholder} {aria}"

        # Detect common patterns
        if any(k in combined_text for k in ['email', 'e-mail']):
            return 'email'
        if any(k in combined_text for k in ['password', 'passwd', 'pwd']):
            return 'password'
        if any(k in combined_text for k in ['first name', 'firstname', 'fname']):
            return 'given-name'
        if any(k in combined_text for k in ['last name', 'lastname', 'lname', 'surname']):
            return 'family-name'
        if any(k in combined_text for k in ['phone', 'telephone', 'mobile']):
            return 'tel'
        if any(k in combined_text for k in ['address']):
            return 'address'
        if any(k in combined_text for k in ['city']):
            return 'address-level2'
        if any(k in combined_text for k in ['state', 'province']):
            return 'address-level1'
        if any(k in combined_text for k in ['zip', 'postal']):
            return 'postal-code'
        if any(k in combined_text for k in ['country']):
            return 'country'
        if any(k in combined_text for k in ['linkedin']):
            return 'linkedin'
        if any(k in combined_text for k in ['github']):
            return 'github'
        if any(k in combined_text for k in ['portfolio', 'website']):
            return 'url'
        if any(k in combined_text for k in ['resume', 'cv']):
            return 'resume'
        if any(k in combined_text for k in ['cover letter']):
            return 'cover-letter'

        return 'unknown'

    def _detect_button_purpose(self, button_data: Dict[str, Any]) -> str:
        """
        Detect the semantic purpose of a button.

        Returns:
            Purpose string (submit, next, apply, etc.)
        """
        text = button_data.get('text', '').lower()
        aria = button_data.get('aria_label', '').lower()

        combined = f"{text} {aria}"

        if any(k in combined for k in ['submit', 'send', 'confirm']):
            return 'submit'
        if any(k in combined for k in ['apply', 'apply now']):
            return 'apply'
        if any(k in combined for k in ['next', 'continue', 'proceed']):
            return 'next'
        if any(k in combined for k in ['back', 'previous']):
            return 'back'
        if any(k in combined for k in ['sign in', 'log in', 'login']):
            return 'signin'
        if any(k in combined for k in ['sign up', 'register', 'create account']):
            return 'signup'
        if any(k in combined for k in ['cancel', 'close']):
            return 'cancel'
        if any(k in combined for k in ['save']):
            return 'save'
        if any(k in combined for k in ['upload']):
            return 'upload'

        return 'unknown'
