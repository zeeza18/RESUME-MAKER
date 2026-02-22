"""
Logging utilities for the application.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


class ApplicationLogger:
    """Custom logger with artifact saving."""

    def __init__(self, run_dir: Path, config):
        """
        Initialize logger.

        Args:
            run_dir: Directory for this run's artifacts
            config: Configuration object
        """
        self.run_dir = run_dir
        self.config = config
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create actions log file
        self.actions_log = run_dir / "actions.log"
        self.network_log = run_dir / "network.jsonl"

        # Setup Python logger
        log_level = getattr(logging, config.get('logging.level', 'INFO'))

        self.logger = logging.getLogger('apply')
        self.logger.setLevel(log_level)

        # Console handler with UTF-8 encoding
        import io
        console_handler = logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        )
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler with UTF-8 encoding
        file_handler = logging.FileHandler(self.actions_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, message: str):
        """Log info message."""
        masked = self.config.mask_sensitive(message)
        self.logger.info(masked)

    def debug(self, message: str):
        """Log debug message."""
        masked = self.config.mask_sensitive(message)
        self.logger.debug(masked)

    def warning(self, message: str):
        """Log warning message."""
        masked = self.config.mask_sensitive(message)
        self.logger.warning(masked)

    def error(self, message: str):
        """Log error message."""
        masked = self.config.mask_sensitive(message)
        self.logger.error(masked)

    def action(self, action_type: str, details: Dict[str, Any]):
        """
        Log an action taken.

        Args:
            action_type: Type of action (CLICK, FILL, NAVIGATE, etc.)
            details: Action details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type,
            'details': details
        }

        message = f"ACTION: {action_type} - {details}"
        self.info(message)

    def save_html(self, html: str, name: str = "page"):
        """
        Save HTML snapshot.

        Args:
            html: HTML content
            name: File name prefix
        """
        if not self.config.get('logging.save_snapshots', True):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.run_dir / f"{name}_{timestamp}.html"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        self.debug(f"Saved HTML snapshot: {filename.name}")

    def save_network_response(self, url: str, response_data: Any):
        """
        Save network response to JSONL file.

        Args:
            url: Request URL
            response_data: Response data
        """
        if not self.config.get('logging.save_network', True):
            return

        entry = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'data': response_data
        }

        with open(self.network_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def save_elements(self, elements: Dict[str, Any], name: str = "elements"):
        """
        Save element inventory.

        Args:
            elements: Element inventory data
            name: File name prefix
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.run_dir / f"{name}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(elements, f, indent=2)

        self.debug(f"Saved element inventory: {filename.name}")

    def save_universal_extraction(self, extraction: Dict[str, Any], iteration: int):
        """
        Save universal extraction data (comprehensive).

        Args:
            extraction: Universal extraction data
            iteration: Iteration number
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.run_dir / f"universal_extraction_iter{iteration}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(extraction, f, indent=2, ensure_ascii=False)

        self.info(f"Saved UNIVERSAL extraction: {filename.name} ({extraction.get('_stats', {}).get('total_data_points', 0)} data points)")

    def save_final_status(self, status: str, reason: str, details: Dict[str, Any]):
        """
        Save final run status.

        Args:
            status: Status (SUCCESS, FAILED, BLOCKED)
            reason: Reason for status
            details: Additional details
        """
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'reason': reason,
            'details': details
        }

        filename = self.run_dir / "final_status.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)

        self.info(f"Final status: {status} - {reason}")

    def save_iteration_debug(self, iteration: int, stage: str, content: str):
        """
        Save detailed debug info for each iteration stage.

        Args:
            iteration: Iteration number
            stage: Stage name (extraction, prompt, response, code, result)
            content: Content to save
        """
        filename = self.run_dir / f"iteration{iteration}_{stage}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        self.debug(f"Saved {stage} debug: {filename.name}")
