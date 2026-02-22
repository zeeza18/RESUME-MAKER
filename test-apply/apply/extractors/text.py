"""
Visible text extraction and analysis.
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Comment


class TextExtractor:
    """Extracts and analyzes visible text content."""

    def __init__(self, logger):
        """
        Initialize text extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract(self, html: str) -> Dict[str, Any]:
        """
        Extract visible text and detect key phrases.

        Args:
            html: HTML content

        Returns:
            Extracted text data
        """
        self.logger.debug("Extracting visible text...")

        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()

        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Get visible text
        visible_text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        visible_text = ' '.join(visible_text.split())

        text_data = {
            'full_text': visible_text,
            'length': len(visible_text),
            'key_phrases': self._detect_key_phrases(visible_text),
            'page_state': self._detect_page_state(visible_text)
        }

        self.logger.debug(
            f"Text extraction: {text_data['length']} chars, "
            f"state={text_data['page_state']}"
        )

        return text_data

    def _detect_key_phrases(self, text: str) -> List[str]:
        """
        Detect key phrases in text.

        Args:
            text: Text content

        Returns:
            List of detected key phrases
        """
        text_lower = text.lower()
        phrases = []

        # Success/confirmation phrases
        if any(phrase in text_lower for phrase in [
            'application submitted',
            'application received',
            'thank you for applying',
            'successfully submitted',
            'we\'ll be in touch',
            'application complete'
        ]):
            phrases.append('application_submitted')

        # Sign in / authentication
        if any(phrase in text_lower for phrase in [
            'sign in',
            'log in',
            'login',
            'enter your password'
        ]):
            phrases.append('signin_required')

        # Sign up / registration
        if any(phrase in text_lower for phrase in [
            'sign up',
            'create account',
            'register',
            'create your account'
        ]):
            phrases.append('signup_required')

        # Application form
        if any(phrase in text_lower for phrase in [
            'job application',
            'apply for',
            'application form',
            'complete your application'
        ]):
            phrases.append('application_form')

        # Review/confirmation step
        if any(phrase in text_lower for phrase in [
            'review your application',
            'review and submit',
            'confirm and submit',
            'please review'
        ]):
            phrases.append('review_step')

        # CAPTCHA/challenge
        if any(phrase in text_lower for phrase in [
            'captcha',
            'recaptcha',
            'verify you are human',
            'security check',
            'cloudflare'
        ]):
            phrases.append('captcha_detected')

        # Error messages
        if any(phrase in text_lower for phrase in [
            'error',
            'invalid',
            'required field',
            'please enter',
            'something went wrong'
        ]):
            phrases.append('error_detected')

        return phrases

    def _detect_page_state(self, text: str) -> str:
        """
        Detect the current page state.

        Args:
            text: Text content

        Returns:
            State identifier
        """
        phrases = self._detect_key_phrases(text)

        # Prioritize detection
        if 'application_submitted' in phrases:
            return 'CONFIRMATION'

        if 'captcha_detected' in phrases:
            return 'CAPTCHA'

        if 'review_step' in phrases:
            return 'REVIEW'

        if 'application_form' in phrases:
            return 'FORM_FILL'

        if 'signin_required' in phrases:
            return 'SIGN_IN'

        if 'signup_required' in phrases:
            return 'SIGN_UP'

        return 'UNKNOWN'

    def contains_phrase(self, text: str, phrase: str) -> bool:
        """
        Check if text contains a specific phrase (case-insensitive).

        Args:
            text: Text to search
            phrase: Phrase to find

        Returns:
            True if phrase found
        """
        return phrase.lower() in text.lower()
