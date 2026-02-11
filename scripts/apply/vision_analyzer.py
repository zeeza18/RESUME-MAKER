"""Gemini API for screenshot/layout analysis."""

import os
import base64
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class VisionAnalyzer:
    """Uses Gemini Vision to analyze screenshots and identify form elements."""

    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.enabled = False
        self.model = None

        if not api_key:
            print("[VisionAnalyzer] No GEMINI_API_KEY or GOOGLE_API_KEY found – running in fallback mode")
            return

        if genai is None:
            print("[VisionAnalyzer] google-generativeai not installed – running in fallback mode")
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.enabled = True
        print("[VisionAnalyzer] Gemini Vision initialized successfully")

    def _load_image(self, image_path: str) -> Dict[str, Any]:
        """Load image and prepare for Gemini API."""
        with open(image_path, 'rb') as f:
            image_data = f.read()

        return {
            'mime_type': 'image/png',
            'data': base64.b64encode(image_data).decode('utf-8')
        }

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a JSON response, stripping markdown fences if present."""
        text = text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
            text = text.rsplit('```', 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def analyze_screenshot(self, screenshot_path: str, page_content: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a screenshot to identify form fields, buttons, page layout.
        Falls back to DOM-based page_content when Gemini is unavailable.
        """
        if not self.enabled:
            # Fallback: build analysis from DOM content
            if page_content:
                fields = []
                purposes = {}
                for form in page_content.get('forms', []):
                    for f in form.get('fields', []):
                        fields.append({
                            "field_type": f.get('type', 'text'),
                            "label": f.get('label', ''),
                            "placeholder": f.get('placeholder', ''),
                            "required": f.get('required', False),
                            "css_selector_hint": f"#{f['name']}" if f.get('name') else "",
                        })
                        # Guess purpose from name/label
                        name = (f.get('name') or f.get('label') or '').lower()
                        if 'email' in name:
                            purposes['email'] = f"#{f.get('name', '')}"
                        elif 'password' in name or f.get('type') == 'password':
                            purposes['password'] = f"#{f.get('name', '')}"
                        elif 'first' in name and 'name' in name:
                            purposes['first_name'] = f"#{f.get('name', '')}"
                        elif 'last' in name and 'name' in name:
                            purposes['last_name'] = f"#{f.get('name', '')}"
                        elif 'phone' in name:
                            purposes['phone'] = f"#{f.get('name', '')}"
                        elif 'file' in name or f.get('type') == 'file':
                            purposes['resume_upload'] = f"#{f.get('name', '')}"

                buttons = [
                    {"text": b.get('text', ''), "type": b.get('type', 'button'),
                     "css_selector_hint": f"#{b['id']}" if b.get('id') else ""}
                    for b in page_content.get('buttons', [])
                ]

                # Guess page type
                page_type = "application_form"
                btn_texts = ' '.join(b.get('text', '').lower() for b in page_content.get('buttons', []))
                if 'login' in btn_texts or 'sign in' in btn_texts:
                    page_type = "login"
                elif 'sign up' in btn_texts or 'register' in btn_texts:
                    page_type = "signup"

                return {
                    "page_type": page_type,
                    "form_fields": fields,
                    "buttons": buttons,
                    "detected_fields_purpose": purposes,
                    "errors": [],
                    "recommendations": ["Gemini unavailable – using DOM analysis"],
                }
            return {
                "page_type": "unknown",
                "form_fields": [],
                "buttons": [],
                "detected_fields_purpose": {},
                "errors": ["Gemini unavailable and no DOM content"],
                "recommendations": [],
            }

        image = self._load_image(screenshot_path)

        prompt = """Analyze this job application page screenshot and provide a detailed JSON response with:

1. "page_type": Type of page (login, signup, application_form, profile, confirmation, error, other)
2. "current_step": If multi-step form, what step is this (1, 2, 3, etc.)
3. "form_fields": Array of visible form fields with:
   - "field_type": (text, email, password, textarea, select, checkbox, radio, file_upload)
   - "label": The field label text
   - "placeholder": Placeholder text if visible
   - "required": true/false if indicated
   - "css_selector_hint": Suggested CSS selector pattern
   - "position": (top, middle, bottom of form)
4. "buttons": Array of buttons with:
   - "text": Button text
   - "type": (submit, next, login, signup, upload, cancel)
   - "css_selector_hint": Suggested CSS selector
   - "is_primary": true/false
5. "detected_fields_purpose": Map of detected field purposes:
   - email, password, first_name, last_name, phone, resume_upload, cover_letter, linkedin, etc.
6. "navigation": Any detected navigation elements (back, next, pagination)
7. "errors": Any visible error messages
8. "recommendations": Array of recommended actions to take

Return ONLY valid JSON, no markdown code blocks."""

        response = self.model.generate_content([prompt, image])
        result = self._parse_json_response(response.text)
        if result:
            return result
        return {
            "page_type": "unknown",
            "raw_analysis": response.text,
            "form_fields": [],
            "buttons": [],
            "detected_fields_purpose": {},
            "errors": ["Could not parse structured response"],
            "recommendations": ["Manual review recommended"]
        }

    def detect_next_action(self, screenshot_path: str, current_state: str = "", page_content: Dict[str, Any] = None) -> Dict[str, Any]:
        """Determine the next action to take based on current page state."""
        if not self.enabled:
            # Fallback: guess from DOM
            if page_content:
                forms = page_content.get('forms', [])
                buttons = page_content.get('buttons', [])
                btn_texts = ' '.join(b.get('text', '').lower() for b in buttons)

                if 'login' in btn_texts or 'sign in' in btn_texts:
                    return {"action_type": "login", "confidence": 50,
                            "reasoning": "Login detected via DOM (Gemini unavailable)"}
                if forms:
                    return {"action_type": "fill_form", "confidence": 50,
                            "reasoning": "Form detected via DOM (Gemini unavailable)"}
                if 'apply' in btn_texts or 'submit' in btn_texts or 'next' in btn_texts:
                    return {"action_type": "click_button", "confidence": 40,
                            "target_element": "submit/next button",
                            "reasoning": "Button detected via DOM (Gemini unavailable)"}
            return {"action_type": "fill_form", "confidence": 30,
                    "reasoning": "Default to fill_form (Gemini unavailable)"}

        image = self._load_image(screenshot_path)

        prompt = f"""Based on this job application page screenshot, determine the next action to take.

Current state context: {current_state if current_state else 'Starting application'}

Analyze and return JSON with:
1. "action_type": One of (fill_form, click_button, upload_file, wait, login, complete, error)
2. "target_element": Description of element to interact with
3. "css_selector_suggestion": Best CSS selector to target
4. "value_to_fill": If filling a field, what value type (email, name, phone, etc.)
5. "confidence": 0-100 confidence score
6. "reasoning": Brief explanation of why this action

Return ONLY valid JSON."""

        response = self.model.generate_content([prompt, image])
        result = self._parse_json_response(response.text)
        if result:
            return result
        return {
            "action_type": "error",
            "target_element": None,
            "css_selector_suggestion": None,
            "value_to_fill": None,
            "confidence": 0,
            "reasoning": response.text
        }

    def extract_job_description(self, screenshot_path: str, page_text: str = "") -> Dict[str, Any]:
        """
        Extract the complete job description from a job posting page.
        Falls back to raw page text when Gemini is unavailable.
        """
        if not self.enabled:
            # Fallback: use page text directly
            return {
                "job_description": page_text[:5000] if page_text else "",
                "job_title": "Unknown",
                "company": "Unknown",
                "confidence": 20 if page_text else 0,
            }

        image = self._load_image(screenshot_path)

        prompt = f"""Extract the complete job description from this job posting page.

Page text content (for reference):
{page_text[:5000] if page_text else "(not available)"}

Return a JSON object with:
1. "job_description": The full job description text including responsibilities, requirements, qualifications, and any other relevant details. Be comprehensive - include everything that describes what the role entails and what the candidate needs.
2. "job_title": The job title/position name
3. "company": The company name
4. "confidence": 0-100 confidence score that this is a valid job posting with extractable JD

Return ONLY valid JSON, no markdown code blocks."""

        response = self.model.generate_content([prompt, image])
        result = self._parse_json_response(response.text)
        if result:
            return result
        return {
            "job_description": page_text[:3000] if page_text else "",
            "job_title": "Unknown",
            "company": "Unknown",
            "confidence": 10,
            "raw_response": response.text
        }

    def compare_screenshots(self, before_path: str, after_path: str) -> Dict[str, Any]:
        """Compare two screenshots to determine if action was successful."""
        if not self.enabled:
            # Optimistic fallback: assume action worked
            return {
                "action_successful": True,
                "page_changed": True,
                "new_errors": [],
                "progress_made": True,
                "new_page_type": "unknown",
                "summary": "Gemini unavailable – assuming success"
            }

        before_image = self._load_image(before_path)
        after_image = self._load_image(after_path)

        prompt = """Compare these two job application screenshots (before and after an action).

Determine:
1. "action_successful": true/false
2. "page_changed": true/false
3. "new_errors": Any new error messages visible
4. "progress_made": true/false (did we move forward in the application?)
5. "new_page_type": Type of page we're now on
6. "summary": Brief summary of what changed

Return ONLY valid JSON."""

        response = self.model.generate_content([prompt, before_image, after_image])
        result = self._parse_json_response(response.text)
        if result:
            return result
        return {
            "action_successful": False,
            "page_changed": False,
            "new_errors": [],
            "progress_made": False,
            "new_page_type": "unknown",
            "summary": response.text
        }
