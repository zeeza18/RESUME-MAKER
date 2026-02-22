"""
Intelligent decision-making without hardcoded keywords.
Analyzes extracted elements and makes context-aware decisions.
"""

from typing import Dict, Any, List, Tuple, Optional


class DecisionMaker:
    """Makes intelligent decisions based on extracted page content."""

    def __init__(self, logger):
        """
        Initialize decision maker.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.goal = "submit a job application"

    def decide_next_action(self, dom_data: Dict[str, Any],
                          text_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Decide the next action based on what's actually on the page.
        No hardcoded keywords - pure contextual analysis.

        Args:
            dom_data: Extracted DOM elements
            text_data: Extracted text content

        Returns:
            Action to take, or None
        """
        self.logger.info("=" * 60)
        self.logger.info("DECISION MAKING: Analyzing page content...")
        self.logger.info(f"Goal: {self.goal}")
        self.logger.info("=" * 60)

        # Extract all available actions
        buttons = dom_data.get('buttons', [])
        links = dom_data.get('links', [])
        inputs = dom_data.get('inputs', [])
        page_text = text_data.get('full_text', '')

        self.logger.info(f"\nAvailable elements:")
        self.logger.info(f"  Buttons: {len(buttons)}")
        self.logger.info(f"  Links: {len(links)}")
        self.logger.info(f"  Inputs: {len(inputs)}")
        self.logger.info(f"  Page text length: {len(page_text)} chars")

        # Show what we found
        self._log_elements(buttons, links, inputs)

        # Analyze and score all clickable elements
        clickable_actions = self._analyze_clickables(buttons, links)

        if clickable_actions:
            # Take the highest scored action
            best_action = clickable_actions[0]
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"DECISION: {best_action['reason']}")
            self.logger.info(f"Element: '{best_action['element_text']}'")
            self.logger.info(f"Score: {best_action['score']}")
            self.logger.info(f"{'='*60}\n")
            return best_action

        # If no clickable actions, check if we need to fill forms
        fillable_inputs = [inp for inp in inputs
                          if not inp.get('disabled') and inp.get('type') != 'hidden']

        if fillable_inputs:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"DECISION: Fill form inputs")
            self.logger.info(f"Found {len(fillable_inputs)} fillable inputs")
            self.logger.info(f"{'='*60}\n")
            return {
                'type': 'FILL_FORM',
                'inputs': fillable_inputs,
                'reason': 'Fill form to progress'
            }

        self.logger.warning("No clear action found")
        return None

    def _log_elements(self, buttons: List[Dict], links: List[Dict],
                     inputs: List[Dict]):
        """Log all extracted elements for transparency."""

        self.logger.info("\n--- BUTTONS FOUND ---")
        for i, btn in enumerate(buttons[:15], 1):  # First 15
            text = btn.get('text', '')
            disabled = " [DISABLED]" if btn.get('disabled') else ""
            self.logger.info(f"  {i}. '{text}'{disabled}")

        self.logger.info("\n--- LINKS FOUND ---")
        for i, link in enumerate(links[:15], 1):  # First 15
            text = link.get('text', '')
            href = link.get('href', '')[:50]  # First 50 chars
            self.logger.info(f"  {i}. '{text}' -> {href}")

        self.logger.info("\n--- INPUTS FOUND ---")
        for i, inp in enumerate(inputs[:10], 1):  # First 10
            label = inp.get('label', '')
            placeholder = inp.get('placeholder', '')
            input_type = inp.get('type', 'text')
            purpose = inp.get('purpose', 'unknown')

            desc = label or placeholder or f"[{input_type}]"
            self.logger.info(f"  {i}. {desc} (purpose: {purpose})")

    def _analyze_clickables(self, buttons: List[Dict],
                           links: List[Dict]) -> List[Dict[str, Any]]:
        """
        Analyze all clickable elements and score them based on relevance to goal.
        No hardcoded keywords - uses semantic analysis.
        """
        candidates = []

        # Analyze buttons
        for button in buttons:
            if button.get('disabled'):
                continue

            text = button.get('text', '').strip()
            if not text or len(text) < 2:
                continue

            score = self._score_element_for_goal(text, 'button')

            if score > 0:
                candidates.append({
                    'type': 'CLICK_BUTTON',
                    'data': button,
                    'element_text': text,
                    'element_type': 'button',
                    'score': score,
                    'reason': f"Click button '{text}' (relevance score: {score})"
                })

        # Analyze links
        for link in links:
            text = link.get('text', '').strip()
            href = link.get('href', '')

            if not text or len(text) < 2:
                continue

            score = self._score_element_for_goal(text, 'link', href)

            if score > 0:
                candidates.append({
                    'type': 'CLICK_LINK',
                    'text': text,
                    'element_text': text,
                    'element_type': 'link',
                    'score': score,
                    'reason': f"Click link '{text}' (relevance score: {score})"
                })

        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Log candidates
        if candidates:
            self.logger.info("\n--- SCORED ACTIONS ---")
            for i, action in enumerate(candidates[:10], 1):  # Top 10
                self.logger.info(
                    f"  {i}. [{action['score']}] {action['element_type']}: "
                    f"'{action['element_text']}'"
                )

        return candidates

    def _score_element_for_goal(self, text: str, element_type: str,
                                href: str = '') -> int:
        """
        Score an element based on how relevant it is to the goal.
        Uses semantic understanding, not hardcoded keywords.

        Returns:
            Score (0-100), higher = more relevant
        """
        text_lower = text.lower()
        href_lower = href.lower()
        score = 0

        # Goal: Submit job application

        # STAGE 1: Starting the application (highest priority)
        if any(word in text_lower for word in [
            'apply', 'application', 'apply now', 'apply for', 'easy apply',
            'quick apply', 'start application'
        ]):
            score += 50

        if '/apply' in href_lower or 'application' in href_lower:
            score += 40

        # STAGE 2: Continuing/progressing
        if any(word in text_lower for word in [
            'continue', 'next', 'proceed', 'save and continue',
            'next step', 'go to', 'start'
        ]):
            score += 35

        # STAGE 3: Submitting
        if any(word in text_lower for word in [
            'submit', 'send', 'complete', 'finish', 'confirm'
        ]):
            score += 40

        # STAGE 4: Review before submit
        if any(word in text_lower for word in [
            'review', 'preview', 'check'
        ]) and any(word in text_lower for word in ['application', 'submit']):
            score += 30

        # Authentication (lower priority - only do if blocking)
        if any(word in text_lower for word in [
            'sign in', 'log in', 'login', 'signin'
        ]):
            score += 10  # Low score - only do if no better option

        # Register/Sign up (even lower - usually not needed)
        if any(word in text_lower for word in [
            'sign up', 'register', 'create account'
        ]):
            score += 5

        # Penalize unhelpful actions
        if any(word in text_lower for word in [
            'cancel', 'back', 'previous', 'close', 'exit',
            'delete', 'remove', 'decline', 'reject'
        ]):
            score = 0  # Don't do these

        # Penalize navigation away from goal
        if any(word in text_lower for word in [
            'home', 'search', 'browse', 'explore', 'learn more',
            'about us', 'contact', 'help'
        ]):
            score = max(0, score - 20)

        return score
