"""
COMPLETE UNIVERSAL EXTRACTOR - Pulls EVERYTHING from a page.
Single JSON output with ALL data structured and ready for AI.
"""

from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from bs4 import BeautifulSoup
import json
import re


class CompleteUniversalExtractor:
    """The ultimate single-call extractor - returns complete page state."""

    def __init__(self, logger):
        self.logger = logger

    def extract_complete_page(self, page: Page, html: str) -> Dict[str, Any]:
        """
        Extract EVERYTHING from page in one structured JSON.

        Returns:
            Complete page state with:
            - metadata
            - interactive_elements (buttons, inputs, links, selects, etc.)
            - hidden_data (fields, tokens, storage)
            - page_state (current state, platform, requirements)
            - content (text, structure, media)
            - javascript_context
            - validation_rules
        """
        self.logger.info("COMPLETE UNIVERSAL EXTRACTION - Pulling everything...")

        soup = BeautifulSoup(html, 'lxml')

        # Build complete extraction
        complete = {
            # Page metadata
            'metadata': self._extract_metadata(page, soup),

            # All interactive elements in one place
            'interactive_elements': {
                'buttons': self._extract_buttons_complete(soup),
                'inputs': self._extract_inputs_complete(soup),
                'selects': self._extract_selects_complete(soup),
                'links': self._extract_links_complete(soup),
                'textareas': self._extract_textareas(soup),
                'checkboxes': self._extract_checkboxes(soup),
                'radios': self._extract_radios(soup),
                'file_uploads': self._extract_file_uploads(soup),
            },

            # Hidden data and tokens
            'hidden_data': {
                'hidden_fields': self._extract_hidden_fields(soup),
                'csrf_tokens': self._extract_csrf_tokens(soup),
                'local_storage': self._safe_extract_storage(page, 'localStorage'),
                'session_storage': self._safe_extract_storage(page, 'sessionStorage'),
                'cookies': self._safe_extract_cookies(page),
                'data_attributes': self._extract_all_data_attrs(soup),
            },

            # Page state and platform detection
            'page_state': {
                'platform': self._detect_platform(page.url, html),
                'page_type': self._detect_page_type(soup),
                'has_forms': len(soup.find_all('form')) > 0,
                'form_count': len(soup.find_all('form')),
                'required_fields': self._extract_required_fields(soup),
                'validation_rules': self._extract_validation_rules(soup),
                'frameworks': self._detect_frameworks(page),
            },

            # Content and structure
            'content': {
                'page_text': self._extract_clean_text(soup),
                'headings': self._extract_headings(soup),
                'semantic_structure': self._extract_semantic_tags(soup),
                'meta_tags': self._extract_meta_tags(soup),
                'title': page.title(),
            },

            # JavaScript context
            'javascript': {
                'window_data': self._safe_eval(page, self._get_window_script()),
                'global_vars': self._safe_eval(page, self._get_globals_script()),
            },

            # API and network hints
            'api_hints': {
                'endpoints': self._extract_api_endpoints(soup),
                'graphql_detected': self._detect_graphql(page),
            },

            # Element counts for quick overview
            'stats': {}
        }

        # Calculate stats
        complete['stats'] = self._calculate_complete_stats(complete)

        self.logger.info(f"EXTRACTION COMPLETE: {complete['stats']['total_elements']} elements extracted")

        return complete

    # ==================== METADATA ====================

    def _extract_metadata(self, page: Page, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata."""
        return {
            'url': page.url,
            'title': page.title(),
            'viewport': page.viewport_size,
            'charset': self._get_charset(soup),
            'language': soup.html.get('lang', '') if soup.html else '',
        }

    def _get_charset(self, soup: BeautifulSoup) -> str:
        """Get page charset."""
        charset_meta = soup.find('meta', charset=True)
        if charset_meta:
            return charset_meta.get('charset', 'utf-8')
        return 'utf-8'

    # ==================== BUTTONS ====================

    def _extract_buttons_complete(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all buttons with complete context."""
        buttons = []

        # Find all button-like elements (INCLUDING CUSTOM WEB COMPONENTS!)
        # 1. Regular buttons and inputs
        for elem in soup.find_all(['button', 'input']):
            if elem.name == 'input' and elem.get('type') not in ['submit', 'button']:
                continue

            buttons.append({
                'text': elem.get_text(strip=True) or elem.get('value', ''),
                'tag': elem.name,
                'type': elem.get('type', 'button'),
                'id': elem.get('id', ''),
                'name': elem.get('name', ''),
                'class': elem.get('class', []),
                'aria_label': elem.get('aria-label', ''),
                'disabled': elem.get('disabled') is not None,
                'purpose': self._detect_button_purpose(elem),
                'form_id': elem.get('form', ''),
                'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                'selectors': self._generate_selectors(elem),
            })

        # 2. Clickable divs/spans with role="button"
        for elem in soup.find_all(attrs={'role': 'button'}):
            if elem.name not in ['button', 'input']:
                buttons.append({
                    'text': elem.get_text(strip=True),
                    'tag': elem.name,
                    'type': 'clickable',
                    'id': elem.get('id', ''),
                    'name': '',
                    'class': elem.get('class', []),
                    'aria_label': elem.get('aria-label', ''),
                    'disabled': False,
                    'purpose': self._detect_button_purpose(elem),
                    'form_id': '',
                    'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                    'selectors': self._generate_selectors(elem),
                })

        # 3. CUSTOM WEB COMPONENTS (ukg-button, ion-button, mat-button, etc.)
        # Look for elements with data-tag-name="button" or names ending in "-button"
        for elem in soup.find_all():
            # Check if it's a custom button element
            if (elem.name.endswith('-button') or
                elem.get('data-tag-name') == 'button' or
                'button' in elem.get('class', []) or
                'btn' in elem.get('class', [])):

                # Skip if already added
                if elem.name in ['button', 'input']:
                    continue

                # Get text content
                text = elem.get_text(strip=True)
                if not text:  # Skip empty elements
                    continue

                buttons.append({
                    'text': text,
                    'tag': elem.name,
                    'type': 'custom-component',
                    'id': elem.get('id', ''),
                    'name': elem.get('name', ''),
                    'class': elem.get('class', []),
                    'aria_label': elem.get('aria-label', ''),
                    'disabled': elem.get('disabled') is not None,
                    'purpose': self._detect_button_purpose(elem),
                    'form_id': '',
                    'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                    'selectors': self._generate_selectors(elem),
                })

        return buttons

    def _detect_button_purpose(self, elem) -> str:
        """Detect button purpose."""
        text = elem.get_text(strip=True).lower()
        aria = elem.get('aria-label', '').lower()
        combined = f"{text} {aria}"

        patterns = {
            'apply': ['apply', 'apply now', 'submit application'],
            'submit': ['submit', 'send', 'confirm'],
            'next': ['next', 'continue', 'proceed'],
            'back': ['back', 'previous'],
            'signin': ['sign in', 'log in', 'login'],
            'signup': ['sign up', 'register', 'create account'],
            'cancel': ['cancel', 'close', 'dismiss'],
            'save': ['save'],
            'upload': ['upload', 'choose file'],
        }

        for purpose, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                return purpose

        return 'unknown'

    # ==================== INPUTS ====================

    def _extract_inputs_complete(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all input fields with complete context."""
        inputs = []

        for elem in soup.find_all('input'):
            # Skip buttons, checkboxes, radios, files, hidden (handled separately)
            input_type = elem.get('type', 'text')
            if input_type in ['submit', 'button', 'checkbox', 'radio', 'file', 'hidden']:
                continue

            inputs.append({
                'label': self._find_label(elem, soup),
                'placeholder': elem.get('placeholder', ''),
                'type': input_type,
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'value': elem.get('value', ''),
                'purpose': self._detect_input_purpose(elem, soup),
                'required': elem.get('required') is not None,
                'disabled': elem.get('disabled') is not None,
                'readonly': elem.get('readonly') is not None,
                'autocomplete': elem.get('autocomplete', ''),
                'pattern': elem.get('pattern', ''),
                'min': elem.get('min', ''),
                'max': elem.get('max', ''),
                'minlength': elem.get('minlength', ''),
                'maxlength': elem.get('maxlength', ''),
                'aria_label': elem.get('aria-label', ''),
                'aria_required': elem.get('aria-required', ''),
                'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                'selectors': self._generate_selectors(elem),
            })

        return inputs

    def _detect_input_purpose(self, elem, soup: BeautifulSoup) -> str:
        """Detect input purpose from context."""
        # Check autocomplete first (most reliable)
        autocomplete = elem.get('autocomplete', '').lower()
        if autocomplete and autocomplete != 'off':
            return autocomplete

        # Check type
        input_type = elem.get('type', '').lower()
        if input_type in ['email', 'password', 'tel', 'url']:
            return input_type

        # Analyze text clues
        name = elem.get('name', '').lower()
        id_attr = elem.get('id', '').lower()
        placeholder = elem.get('placeholder', '').lower()
        label = self._find_label(elem, soup).lower()
        aria = elem.get('aria-label', '').lower()

        combined = f"{name} {id_attr} {placeholder} {label} {aria}"

        patterns = {
            'email': ['email', 'e-mail'],
            'password': ['password', 'passwd', 'pwd'],
            'given-name': ['first name', 'firstname', 'fname'],
            'family-name': ['last name', 'lastname', 'lname', 'surname'],
            'name': ['full name', 'name'],
            'tel': ['phone', 'telephone', 'mobile'],
            'address-line1': ['address', 'street'],
            'address-level2': ['city'],
            'address-level1': ['state', 'province'],
            'postal-code': ['zip', 'postal'],
            'country': ['country'],
            'url': ['website', 'url'],
            'linkedin': ['linkedin'],
            'github': ['github'],
        }

        for purpose, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                return purpose

        return 'unknown'

    # ==================== SELECTS ====================

    def _extract_selects_complete(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all select dropdowns."""
        selects = []

        for elem in soup.find_all('select'):
            options = []
            for opt in elem.find_all('option'):
                options.append({
                    'value': opt.get('value', ''),
                    'text': opt.get_text(strip=True),
                    'selected': opt.get('selected') is not None,
                })

            selects.append({
                'label': self._find_label(elem, soup),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'purpose': self._detect_select_purpose(elem, soup),
                'required': elem.get('required') is not None,
                'disabled': elem.get('disabled') is not None,
                'multiple': elem.get('multiple') is not None,
                'options': options,
                'option_count': len(options),
                'aria_label': elem.get('aria-label', ''),
                'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                'selectors': self._generate_selectors(elem),
            })

        return selects

    def _detect_select_purpose(self, elem, soup: BeautifulSoup) -> str:
        """Detect select purpose."""
        name = elem.get('name', '').lower()
        label = self._find_label(elem, soup).lower()
        combined = f"{name} {label}"

        patterns = {
            'country': ['country'],
            'state': ['state', 'province'],
            'gender': ['gender'],
            'education': ['education', 'degree'],
            'experience': ['experience', 'years'],
            'work-authorization': ['work authorization', 'visa'],
        }

        for purpose, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                return purpose

        return 'unknown'

    # ==================== OTHER ELEMENTS ====================

    def _extract_links_complete(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all links."""
        links = []
        for elem in soup.find_all('a'):
            links.append({
                'text': elem.get_text(strip=True),
                'href': elem.get('href', ''),
                'target': elem.get('target', ''),
                'aria_label': elem.get('aria-label', ''),
                'class': elem.get('class', []),
                'id': elem.get('id', ''),
                'selectors': self._generate_selectors(elem),
            })
        return links

    def _extract_textareas(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract textareas."""
        textareas = []
        for elem in soup.find_all('textarea'):
            textareas.append({
                'label': self._find_label(elem, soup),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'placeholder': elem.get('placeholder', ''),
                'required': elem.get('required') is not None,
                'rows': elem.get('rows', ''),
                'cols': elem.get('cols', ''),
                'maxlength': elem.get('maxlength', ''),
                'aria_label': elem.get('aria-label', ''),
                'selectors': self._generate_selectors(elem),
            })
        return textareas

    def _extract_checkboxes(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract checkboxes."""
        checkboxes = []
        for elem in soup.find_all('input', type='checkbox'):
            checkboxes.append({
                'label': self._find_label(elem, soup),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'value': elem.get('value', ''),
                'checked': elem.get('checked') is not None,
                'required': elem.get('required') is not None,
                'aria_label': elem.get('aria-label', ''),
                'selectors': self._generate_selectors(elem),
            })
        return checkboxes

    def _extract_radios(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract radio buttons."""
        radios = []
        for elem in soup.find_all('input', type='radio'):
            radios.append({
                'label': self._find_label(elem, soup),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'value': elem.get('value', ''),
                'checked': elem.get('checked') is not None,
                'aria_label': elem.get('aria-label', ''),
                'selectors': self._generate_selectors(elem),
            })
        return radios

    def _extract_file_uploads(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract file upload fields."""
        uploads = []
        for elem in soup.find_all('input', type='file'):
            uploads.append({
                'label': self._find_label(elem, soup),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'accept': elem.get('accept', ''),
                'multiple': elem.get('multiple') is not None,
                'required': elem.get('required') is not None,
                'purpose': self._detect_file_purpose(elem, soup),
                'aria_label': elem.get('aria-label', ''),
                'selectors': self._generate_selectors(elem),
            })
        return uploads

    def _detect_file_purpose(self, elem, soup: BeautifulSoup) -> str:
        """Detect file upload purpose."""
        label = self._find_label(elem, soup).lower()
        name = elem.get('name', '').lower()
        combined = f"{label} {name}"

        if 'resume' in combined or 'cv' in combined:
            return 'resume'
        if 'cover' in combined:
            return 'cover-letter'
        if 'transcript' in combined:
            return 'transcript'

        return 'document'

    # ==================== HIDDEN DATA ====================

    def _extract_hidden_fields(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract hidden input fields."""
        hidden = []
        for elem in soup.find_all('input', type='hidden'):
            hidden.append({
                'name': elem.get('name', ''),
                'value': elem.get('value', ''),
                'id': elem.get('id', ''),
            })
        return hidden

    def _extract_csrf_tokens(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract CSRF tokens."""
        tokens = []
        csrf_patterns = ['csrf', 'xsrf', '_token', 'authenticity', 'requestverification']

        for elem in soup.find_all('input', type='hidden'):
            name = elem.get('name', '').lower()
            if any(pattern in name for pattern in csrf_patterns):
                tokens.append({
                    'name': elem.get('name', ''),
                    'value': elem.get('value', '')[:50],  # Truncate for safety
                })

        return tokens

    def _safe_extract_storage(self, page: Page, storage_type: str) -> Dict[str, Any]:
        """Safely extract localStorage or sessionStorage."""
        try:
            script = f"""
                () => {{
                    const storage = {{}};
                    for (let i = 0; i < {storage_type}.length; i++) {{
                        const key = {storage_type}.key(i);
                        storage[key] = {storage_type}.getItem(key);
                    }}
                    return storage;
                }}
            """
            result = page.evaluate(script)
            return result if result is not None else {}
        except:
            return {}

    def _safe_extract_cookies(self, page: Page) -> List[Dict[str, Any]]:
        """Safely extract cookies."""
        try:
            return page.context.cookies()
        except:
            return []

    def _extract_all_data_attrs(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all elements with data-* attributes."""
        data_elements = []

        for elem in soup.find_all():
            if not hasattr(elem, 'attrs'):
                continue

            data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
            if data_attrs:
                data_elements.append({
                    'tag': elem.name,
                    'id': elem.get('id', ''),
                    'data': data_attrs
                })

        return data_elements[:50]  # Limit to first 50

    # ==================== PAGE STATE ====================

    def _detect_platform(self, url: str, html: str) -> str:
        """Detect job board platform."""
        url_lower = url.lower()
        html_lower = html.lower()

        platforms = {
            'greenhouse': ['greenhouse.io', 'grnh.se'],
            'lever': ['lever.co'],
            'workday': ['myworkdayjobs.com', 'workday'],
            'taleo': ['taleo.net'],
            'icims': ['icims.com'],
            'ultipro': ['ultipro.com'],
            'smartrecruiters': ['smartrecruiters.com'],
            'jobvite': ['jobvite.com'],
            'linkedin': ['linkedin.com/jobs'],
            'indeed': ['indeed.com'],
        }

        for platform, indicators in platforms.items():
            if any(ind in url_lower or ind in html_lower for ind in indicators):
                return platform

        return 'unknown'

    def _detect_page_type(self, soup: BeautifulSoup) -> str:
        """Detect current page type."""
        text = soup.get_text(separator=' ', strip=True).lower()

        if any(phrase in text for phrase in ['application submitted', 'thank you for applying']):
            return 'confirmation'
        if any(phrase in text for phrase in ['sign in', 'log in', 'login']):
            return 'login'
        if any(phrase in text for phrase in ['create account', 'sign up']):
            return 'signup'
        if len(soup.find_all('form')) > 0:
            return 'form'

        return 'content'

    def _extract_required_fields(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all required fields."""
        required = []
        for elem in soup.find_all(['input', 'select', 'textarea'], required=True):
            required.append({
                'tag': elem.name,
                'type': elem.get('type', ''),
                'name': elem.get('name', ''),
                'label': self._find_label(elem, soup),
            })
        return required

    def _extract_validation_rules(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract validation rules."""
        rules = []
        for elem in soup.find_all(['input', 'textarea']):
            rule = {
                'name': elem.get('name', ''),
                'required': elem.get('required') is not None,
                'pattern': elem.get('pattern', ''),
                'min': elem.get('min', ''),
                'max': elem.get('max', ''),
                'minlength': elem.get('minlength', ''),
                'maxlength': elem.get('maxlength', ''),
            }
            if any([rule['required'], rule['pattern'], rule['min'], rule['max']]):
                rules.append(rule)
        return rules

    def _detect_frameworks(self, page: Page) -> Dict[str, Any]:
        """Detect JavaScript frameworks."""
        try:
            result = page.evaluate("""
                () => {
                    return {
                        react: !!window.React || !!document.querySelector('[data-reactroot]'),
                        vue: !!window.Vue || !!window.__VUE__,
                        angular: !!document.querySelector('[ng-version]'),
                    };
                }
            """)
            return result if result is not None else {}
        except:
            return {}

    # ==================== CONTENT ====================

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean page text."""
        for elem in soup(['script', 'style', 'noscript']):
            elem.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())

        # Limit to 8000 chars to avoid token limits
        if len(text) > 8000:
            return text[:8000] + "... [truncated]"

        return text

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract headings."""
        headings = []
        for tag in ['h1', 'h2', 'h3', 'h4']:
            for elem in soup.find_all(tag):
                headings.append({
                    'level': tag,
                    'text': elem.get_text(strip=True)
                })
        return headings[:20]

    def _extract_semantic_tags(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract semantic HTML5 tag counts."""
        tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        return {tag: len(soup.find_all(tag)) for tag in tags}

    def _extract_meta_tags(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract meta tags."""
        metas = []
        for meta in soup.find_all('meta'):
            metas.append({
                'name': meta.get('name', ''),
                'property': meta.get('property', ''),
                'content': meta.get('content', ''),
            })
        return metas[:20]

    # ==================== JAVASCRIPT ====================

    def _safe_eval(self, page: Page, script: str) -> Any:
        """Safely evaluate JavaScript."""
        try:
            result = page.evaluate(script)
            return result if result is not None else {}
        except:
            return {}

    def _get_window_script(self) -> str:
        """Get window data extraction script."""
        return """
            () => ({
                location: {
                    href: window.location.href,
                    pathname: window.location.pathname,
                    search: window.location.search,
                },
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
            })
        """

    def _get_globals_script(self) -> str:
        """Get global variables extraction script."""
        return """
            () => {
                const globals = {};
                const checkVars = ['appConfig', 'jobData', 'formData', '__NEXT_DATA__', '__NUXT__'];
                for (const varName of checkVars) {
                    if (typeof window[varName] !== 'undefined') {
                        try {
                            globals[varName] = JSON.parse(JSON.stringify(window[varName]));
                        } catch (e) {
                            globals[varName] = String(window[varName]);
                        }
                    }
                }
                return globals;
            }
        """

    # ==================== API HINTS ====================

    def _extract_api_endpoints(self, soup: BeautifulSoup) -> List[str]:
        """Extract API endpoint hints from scripts."""
        endpoints = set()

        for script in soup.find_all('script'):
            text = script.get_text()
            patterns = [
                r'["\']([^"\']*(?:/api/|/v\d+/|/graphql)[^"\']*)["\']',
                r'fetch\(["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text)
                endpoints.update(matches)

        return list(endpoints)[:20]

    def _detect_graphql(self, page: Page) -> bool:
        """Detect GraphQL usage."""
        try:
            result = page.evaluate("""
                () => !!(window.__APOLLO_STATE__ || window.__RELAY_STORE__)
            """)
            return result if result is not None else False
        except:
            return False

    # ==================== HELPERS ====================

    def _find_label(self, elem, soup: BeautifulSoup) -> str:
        """Find label for element."""
        # Check for label by 'for' attribute
        elem_id = elem.get('id')
        if elem_id:
            label = soup.find('label', attrs={'for': elem_id})
            if label:
                return label.get_text(strip=True)

        # Check parent label
        parent = elem.find_parent('label')
        if parent:
            return parent.get_text(strip=True)

        return ''

    def _generate_selectors(self, elem) -> Dict[str, str]:
        """Generate multiple selectors for element."""
        selectors = {}

        if elem.get('id'):
            selectors['id'] = f"#{elem['id']}"

        if elem.get('name'):
            selectors['name'] = f"[name='{elem['name']}']"

        if elem.get('aria-label'):
            selectors['aria_label'] = f"[aria-label='{elem['aria-label']}']"

        return selectors

    def _calculate_complete_stats(self, complete: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics."""
        ie = complete['interactive_elements']

        return {
            'total_elements': (
                len(ie['buttons']) +
                len(ie['inputs']) +
                len(ie['selects']) +
                len(ie['links']) +
                len(ie['textareas']) +
                len(ie['checkboxes']) +
                len(ie['radios']) +
                len(ie['file_uploads'])
            ),
            'buttons': len(ie['buttons']),
            'inputs': len(ie['inputs']),
            'selects': len(ie['selects']),
            'links': len(ie['links']),
            'textareas': len(ie['textareas']),
            'checkboxes': len(ie['checkboxes']),
            'radios': len(ie['radios']),
            'file_uploads': len(ie['file_uploads']),
            'hidden_fields': len(complete['hidden_data']['hidden_fields']),
            'required_fields': len(complete['page_state']['required_fields']),
            'platform': complete['page_state']['platform'],
            'page_type': complete['page_state']['page_type'],
        }
