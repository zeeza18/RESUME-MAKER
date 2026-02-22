"""
TRUE UNIVERSAL EXTRACTOR - Pulls EVERY ELEMENT, no exceptions.
No assumptions, no hardcoded lists, just EVERYTHING.
"""

from typing import Dict, Any, List
from playwright.sync_api import Page
from bs4 import BeautifulSoup
import json


class PullEverythingExtractor:
    """
    The ULTIMATE extractor - pulls EVERY element from the page.
    No filtering, no assumptions - if it exists, we extract it.
    """

    def __init__(self, logger):
        self.logger = logger

    def pull_everything(self, page: Page, html: str) -> Dict[str, Any]:
        """
        Pull EVERY element from the page + ALL iframes (Greenhouse, Lever, Workday, etc.)

        Returns:
            {
                'all_elements': [...],  # EVERY element with ALL attributes
                'clickables': [...],    # Anything that might be clickable
                'fillables': [...],     # Anything that can be filled
                'text_content': '...',  # All text
                'iframes': [...],       # ALL iframes found with their content
                'stats': {...}
            }
        """
        self.logger.info("PULLING EVERYTHING FROM PAGE + IFRAMES...")

        soup = BeautifulSoup(html, 'lxml')

        # Get ALL elements from main page
        all_elements = []
        clickables = []
        fillables = []

        for elem in soup.find_all():
            # Extract EVERYTHING about this element
            elem_data = self._extract_element_complete(elem)

            # Add to all elements
            all_elements.append(elem_data)

            # Categorize by capability
            if self._is_clickable(elem_data):
                clickables.append(elem_data)

            if self._is_fillable(elem_data):
                fillables.append(elem_data)

        # Get all text from main page
        text_content = self._get_all_text(soup)

        # CRITICAL: Extract from ALL iframes (Greenhouse, Lever, Workday, etc.)
        iframe_data = self._extract_all_iframes(page)

        # Combine iframe elements with main page
        for iframe in iframe_data:
            clickables.extend(iframe['clickables'])
            fillables.extend(iframe['fillables'])
            text_content += "\n\n--- IFRAME CONTENT ---\n" + iframe['text_content']

        # Get JavaScript state
        js_state = self._pull_javascript_state(page)

        result = {
            'all_elements': all_elements[:500],  # Limit to prevent huge output
            'clickables': clickables,
            'fillables': fillables,
            'text_content': text_content,
            'iframes': iframe_data,  # Info about iframes
            'javascript_state': js_state,
            'stats': {
                'total_elements': len(all_elements),
                'clickable_count': len(clickables),
                'fillable_count': len(fillables),
                'text_length': len(text_content),
                'iframe_count': len(iframe_data),
            }
        }

        self.logger.info(f"PULLED EVERYTHING: {len(all_elements)} elements + {len(iframe_data)} iframes")

        return result

    def _extract_all_iframes(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract content from ALL iframes on the page.
        This handles Greenhouse, Lever, Workday, and ANY iframe-based system.
        """
        iframe_data = []

        try:
            # Get all frames from the page
            frames = page.frames
            self.logger.info(f"Found {len(frames)} frames on page (including main)")

            # Skip main frame (index 0), process iframes only
            for iframe_idx, frame in enumerate(frames[1:], 1):
                try:
                    # Get iframe URL and name
                    iframe_url = frame.url
                    iframe_name = frame.name or f'iframe-{iframe_idx}'

                    # Store the actual frame index in the page.frames list
                    frame_index = iframe_idx  # This is the index we'll use to access the frame

                    self.logger.debug(f"Extracting frame {iframe_idx}: name={iframe_name}, url={iframe_url[:100] if iframe_url else 'about:blank'}")

                    # Skip empty/blank iframes
                    if not iframe_url or iframe_url in ['about:blank', 'about:srcdoc']:
                        self.logger.debug(f"Skipping empty iframe {iframe_idx}")
                        continue

                    # Wait for iframe to load
                    try:
                        frame.wait_for_load_state('domcontentloaded', timeout=5000)
                    except:
                        pass  # Continue anyway

                    # Get HTML from iframe
                    iframe_html = frame.content()

                    # Parse iframe content
                    iframe_soup = BeautifulSoup(iframe_html, 'lxml')

                    # Extract elements from iframe
                    iframe_clickables = []
                    iframe_fillables = []

                    for elem in iframe_soup.find_all():
                        elem_data = self._extract_element_complete(elem)

                        # Mark that this is from an iframe
                        elem_data['iframe_index'] = frame_index
                        elem_data['iframe_name'] = iframe_name
                        elem_data['iframe_url'] = iframe_url

                        if self._is_clickable(elem_data):
                            iframe_clickables.append(elem_data)

                        if self._is_fillable(elem_data):
                            iframe_fillables.append(elem_data)

                    # Get text from iframe
                    iframe_text = self._get_all_text(iframe_soup)

                    iframe_data.append({
                        'iframe_index': frame_index,
                        'iframe_name': iframe_name,
                        'iframe_url': iframe_url,
                        'clickables': iframe_clickables,
                        'fillables': iframe_fillables,
                        'text_content': iframe_text,
                        'stats': {
                            'clickable_count': len(iframe_clickables),
                            'fillable_count': len(iframe_fillables),
                        }
                    })

                    self.logger.info(
                        f"Frame {iframe_idx} ({iframe_name}): {len(iframe_clickables)} clickables, "
                        f"{len(iframe_fillables)} fillables"
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to extract iframe {iframe_idx}: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error during iframe extraction: {e}")

        return iframe_data

    def _extract_element_complete(self, elem) -> Dict[str, Any]:
        """
        Extract EVERYTHING about an element.
        No filtering - get ALL attributes.
        """
        # Get all attributes
        attrs = dict(elem.attrs) if hasattr(elem, 'attrs') else {}

        # Extract classes as list
        classes = elem.get('class', []) if hasattr(elem, 'get') else []
        if isinstance(classes, str):
            classes = [classes]

        elem_data = {
            'tag': elem.name,
            'text': elem.get_text(strip=True) if hasattr(elem, 'get_text') else '',
            'id': elem.get('id', '') if hasattr(elem, 'get') else '',
            'classes': classes,
            'all_attributes': attrs,  # EVERY attribute!
        }

        # Add specific common attributes for easy access
        if hasattr(elem, 'get'):
            elem_data.update({
                'name': elem.get('name', ''),
                'type': elem.get('type', ''),
                'value': elem.get('value', ''),
                'href': elem.get('href', ''),
                'src': elem.get('src', ''),
                'role': elem.get('role', ''),
                'aria_label': elem.get('aria-label', ''),
                'placeholder': elem.get('placeholder', ''),
                'disabled': elem.get('disabled') is not None,
                'required': elem.get('required') is not None,
                'readonly': elem.get('readonly') is not None,
            })

        return elem_data

    def _is_clickable(self, elem_data: Dict[str, Any]) -> bool:
        """
        Determine if element is clickable.
        Smart detection - avoid false positives.
        """
        tag = elem_data['tag']
        attrs = elem_data['all_attributes']
        text = elem_data['text']

        # Skip container elements that are obviously not clickable
        if tag in ['html', 'head', 'body', 'style', 'script', 'meta', 'title']:
            return False

        # Obvious clickables
        if tag in ['button', 'a']:
            return True

        # Input buttons
        if tag == 'input' and elem_data.get('type') in ['submit', 'button']:
            return True

        # Custom web components ending in -button
        if tag.endswith('-button'):
            return True

        # Has role="button"
        if elem_data.get('role') == 'button':
            return True

        # Has onclick or click event handlers
        if any(k.startswith('on') and 'click' in k.lower() for k in attrs.keys()):
            return True

        # Has button-like classes (be specific to avoid false positives)
        classes = elem_data['classes']
        button_class_patterns = ['btn-', 'button-', '-btn', '-button']
        exact_matches = ['btn', 'button', 'clickable']

        for cls in classes:
            cls_lower = cls.lower()
            # Exact match or pattern match
            if cls_lower in exact_matches or any(pattern in cls_lower for pattern in button_class_patterns):
                return True

        # Has button-like data attributes
        for key in attrs.keys():
            if key.startswith('data-') and ('button' in key.lower() or 'click' in key.lower()):
                return True

        # Has short text that suggests it's clickable (avoid long text blocks)
        if text and len(text) < 100:
            clickable_words = ['apply', 'submit', 'continue', 'next', 'sign in', 'login', 'register', 'save']
            if any(word in text.lower() for word in clickable_words):
                return True

        return False

    def _is_fillable(self, elem_data: Dict[str, Any]) -> bool:
        """
        Determine if element can be filled.
        Liberal definition - if it MIGHT accept input, include it.
        """
        tag = elem_data['tag']
        elem_type = elem_data.get('type', '')

        # Obvious fillables
        if tag in ['input', 'textarea', 'select']:
            # Skip buttons and hidden (but include everything else)
            if elem_type not in ['submit', 'button']:
                return True

        # Custom input components
        if tag.endswith('-input') or 'input' in tag:
            return True

        # Has contenteditable
        if elem_data['all_attributes'].get('contenteditable') == 'true':
            return True

        # Has role="textbox"
        if elem_data.get('role') in ['textbox', 'searchbox', 'combobox']:
            return True

        return False

    def _get_all_text(self, soup: BeautifulSoup) -> str:
        """Get ALL text from page."""
        # Remove scripts and styles
        for elem in soup(['script', 'style', 'noscript']):
            elem.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())

        # Limit to 10000 chars
        if len(text) > 10000:
            return text[:10000] + "... [truncated]"

        return text

    def _pull_javascript_state(self, page: Page) -> Dict[str, Any]:
        """Pull JavaScript state from window."""
        try:
            result = page.evaluate("""
                () => {
                    const state = {};

                    // Get ALL global variables (first level)
                    for (const key in window) {
                        try {
                            const value = window[key];
                            const type = typeof value;

                            // Include primitives and simple objects
                            if (type === 'string' || type === 'number' || type === 'boolean') {
                                state[key] = value;
                            } else if (type === 'object' && value !== null && !value.nodeType) {
                                // Try to serialize objects
                                try {
                                    state[key] = JSON.parse(JSON.stringify(value));
                                } catch (e) {
                                    state[key] = `[${type}]`;
                                }
                            }
                        } catch (e) {
                            // Skip inaccessible properties
                        }
                    }

                    // Get storage
                    state.__localStorage = {};
                    state.__sessionStorage = {};

                    try {
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            state.__localStorage[key] = localStorage.getItem(key);
                        }
                    } catch (e) {}

                    try {
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            state.__sessionStorage[key] = sessionStorage.getItem(key);
                        }
                    } catch (e) {}

                    return state;
                }
            """)
            return result if result is not None else {}
        except Exception as e:
            self.logger.debug(f"Could not pull JS state: {e}")
            return {}

    def format_for_ai(self, data: Dict[str, Any]) -> str:
        """
        Format extracted data for AI consumption.
        Returns clean JSON string.
        """
        # Create AI-friendly format
        ai_data = {
            'page_summary': {
                'total_elements': data['stats']['total_elements'],
                'clickable_elements': data['stats']['clickable_count'],
                'fillable_elements': data['stats']['fillable_count'],
            },

            'clickable_elements': [
                {
                    'tag': elem['tag'],
                    'text': elem['text'][:100],  # Limit text length
                    'id': elem['id'],
                    'classes': elem['classes'],
                    'role': elem['role'],
                    'aria_label': elem['aria_label'],
                    'data_attrs': {k: v for k, v in elem['all_attributes'].items() if k.startswith('data-')},
                }
                for elem in data['clickables'][:50]  # Limit to first 50
            ],

            'fillable_elements': [
                {
                    'tag': elem['tag'],
                    'text': elem['text'][:100],
                    'id': elem['id'],
                    'name': elem['name'],
                    'type': elem['type'],
                    'placeholder': elem['placeholder'],
                    'required': elem['required'],
                    'aria_label': elem['aria_label'],
                }
                for elem in data['fillables'][:50]  # Limit to first 50
            ],

            'page_text': data['text_content'],

            'javascript_state': {
                k: v for k, v in data['javascript_state'].items()
                if k.startswith('__') or k in ['appConfig', 'jobData', 'formData', 'config']
            }
        }

        return json.dumps(ai_data, indent=2, ensure_ascii=False)
