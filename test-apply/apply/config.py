"""
Configuration management with secure credential handling.
"""

import os
import sys
import yaml
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Application configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file. Defaults to config.yaml in project root.
        """
        # Load environment variables from .env
        load_dotenv()

        # Determine config path
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._password: Optional[str] = None

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default configuration. Copy config.example.yaml to config.yaml")
            self._config = self._default_config()
        else:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'profile': {
                'email': '',
                'first_name': '',
                'last_name': '',
                'phone': '',
                'resume_path': '',
            },
            'browser': {
                'headless': False,
                'browser_type': 'chromium',
                'slow_mo': 100,
                'viewport': {'width': 1280, 'height': 720}
            },
            'automation': {
                'max_iterations': 50,
                'max_scroll_attempts': 10,
                'action_delay': 1000,
                'page_timeout': 30000,
                'element_timeout': 10000,
            },
            'logging': {
                'level': 'DEBUG',  # Default to DEBUG for better visibility
                'save_snapshots': True,
                'save_network': True,
                'mask_secrets': True,
            },
            'credentials': {
                'password_env_var': 'JOB_APP_PASSWORD',
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'browser.headless')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_password(self, prompt_if_missing: bool = True) -> Optional[str]:
        """
        Get password securely from environment or prompt.

        Args:
            prompt_if_missing: If True, prompt user if password not found

        Returns:
            Password string or None
        """
        if self._password:
            return self._password

        # Try environment variable
        env_var = self.get('credentials.password_env_var', 'JOB_APP_PASSWORD')
        password = os.getenv(env_var)

        if password:
            self._password = password
            return password

        # Prompt if requested
        if prompt_if_missing:
            print(f"\nPassword not found in environment variable {env_var}")
            password = getpass.getpass("Enter password for job applications: ")
            self._password = password
            return password

        return None

    def get_profile(self) -> Dict[str, str]:
        """Get user profile information (includes password)."""
        profile = dict(self.get('profile', {}))
        # Add password from environment
        profile['password'] = self.get_password(prompt_if_missing=False) or ''
        return profile

    def mask_sensitive(self, text: str) -> str:
        """
        Mask sensitive information in text.

        Args:
            text: Text to mask

        Returns:
            Masked text
        """
        if not self.get('logging.mask_secrets', True):
            return text

        # Mask password
        if self._password and self._password in text:
            text = text.replace(self._password, '***MASKED***')

        # Mask email (partial)
        email = self.get('profile.email', '')
        if email and '@' in email:
            username, domain = email.split('@', 1)
            if len(username) > 2:
                masked_email = username[:2] + '***@' + domain
                text = text.replace(email, masked_email)

        return text

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if valid, False otherwise
        """
        # V1: Only require essential fields
        required_fields = ['profile.email', 'profile.name']

        missing = []
        for field in required_fields:
            value = self.get(field)
            if not value:
                missing.append(field)

        if missing:
            print(f"Error: Missing required configuration fields: {', '.join(missing)}")
            return False

        return True
