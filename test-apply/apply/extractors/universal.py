"""
Universal deep extraction - captures EVERYTHING from a page.
This is the most comprehensive extractor possible.
"""

from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from bs4 import BeautifulSoup
import json
import re


class UniversalExtractor:
    """The ultimate page extractor - captures everything."""

    def __init__(self, logger):
        """
        Initialize universal extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract_everything(self, page: Page, html: str) -> Dict[str, Any]:
        """
        Extract EVERYTHING from the page.

        Args:
            page: Playwright page instance
            html: HTML content

        Returns:
            Comprehensive extraction results
        """
        self.logger.info("Starting DEEP UNIVERSAL EXTRACTION...")

        extraction = {
            # Core content
            'html_structure': self._extract_html_structure(html),
            'metadata': self._extract_metadata(html, page),

            # Interactive elements (enhanced)
            'forms': self._extract_forms_deep(html, page),
            'inputs': self._extract_inputs_deep(html, page),
            'buttons': self._extract_buttons_deep(html, page),
            'links': self._extract_links_deep(html, page),
            'selects': self._extract_selects_deep(html, page),

            # Hidden data
            'data_attributes': self._extract_data_attributes(html),
            'hidden_fields': self._extract_hidden_fields(html),
            'meta_tags': self._extract_meta_tags(html),

            # JavaScript context
            'window_data': self._extract_window_data(page),
            'local_storage': self._extract_local_storage(page),
            'session_storage': self._extract_session_storage(page),
            'cookies': self._extract_cookies(page),
            'global_variables': self._extract_global_variables(page),

            # Dynamic content
            'react_state': self._extract_react_state(page),
            'vue_state': self._extract_vue_state(page),
            'angular_state': self._extract_angular_state(page),
            'computed_styles': self._extract_computed_styles(page),

            # Advanced features
            'iframes': self._extract_iframes(page),
            'shadow_dom': self._extract_shadow_dom(page),
            'web_components': self._extract_web_components(html),
            'canvas_data': self._extract_canvas_data(page),
            'svg_data': self._extract_svg_data(html),

            # Accessibility & ARIA
            'aria_tree': self._extract_aria_tree(html),
            'accessibility_tree': self._extract_accessibility_tree(page),
            'focus_management': self._extract_focus_data(page),

            # Validation & constraints
            'form_validation': self._extract_validation_rules(html),
            'input_constraints': self._extract_input_constraints(html),
            'required_fields': self._extract_required_fields(html),

            # Scripts & resources
            'scripts': self._extract_scripts(html),
            'stylesheets': self._extract_stylesheets(html),
            'resources': self._extract_resources(html),

            # Network & API
            'api_endpoints': self._extract_api_endpoints(html, page),
            'graphql_schemas': self._extract_graphql_schemas(page),
            'websockets': self._extract_websocket_data(page),

            # Job application specific
            'job_data': self._extract_job_data(html, page),
            'application_schema': self._extract_application_schema(page),
            'file_upload_requirements': self._extract_file_upload_info(html),

            # Page state & behavior
            'page_state': self._extract_page_state(html, page),
            'event_listeners': self._extract_event_listeners(page),
            'timers_intervals': self._extract_timers(page),

            # Security & auth
            'csrf_tokens': self._extract_csrf_tokens(html),
            'auth_tokens': self._extract_auth_tokens(page),
            'security_headers': self._extract_security_headers(page),

            # Content analysis
            'text_analysis': self._extract_text_analysis(html),
            'semantic_structure': self._extract_semantic_structure(html),
            'language_detection': self._extract_language_data(html),
        }

        # Calculate extraction stats
        extraction['_stats'] = self._calculate_stats(extraction)

        self.logger.info(f"EXTRACTION COMPLETE: {extraction['_stats']['total_data_points']} data points extracted")

        return extraction

    # ==================== HTML STRUCTURE ====================

    def _extract_html_structure(self, html: str) -> Dict[str, Any]:
        """Extract HTML document structure."""
        soup = BeautifulSoup(html, 'lxml')

        return {
            'doctype': str(soup.find('!doctype')) if soup.find('!doctype') else None,
            'html_attrs': dict(soup.html.attrs) if soup.html else {},
            'head_content': self._extract_head_content(soup),
            'body_attrs': dict(soup.body.attrs) if soup.body else {},
            'element_counts': {
                'total_elements': len(soup.find_all()),
                'divs': len(soup.find_all('div')),
                'spans': len(soup.find_all('span')),
                'inputs': len(soup.find_all('input')),
                'buttons': len(soup.find_all('button')),
                'forms': len(soup.find_all('form')),
                'scripts': len(soup.find_all('script')),
            }
        }

    def _extract_head_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract head section content."""
        head = soup.head
        if not head:
            return {}

        return {
            'title': head.title.string if head.title else None,
            'base_url': head.base.get('href') if head.base else None,
            'meta_count': len(head.find_all('meta')),
            'link_count': len(head.find_all('link')),
            'script_count': len(head.find_all('script')),
        }

    # ==================== METADATA ====================

    def _extract_metadata(self, html: str, page: Page) -> Dict[str, Any]:
        """Extract page metadata."""
        soup = BeautifulSoup(html, 'lxml')

        return {
            'url': page.url,
            'title': page.title(),
            'viewport': page.viewport_size,
            'user_agent': page.evaluate("navigator.userAgent"),
            'platform': page.evaluate("navigator.platform"),
            'language': page.evaluate("navigator.language"),
            'online': page.evaluate("navigator.onLine"),
            'cookie_enabled': page.evaluate("navigator.cookieEnabled"),
            'charset': self._extract_charset(soup),
        }

    def _extract_charset(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page charset."""
        charset_meta = soup.find('meta', charset=True)
        if charset_meta:
            return charset_meta.get('charset')

        content_type = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        if content_type and content_type.get('content'):
            match = re.search(r'charset=([^;]+)', content_type.get('content'))
            if match:
                return match.group(1)

        return None

    # ==================== FORMS - DEEP ====================

    def _extract_forms_deep(self, html: str, page: Page) -> List[Dict[str, Any]]:
        """Extract comprehensive form data."""
        soup = BeautifulSoup(html, 'lxml')
        forms = []

        for form in soup.find_all('form'):
            form_data = {
                'tag': 'form',
                'action': form.get('action', ''),
                'method': form.get('method', 'get').upper(),
                'id': form.get('id', ''),
                'name': form.get('name', ''),
                'class': ' '.join(form.get('class', [])),
                'enctype': form.get('enctype', 'application/x-www-form-urlencoded'),
                'autocomplete': form.get('autocomplete', ''),
                'novalidate': form.get('novalidate') is not None,
                'target': form.get('target', ''),
                'accept_charset': form.get('accept-charset', ''),

                # All data attributes
                'data_attributes': {k: v for k, v in form.attrs.items() if k.startswith('data-')},

                # Children count
                'input_count': len(form.find_all('input')),
                'select_count': len(form.find_all('select')),
                'textarea_count': len(form.find_all('textarea')),
                'button_count': len(form.find_all('button')),

                # Try to get computed properties
                'xpath': self._get_xpath(form),
            }

            forms.append(form_data)

        return forms

    # ==================== INPUTS - DEEP ====================

    def _extract_inputs_deep(self, html: str, page: Page) -> List[Dict[str, Any]]:
        """Extract comprehensive input field data."""
        soup = BeautifulSoup(html, 'lxml')
        inputs = []

        for elem in soup.find_all(['input', 'textarea']):
            input_data = {
                'tag': elem.name,
                'type': elem.get('type', 'text' if elem.name == 'input' else 'textarea'),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'class': ' '.join(elem.get('class', [])),

                # Labels & descriptions
                'placeholder': elem.get('placeholder', ''),
                'aria_label': elem.get('aria-label', ''),
                'aria_labelledby': elem.get('aria-labelledby', ''),
                'aria_describedby': elem.get('aria-describedby', ''),
                'title': elem.get('title', ''),
                'label': self._find_label_text(elem, soup),

                # Values & defaults
                'value': elem.get('value', ''),
                'default_value': elem.get('value', ''),
                'checked': elem.get('checked') is not None,
                'default_checked': elem.get('checked') is not None,

                # Constraints & validation
                'required': elem.get('required') is not None,
                'readonly': elem.get('readonly') is not None,
                'disabled': elem.get('disabled') is not None,
                'min': elem.get('min', ''),
                'max': elem.get('max', ''),
                'minlength': elem.get('minlength', ''),
                'maxlength': elem.get('maxlength', ''),
                'pattern': elem.get('pattern', ''),
                'step': elem.get('step', ''),
                'accept': elem.get('accept', ''),  # for file inputs
                'multiple': elem.get('multiple') is not None,

                # Autocomplete & input hints
                'autocomplete': elem.get('autocomplete', ''),
                'autocapitalize': elem.get('autocapitalize', ''),
                'autocorrect': elem.get('autocorrect', ''),
                'spellcheck': elem.get('spellcheck', ''),
                'inputmode': elem.get('inputmode', ''),

                # ARIA attributes
                'aria_invalid': elem.get('aria-invalid', ''),
                'aria_required': elem.get('aria-required', ''),
                'aria_readonly': elem.get('aria-readonly', ''),
                'aria_disabled': elem.get('aria-disabled', ''),
                'role': elem.get('role', ''),

                # Data attributes
                'data_attributes': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},

                # Form association
                'form': elem.get('form', ''),

                # Sizing
                'size': elem.get('size', ''),
                'rows': elem.get('rows', '') if elem.name == 'textarea' else '',
                'cols': elem.get('cols', '') if elem.name == 'textarea' else '',

                # Context
                'context': self._get_context_text(elem),
                'parent_form': self._get_parent_form_id(elem),
                'xpath': self._get_xpath(elem),

                # Purpose detection (enhanced)
                'purpose': self._detect_input_purpose_deep(elem, soup),
            }

            inputs.append(input_data)

        return inputs

    def _detect_input_purpose_deep(self, elem, soup: BeautifulSoup) -> str:
        """Enhanced input purpose detection."""
        # Check autocomplete (most reliable)
        autocomplete = elem.get('autocomplete', '').lower()
        if autocomplete and autocomplete != 'off':
            return autocomplete

        # Check type
        input_type = elem.get('type', '').lower()
        if input_type in ['email', 'password', 'tel', 'url', 'date', 'time', 'number']:
            return input_type

        # Gather all text clues
        name = elem.get('name', '').lower()
        id_attr = elem.get('id', '').lower()
        placeholder = elem.get('placeholder', '').lower()
        aria_label = elem.get('aria-label', '').lower()
        title = elem.get('title', '').lower()
        label = self._find_label_text(elem, soup).lower()

        # Check data attributes for hints
        data_attrs = ' '.join([f"{k}={v}" for k, v in elem.attrs.items() if k.startswith('data-')]).lower()

        combined = f"{name} {id_attr} {placeholder} {aria_label} {title} {label} {data_attrs}"

        # Enhanced pattern matching
        patterns = {
            'email': ['email', 'e-mail', 'mail'],
            'password': ['password', 'passwd', 'pwd', 'pass'],
            'username': ['username', 'user', 'login'],
            'given-name': ['first name', 'firstname', 'fname', 'given name', 'forename'],
            'family-name': ['last name', 'lastname', 'lname', 'surname', 'family name'],
            'name': ['full name', 'name'],
            'tel': ['phone', 'telephone', 'mobile', 'cell'],
            'address-line1': ['address line 1', 'address1', 'street'],
            'address-line2': ['address line 2', 'address2', 'apt', 'suite'],
            'address-level2': ['city', 'town'],
            'address-level1': ['state', 'province', 'region'],
            'postal-code': ['zip', 'postal', 'postcode'],
            'country': ['country'],
            'organization': ['company', 'organization', 'employer'],
            'organization-title': ['job title', 'title', 'position'],
            'url': ['website', 'url', 'homepage'],
            'linkedin': ['linkedin'],
            'github': ['github'],
            'portfolio': ['portfolio'],
            'resume': ['resume', 'cv', 'curriculum vitae'],
            'cover-letter': ['cover letter', 'covering letter'],
            'salary': ['salary', 'compensation', 'expected salary'],
            'start-date': ['start date', 'available', 'availability'],
            'referral': ['referral', 'how did you hear'],
        }

        for purpose, keywords in patterns.items():
            if any(keyword in combined for keyword in keywords):
                return purpose

        return 'unknown'

    # ==================== BUTTONS - DEEP ====================

    def _extract_buttons_deep(self, html: str, page: Page) -> List[Dict[str, Any]]:
        """Extract comprehensive button data."""
        soup = BeautifulSoup(html, 'lxml')
        buttons = []

        # Find all button-like elements
        selectors = [
            ('button', {}),
            ('input', {'type': 'submit'}),
            ('input', {'type': 'button'}),
            ('a', {'role': 'button'}),
            ('div', {'role': 'button'}),
            ('span', {'role': 'button'}),
        ]

        for tag, attrs in selectors:
            for elem in soup.find_all(tag, attrs):
                button_data = {
                    'tag': elem.name,
                    'type': elem.get('type', 'button'),
                    'text': elem.get_text(strip=True),
                    'value': elem.get('value', ''),
                    'name': elem.get('name', ''),
                    'id': elem.get('id', ''),
                    'class': ' '.join(elem.get('class', [])),

                    # ARIA & accessibility
                    'aria_label': elem.get('aria-label', ''),
                    'aria_labelledby': elem.get('aria-labelledby', ''),
                    'aria_describedby': elem.get('aria-describedby', ''),
                    'aria_pressed': elem.get('aria-pressed', ''),
                    'aria_expanded': elem.get('aria-expanded', ''),
                    'role': elem.get('role', ''),
                    'title': elem.get('title', ''),

                    # State
                    'disabled': elem.get('disabled') is not None,
                    'aria_disabled': elem.get('aria-disabled', ''),
                    'hidden': elem.get('hidden') is not None,
                    'aria_hidden': elem.get('aria-hidden', ''),

                    # Data attributes
                    'data_attributes': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},

                    # Link specific
                    'href': elem.get('href', '') if elem.name == 'a' else '',
                    'target': elem.get('target', '') if elem.name == 'a' else '',

                    # Form association
                    'form': elem.get('form', ''),
                    'formaction': elem.get('formaction', ''),
                    'formmethod': elem.get('formmethod', ''),

                    # Context
                    'parent_form': self._get_parent_form_id(elem),
                    'xpath': self._get_xpath(elem),

                    # Purpose detection
                    'purpose': self._detect_button_purpose(elem),
                }

                buttons.append(button_data)

        return buttons

    def _detect_button_purpose(self, elem) -> str:
        """Detect button purpose."""
        text = elem.get_text(strip=True).lower()
        aria = elem.get('aria-label', '').lower()
        title = elem.get('title', '').lower()
        data_attrs = ' '.join([str(v) for k, v in elem.attrs.items() if k.startswith('data-')]).lower()

        combined = f"{text} {aria} {title} {data_attrs}"

        patterns = {
            'submit': ['submit', 'send application', 'apply now', 'confirm'],
            'apply': ['apply', 'apply now', 'submit application'],
            'next': ['next', 'continue', 'proceed', 'forward'],
            'back': ['back', 'previous'],
            'save': ['save', 'save draft', 'save progress'],
            'cancel': ['cancel', 'close', 'dismiss'],
            'signin': ['sign in', 'log in', 'login'],
            'signup': ['sign up', 'register', 'create account', 'join'],
            'upload': ['upload', 'choose file', 'browse'],
            'download': ['download'],
            'edit': ['edit', 'modify', 'change'],
            'delete': ['delete', 'remove'],
            'add': ['add', 'new', 'create'],
        }

        for purpose, keywords in patterns.items():
            if any(keyword in combined for keyword in keywords):
                return purpose

        return 'unknown'

    # ==================== LINKS - DEEP ====================

    def _extract_links_deep(self, html: str, page: Page) -> List[Dict[str, Any]]:
        """Extract comprehensive link data."""
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for elem in soup.find_all('a'):
            link_data = {
                'href': elem.get('href', ''),
                'text': elem.get_text(strip=True),
                'title': elem.get('title', ''),
                'target': elem.get('target', ''),
                'rel': elem.get('rel', []),
                'download': elem.get('download', ''),
                'hreflang': elem.get('hreflang', ''),
                'type': elem.get('type', ''),
                'aria_label': elem.get('aria-label', ''),
                'class': ' '.join(elem.get('class', [])),
                'id': elem.get('id', ''),
                'data_attributes': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                'xpath': self._get_xpath(elem),
            }

            links.append(link_data)

        return links

    # ==================== SELECTS - DEEP ====================

    def _extract_selects_deep(self, html: str, page: Page) -> List[Dict[str, Any]]:
        """Extract comprehensive select/dropdown data."""
        soup = BeautifulSoup(html, 'lxml')
        selects = []

        for elem in soup.find_all('select'):
            # Extract all options
            options = []
            for option in elem.find_all('option'):
                options.append({
                    'value': option.get('value', ''),
                    'text': option.get_text(strip=True),
                    'selected': option.get('selected') is not None,
                    'disabled': option.get('disabled') is not None,
                })

            select_data = {
                'tag': 'select',
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'class': ' '.join(elem.get('class', [])),
                'multiple': elem.get('multiple') is not None,
                'required': elem.get('required') is not None,
                'disabled': elem.get('disabled') is not None,
                'size': elem.get('size', ''),
                'autocomplete': elem.get('autocomplete', ''),
                'aria_label': elem.get('aria-label', ''),
                'label': self._find_label_text(elem, soup),
                'options': options,
                'option_count': len(options),
                'data_attributes': {k: v for k, v in elem.attrs.items() if k.startswith('data-')},
                'form': elem.get('form', ''),
                'parent_form': self._get_parent_form_id(elem),
                'xpath': self._get_xpath(elem),
                'purpose': self._detect_select_purpose(elem, soup),
            }

            selects.append(select_data)

        return selects

    def _detect_select_purpose(self, elem, soup: BeautifulSoup) -> str:
        """Detect select dropdown purpose."""
        name = elem.get('name', '').lower()
        id_attr = elem.get('id', '').lower()
        label = self._find_label_text(elem, soup).lower()
        aria_label = elem.get('aria-label', '').lower()

        combined = f"{name} {id_attr} {label} {aria_label}"

        patterns = {
            'country': ['country'],
            'state': ['state', 'province'],
            'city': ['city'],
            'gender': ['gender', 'sex'],
            'title': ['title', 'salutation', 'mr', 'mrs'],
            'education': ['education', 'degree'],
            'experience': ['experience', 'years'],
            'job-type': ['job type', 'employment type'],
            'work-authorization': ['work authorization', 'visa', 'authorized to work'],
            'ethnicity': ['ethnicity', 'race'],
            'veteran': ['veteran'],
            'disability': ['disability'],
        }

        for purpose, keywords in patterns.items():
            if any(keyword in combined for keyword in keywords):
                return purpose

        return 'unknown'

    # ==================== HIDDEN DATA ====================

    def _extract_data_attributes(self, html: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all data-* attributes from page."""
        soup = BeautifulSoup(html, 'lxml')
        data_attrs = []

        # Find all elements with data-* attributes
        for elem in soup.find_all():
            if not hasattr(elem, 'attrs'):
                continue

            # Extract data-* attributes
            data = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}

            if data:
                elem_data = {
                    'tag': elem.name,
                    'id': elem.get('id', ''),
                    'class': ' '.join(elem.get('class', [])),
                    'data': data
                }
                data_attrs.append(elem_data)

        return {'elements_with_data': data_attrs, 'count': len(data_attrs)}

    def _extract_hidden_fields(self, html: str) -> List[Dict[str, Any]]:
        """Extract all hidden input fields."""
        soup = BeautifulSoup(html, 'lxml')
        hidden = []

        for elem in soup.find_all('input', type='hidden'):
            hidden.append({
                'name': elem.get('name', ''),
                'value': elem.get('value', ''),
                'id': elem.get('id', ''),
                'form': self._get_parent_form_id(elem),
            })

        return hidden

    def _extract_meta_tags(self, html: str) -> List[Dict[str, Any]]:
        """Extract all meta tags."""
        soup = BeautifulSoup(html, 'lxml')
        metas = []

        for meta in soup.find_all('meta'):
            metas.append({
                'name': meta.get('name', ''),
                'property': meta.get('property', ''),
                'content': meta.get('content', ''),
                'charset': meta.get('charset', ''),
                'http_equiv': meta.get('http-equiv', ''),
            })

        return metas

    # ==================== JAVASCRIPT CONTEXT ====================

    def _extract_window_data(self, page: Page) -> Dict[str, Any]:
        """Extract data from window object."""
        try:
            result = page.evaluate("""
                () => {
                    const data = {};

                    // Window properties
                    data.location = {
                        href: window.location.href,
                        protocol: window.location.protocol,
                        host: window.location.host,
                        pathname: window.location.pathname,
                        search: window.location.search,
                        hash: window.location.hash,
                    };

                    data.screen = {
                        width: window.screen.width,
                        height: window.screen.height,
                        availWidth: window.screen.availWidth,
                        availHeight: window.screen.availHeight,
                        colorDepth: window.screen.colorDepth,
                    };

                    data.innerWidth = window.innerWidth;
                    data.innerHeight = window.innerHeight;
                    data.scrollX = window.scrollX;
                    data.scrollY = window.scrollY;

                    return data;
                }
            """)
            return result if result is not None else {}
        except Exception as e:
            self.logger.debug(f"Could not extract window data: {e}")
            return {}

    def _extract_local_storage(self, page: Page) -> Dict[str, Any]:
        """Extract localStorage data."""
        try:
            result = page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            return result if result is not None else {}
        except Exception as e:
            self.logger.debug(f"Could not extract localStorage: {e}")
            return {}

    def _extract_session_storage(self, page: Page) -> Dict[str, Any]:
        """Extract sessionStorage data."""
        try:
            result = page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            return result if result is not None else {}
        except Exception as e:
            self.logger.debug(f"Could not extract sessionStorage: {e}")
            return {}

    def _extract_cookies(self, page: Page) -> List[Dict[str, Any]]:
        """Extract cookies."""
        try:
            return page.context.cookies()
        except Exception as e:
            self.logger.debug(f"Could not extract cookies: {e}")
            return []

    def _extract_global_variables(self, page: Page) -> Dict[str, Any]:
        """Extract interesting global variables from window."""
        try:
            result = page.evaluate("""
                () => {
                    const globals = {};

                    // Common global variable names
                    const checkVars = [
                        'appConfig', 'config', 'CONFIG',
                        'jobData', 'applicationData', 'formData',
                        'user', 'userData', 'currentUser',
                        'api', 'API', 'apiUrl', 'apiEndpoint',
                        '__INITIAL_STATE__', '__NEXT_DATA__', '__NUXT__',
                        'grecaptcha', 'hcaptcha',
                    ];

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
            """)
            return result if result is not None else {}
        except Exception as e:
            self.logger.debug(f"Could not extract global variables: {e}")
            return {}

    # ==================== FRAMEWORK STATE ====================

    def _extract_react_state(self, page: Page) -> Dict[str, Any]:
        """Extract React component state if available."""
        try:
            result = page.evaluate("""
                () => {
                    // Look for React fiber
                    const rootElement = document.getElementById('root') || document.querySelector('[data-reactroot]');
                    if (!rootElement) return {detected: false};

                    const fiberKey = Object.keys(rootElement).find(key => key.startsWith('__reactFiber'));
                    if (!fiberKey) return {detected: false};

                    return {
                        detected: true,
                        version: window.React && window.React.version ? window.React.version : 'unknown'
                    };
                }
            """)
            return result if result is not None else {'detected': False}
        except Exception as e:
            self.logger.debug(f"Could not extract React state: {e}")
            return {'detected': False}

    def _extract_vue_state(self, page: Page) -> Dict[str, Any]:
        """Extract Vue component state if available."""
        try:
            result = page.evaluate("""
                () => {
                    if (window.__VUE__) {
                        return {
                            detected: true,
                            version: window.Vue && window.Vue.version ? window.Vue.version : 'unknown'
                        };
                    }
                    return {detected: false};
                }
            """)
            return result if result is not None else {'detected': False}
        except Exception as e:
            self.logger.debug(f"Could not extract Vue state: {e}")
            return {'detected': False}

    def _extract_angular_state(self, page: Page) -> Dict[str, Any]:
        """Extract Angular state if available."""
        try:
            result = page.evaluate("""
                () => {
                    const ngElement = document.querySelector('[ng-version]');
                    if (ngElement) {
                        return {
                            detected: true,
                            version: ngElement.getAttribute('ng-version') || 'unknown'
                        };
                    }
                    return {detected: false};
                }
            """)
            return result if result is not None else {'detected': False}
        except Exception as e:
            self.logger.debug(f"Could not extract Angular state: {e}")
            return {'detected': False}

    def _extract_computed_styles(self, page: Page) -> Dict[str, Any]:
        """Extract computed styles for interactive elements."""
        try:
            return page.evaluate("""
                () => {
                    const hiddenElements = [];
                    const visibleElements = [];

                    // Check all inputs and buttons
                    const elements = document.querySelectorAll('input, button, select, textarea, a[role="button"]');

                    elements.forEach(elem => {
                        const style = window.getComputedStyle(elem);
                        const info = {
                            tag: elem.tagName.toLowerCase(),
                            id: elem.id,
                            display: style.display,
                            visibility: style.visibility,
                            opacity: style.opacity,
                        };

                        if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) {
                            hiddenElements.push(info);
                        } else {
                            visibleElements.push(info);
                        }
                    });

                    return {
                        hidden_count: hiddenElements.length,
                        visible_count: visibleElements.length,
                        hidden_elements: hiddenElements.slice(0, 20),  // Limit output
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract computed styles: {e}")
            return {}

    # ==================== ADVANCED FEATURES ====================

    def _extract_iframes(self, page: Page) -> List[Dict[str, Any]]:
        """Extract iframe information."""
        try:
            return page.evaluate("""
                () => {
                    const iframes = [];
                    document.querySelectorAll('iframe').forEach(iframe => {
                        iframes.push({
                            src: iframe.src,
                            name: iframe.name,
                            id: iframe.id,
                            width: iframe.width,
                            height: iframe.height,
                            sandbox: iframe.sandbox.value,
                        });
                    });
                    return iframes;
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract iframes: {e}")
            return []

    def _extract_shadow_dom(self, page: Page) -> Dict[str, Any]:
        """Extract shadow DOM information."""
        try:
            return page.evaluate("""
                () => {
                    const shadowHosts = [];
                    document.querySelectorAll('*').forEach(elem => {
                        if (elem.shadowRoot) {
                            shadowHosts.push({
                                tag: elem.tagName.toLowerCase(),
                                id: elem.id,
                                class: elem.className,
                                mode: elem.shadowRoot.mode,
                            });
                        }
                    });
                    return {
                        count: shadowHosts.length,
                        hosts: shadowHosts
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract shadow DOM: {e}")
            return {'count': 0, 'hosts': []}

    def _extract_web_components(self, html: str) -> List[str]:
        """Extract custom web components."""
        soup = BeautifulSoup(html, 'lxml')
        custom_elements = set()

        for elem in soup.find_all():
            if '-' in elem.name:  # Custom elements must contain hyphen
                custom_elements.add(elem.name)

        return list(custom_elements)

    def _extract_canvas_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract canvas elements info."""
        try:
            return page.evaluate("""
                () => {
                    const canvases = [];
                    document.querySelectorAll('canvas').forEach(canvas => {
                        canvases.push({
                            id: canvas.id,
                            width: canvas.width,
                            height: canvas.height,
                            class: canvas.className,
                        });
                    });
                    return canvases;
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract canvas: {e}")
            return []

    def _extract_svg_data(self, html: str) -> Dict[str, Any]:
        """Extract SVG elements info."""
        soup = BeautifulSoup(html, 'lxml')
        svgs = soup.find_all('svg')

        return {
            'count': len(svgs),
            'svgs': [{
                'id': svg.get('id', ''),
                'class': ' '.join(svg.get('class', [])),
                'viewBox': svg.get('viewBox', ''),
                'width': svg.get('width', ''),
                'height': svg.get('height', ''),
            } for svg in svgs[:10]]  # Limit to first 10
        }

    # ==================== ACCESSIBILITY ====================

    def _extract_aria_tree(self, html: str) -> Dict[str, Any]:
        """Extract ARIA structure."""
        soup = BeautifulSoup(html, 'lxml')
        aria_elements = []

        aria_attrs = ['role', 'aria-label', 'aria-labelledby', 'aria-describedby',
                      'aria-expanded', 'aria-hidden', 'aria-live', 'aria-required']

        for attr in aria_attrs:
            elements = soup.find_all(attrs={attr: True})
            for elem in elements:
                aria_elements.append({
                    'tag': elem.name,
                    'attribute': attr,
                    'value': elem.get(attr),
                    'id': elem.get('id', ''),
                })

        return {
            'count': len(aria_elements),
            'elements': aria_elements[:50]  # Limit output
        }

    def _extract_accessibility_tree(self, page: Page) -> Dict[str, Any]:
        """Extract accessibility tree snapshot."""
        try:
            snapshot = page.accessibility.snapshot()
            return {
                'available': snapshot is not None,
                'snapshot': snapshot
            }
        except Exception as e:
            self.logger.debug(f"Could not extract accessibility tree: {e}")
            return {'available': False}

    def _extract_focus_data(self, page: Page) -> Dict[str, Any]:
        """Extract focus management data."""
        try:
            return page.evaluate("""
                () => {
                    const activeElement = document.activeElement;
                    return {
                        tag: activeElement ? activeElement.tagName.toLowerCase() : null,
                        id: activeElement ? activeElement.id : null,
                        class: activeElement ? activeElement.className : null,
                        tabindex: activeElement ? activeElement.tabIndex : null,
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract focus data: {e}")
            return {}

    # ==================== VALIDATION ====================

    def _extract_validation_rules(self, html: str) -> List[Dict[str, Any]]:
        """Extract form validation rules."""
        soup = BeautifulSoup(html, 'lxml')
        validations = []

        for form in soup.find_all('form'):
            form_id = form.get('id', '')
            novalidate = form.get('novalidate') is not None

            validations.append({
                'form_id': form_id,
                'novalidate': novalidate,
                'html5_validation': not novalidate,
            })

        return validations

    def _extract_input_constraints(self, html: str) -> List[Dict[str, Any]]:
        """Extract input constraints."""
        soup = BeautifulSoup(html, 'lxml')
        constraints = []

        for elem in soup.find_all(['input', 'textarea', 'select']):
            constraint = {
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'required': elem.get('required') is not None,
                'pattern': elem.get('pattern', ''),
                'min': elem.get('min', ''),
                'max': elem.get('max', ''),
                'minlength': elem.get('minlength', ''),
                'maxlength': elem.get('maxlength', ''),
                'step': elem.get('step', ''),
            }

            # Only include if has any constraints
            if any([constraint['required'], constraint['pattern'],
                   constraint['min'], constraint['max'],
                   constraint['minlength'], constraint['maxlength']]):
                constraints.append(constraint)

        return constraints

    def _extract_required_fields(self, html: str) -> List[Dict[str, Any]]:
        """Extract all required fields."""
        soup = BeautifulSoup(html, 'lxml')
        required = []

        for elem in soup.find_all(['input', 'textarea', 'select'], required=True):
            required.append({
                'tag': elem.name,
                'type': elem.get('type', ''),
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'label': self._find_label_text(elem, soup),
            })

        return required

    # ==================== SCRIPTS & RESOURCES ====================

    def _extract_scripts(self, html: str) -> Dict[str, Any]:
        """Extract script information."""
        soup = BeautifulSoup(html, 'lxml')
        scripts = []

        for script in soup.find_all('script'):
            scripts.append({
                'src': script.get('src', ''),
                'type': script.get('type', ''),
                'async': script.get('async') is not None,
                'defer': script.get('defer') is not None,
                'inline': len(script.get_text(strip=True)) > 0,
                'length': len(script.get_text(strip=True)),
            })

        return {
            'count': len(scripts),
            'external': len([s for s in scripts if s['src']]),
            'inline': len([s for s in scripts if s['inline']]),
            'scripts': scripts
        }

    def _extract_stylesheets(self, html: str) -> List[Dict[str, Any]]:
        """Extract stylesheet links."""
        soup = BeautifulSoup(html, 'lxml')
        styles = []

        for link in soup.find_all('link', rel='stylesheet'):
            styles.append({
                'href': link.get('href', ''),
                'media': link.get('media', ''),
                'type': link.get('type', ''),
            })

        return styles

    def _extract_resources(self, html: str) -> Dict[str, Any]:
        """Extract resource links (images, fonts, etc)."""
        soup = BeautifulSoup(html, 'lxml')

        return {
            'images': len(soup.find_all('img')),
            'videos': len(soup.find_all('video')),
            'audios': len(soup.find_all('audio')),
            'links_preload': len(soup.find_all('link', rel='preload')),
            'links_prefetch': len(soup.find_all('link', rel='prefetch')),
        }

    # ==================== NETWORK & API ====================

    def _extract_api_endpoints(self, html: str, page: Page) -> List[str]:
        """Extract API endpoint references."""
        soup = BeautifulSoup(html, 'lxml')
        endpoints = set()

        # Look in scripts for API URLs
        for script in soup.find_all('script'):
            text = script.get_text()
            # Find URLs that look like API endpoints
            api_patterns = [
                r'["\']([^"\']*(?:/api/|/v\d+/|/graphql|/rest/)[^"\']*)["\']',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.[^(]+\(["\']([^"\']+)["\']',
            ]

            for pattern in api_patterns:
                matches = re.findall(pattern, text)
                endpoints.update(matches)

        return list(endpoints)[:50]  # Limit

    def _extract_graphql_schemas(self, page: Page) -> Dict[str, Any]:
        """Extract GraphQL schema if available."""
        try:
            return page.evaluate("""
                () => {
                    // Look for GraphQL hints
                    const hasGraphQL = document.querySelector('[data-graphql]') ||
                                      window.__APOLLO_STATE__ ||
                                      window.__RELAY_STORE__;

                    return {
                        detected: !!hasGraphQL,
                        apollo: !!window.__APOLLO_STATE__,
                        relay: !!window.__RELAY_STORE__,
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract GraphQL: {e}")
            return {'detected': False}

    def _extract_websocket_data(self, page: Page) -> Dict[str, Any]:
        """Extract WebSocket information."""
        try:
            return page.evaluate("""
                () => {
                    // Check if WebSocket is used
                    return {
                        supported: 'WebSocket' in window,
                        // We can't reliably get active connections
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract WebSocket: {e}")
            return {'supported': False}

    # ==================== JOB APPLICATION SPECIFIC ====================

    def _extract_job_data(self, html: str, page: Page) -> Dict[str, Any]:
        """Extract job-specific data."""
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=' ', strip=True).lower()

        job_data = {
            'detected_job_board': self._detect_job_board(html, page),
            'has_apply_button': any('apply' in btn.get_text().lower() for btn in soup.find_all(['button', 'a'])),
            'has_resume_upload': any('resume' in elem.get('accept', '').lower() or
                                    'resume' in self._find_label_text(elem, soup).lower()
                                    for elem in soup.find_all('input', type='file')),
            'requires_account': 'sign in' in text or 'create account' in text,
        }

        return job_data

    def _detect_job_board(self, html: str, page: Page) -> Optional[str]:
        """Detect which job board/ATS this is."""
        url = page.url.lower()
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
            'glassdoor': ['glassdoor.com'],
        }

        for platform, indicators in platforms.items():
            if any(indicator in url or indicator in html_lower for indicator in indicators):
                return platform

        return 'unknown'

    def _extract_application_schema(self, page: Page) -> Dict[str, Any]:
        """Extract application form schema from JSON-LD or structured data."""
        try:
            return page.evaluate("""
                () => {
                    const schemas = [];
                    document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
                        try {
                            schemas.push(JSON.parse(script.textContent));
                        } catch (e) {}
                    });
                    return {
                        count: schemas.length,
                        schemas: schemas
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract schemas: {e}")
            return {'count': 0, 'schemas': []}

    def _extract_file_upload_info(self, html: str) -> List[Dict[str, Any]]:
        """Extract file upload field information."""
        soup = BeautifulSoup(html, 'lxml')
        uploads = []

        for elem in soup.find_all('input', type='file'):
            uploads.append({
                'name': elem.get('name', ''),
                'id': elem.get('id', ''),
                'accept': elem.get('accept', ''),
                'multiple': elem.get('multiple') is not None,
                'required': elem.get('required') is not None,
                'label': self._find_label_text(elem, soup),
                'purpose': self._detect_file_purpose(elem, soup),
            })

        return uploads

    def _detect_file_purpose(self, elem, soup: BeautifulSoup) -> str:
        """Detect file upload purpose."""
        label = self._find_label_text(elem, soup).lower()
        name = elem.get('name', '').lower()
        id_attr = elem.get('id', '').lower()
        accept = elem.get('accept', '').lower()

        combined = f"{label} {name} {id_attr} {accept}"

        if 'resume' in combined or 'cv' in combined:
            return 'resume'
        if 'cover' in combined:
            return 'cover-letter'
        if 'transcript' in combined:
            return 'transcript'
        if 'portfolio' in combined:
            return 'portfolio'

        return 'document'

    # ==================== PAGE STATE ====================

    def _extract_page_state(self, html: str, page: Page) -> Dict[str, Any]:
        """Extract current page state."""
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=' ', strip=True).lower()

        state_indicators = {
            'is_login_page': any(phrase in text for phrase in ['sign in', 'log in', 'login']),
            'is_signup_page': any(phrase in text for phrase in ['create account', 'sign up', 'register']),
            'is_form_page': len(soup.find_all('form')) > 0,
            'is_confirmation_page': any(phrase in text for phrase in ['thank you', 'submitted', 'received']),
            'is_error_page': any(phrase in text for phrase in ['error', '404', '500', 'not found']),
            'has_captcha': any(phrase in text for phrase in ['recaptcha', 'captcha', 'verify you are human']),
        }

        return state_indicators

    def _extract_event_listeners(self, page: Page) -> Dict[str, Any]:
        """Extract information about event listeners."""
        try:
            return page.evaluate("""
                () => {
                    // We can't easily enumerate all listeners, but we can check common patterns
                    const hasListeners = {
                        onclick_handlers: document.querySelectorAll('[onclick]').length,
                        onsubmit_handlers: document.querySelectorAll('form[onsubmit]').length,
                    };
                    return hasListeners;
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract event listeners: {e}")
            return {}

    def _extract_timers(self, page: Page) -> Dict[str, Any]:
        """Extract active timers/intervals (limited info)."""
        # Note: Can't directly access all timers, but can check for indicators
        return {'note': 'Timer extraction limited by browser security'}

    # ==================== SECURITY ====================

    def _extract_csrf_tokens(self, html: str) -> List[Dict[str, Any]]:
        """Extract CSRF tokens."""
        soup = BeautifulSoup(html, 'lxml')
        tokens = []

        # Common CSRF token patterns
        csrf_patterns = ['csrf', 'xsrf', '_token', 'authenticity_token', '__requestverificationtoken']

        for pattern in csrf_patterns:
            for elem in soup.find_all('input', attrs={'name': re.compile(pattern, re.I)}):
                tokens.append({
                    'name': elem.get('name', ''),
                    'value': elem.get('value', '')[:50],  # Truncate for safety
                    'form': self._get_parent_form_id(elem),
                })

        return tokens

    def _extract_auth_tokens(self, page: Page) -> Dict[str, Any]:
        """Extract authentication tokens from storage."""
        try:
            return page.evaluate("""
                () => {
                    const tokens = {};

                    // Check localStorage for common token keys
                    const tokenKeys = ['token', 'auth_token', 'access_token', 'jwt', 'bearer'];

                    for (const key of tokenKeys) {
                        const value = localStorage.getItem(key);
                        if (value) {
                            tokens[key] = value.substring(0, 20) + '...';  // Truncate
                        }
                    }

                    return {
                        found: Object.keys(tokens).length > 0,
                        keys: Object.keys(tokens)
                    };
                }
            """)
        except Exception as e:
            self.logger.debug(f"Could not extract auth tokens: {e}")
            return {'found': False}

    def _extract_security_headers(self, page: Page) -> Dict[str, Any]:
        """Extract security-related headers."""
        # Note: Headers are typically extracted from network responses
        return {'note': 'Security headers extracted from network layer'}

    # ==================== CONTENT ANALYSIS ====================

    def _extract_text_analysis(self, html: str) -> Dict[str, Any]:
        """Analyze text content."""
        soup = BeautifulSoup(html, 'lxml')

        # Remove scripts and styles
        for elem in soup(['script', 'style', 'noscript']):
            elem.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text_clean = ' '.join(text.split())

        return {
            'total_length': len(text_clean),
            'word_count': len(text_clean.split()),
            'has_emoji': bool(re.search(r'[\U0001F300-\U0001F9FF]', text_clean)),
            'languages_detected': 'auto-detect-not-implemented',
        }

    def _extract_semantic_structure(self, html: str) -> Dict[str, Any]:
        """Extract semantic HTML5 structure."""
        soup = BeautifulSoup(html, 'lxml')

        semantic_tags = ['header', 'nav', 'main', 'article', 'section',
                        'aside', 'footer', 'figure', 'figcaption']

        structure = {}
        for tag in semantic_tags:
            structure[tag] = len(soup.find_all(tag))

        return structure

    def _extract_language_data(self, html: str) -> Dict[str, Any]:
        """Extract language information."""
        soup = BeautifulSoup(html, 'lxml')

        return {
            'html_lang': soup.html.get('lang', '') if soup.html else '',
            'content_language': soup.find('meta', attrs={'http-equiv': 'content-language'}),
            'dir': soup.html.get('dir', 'ltr') if soup.html else 'ltr',
        }

    # ==================== HELPER METHODS ====================

    def _find_label_text(self, elem, soup: BeautifulSoup) -> str:
        """Find associated label text."""
        # Check for label by 'for' attribute
        elem_id = elem.get('id')
        if elem_id:
            label = soup.find('label', attrs={'for': elem_id})
            if label:
                return label.get_text(strip=True)

        # Check for parent label
        parent = elem.find_parent('label')
        if parent:
            return parent.get_text(strip=True)

        return ''

    def _get_context_text(self, elem) -> str:
        """Get surrounding context text."""
        parent = elem.find_parent(['div', 'fieldset', 'section', 'form'])
        if parent:
            text = parent.get_text(strip=True)
            return text[:300] if len(text) > 300 else text
        return ''

    def _get_parent_form_id(self, elem) -> str:
        """Get parent form ID."""
        parent_form = elem.find_parent('form')
        return parent_form.get('id', '') if parent_form else ''

    def _get_xpath(self, elem) -> str:
        """Generate XPath for element (simplified)."""
        # This is a simplified version - full XPath generation is complex
        components = []
        child = elem

        for _ in range(5):  # Limit depth
            if child.parent is None:
                break

            siblings = [s for s in child.parent.children if s.name == child.name]
            if len(siblings) > 1:
                index = siblings.index(child) + 1
                components.append(f"{child.name}[{index}]")
            else:
                components.append(child.name)

            child = child.parent

        return '/' + '/'.join(reversed(components)) if components else ''

    def _calculate_stats(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate extraction statistics."""
        # Helper to safely get nested values
        def safe_get(data, *keys, default=None):
            """Safely get nested dict values."""
            result = data
            for key in keys:
                if result is None or not isinstance(result, dict):
                    return default
                result = result.get(key)
            return result if result is not None else default

        stats = {
            'total_data_points': 0,
            'forms_count': len(extraction.get('forms') or []),
            'inputs_count': len(extraction.get('inputs') or []),
            'buttons_count': len(extraction.get('buttons') or []),
            'links_count': len(extraction.get('links') or []),
            'selects_count': len(extraction.get('selects') or []),
            'hidden_fields_count': len(extraction.get('hidden_fields') or []),
            'meta_tags_count': len(extraction.get('meta_tags') or []),
            'cookies_count': len(extraction.get('cookies') or []),
            'scripts_count': safe_get(extraction, 'scripts', 'count', default=0),
            'has_react': safe_get(extraction, 'react_state', 'detected', default=False),
            'has_vue': safe_get(extraction, 'vue_state', 'detected', default=False),
            'has_angular': safe_get(extraction, 'angular_state', 'detected', default=False),
            'job_board': safe_get(extraction, 'job_data', 'detected_job_board', default='unknown'),
        }

        # Calculate total data points
        for key, value in stats.items():
            if isinstance(value, int):
                stats['total_data_points'] += value

        return stats
