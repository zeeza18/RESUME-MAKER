"""
Setup verification script.

Run this to verify your installation is correct.
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False


def check_dependencies():
    """Check required packages."""
    print("\nChecking dependencies...")
    required = [
        'playwright',
        'yaml',
        'bs4',
        'lxml',
        'dotenv'
    ]

    all_ok = True
    for package in required:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'bs4':
                import bs4
            elif package == 'lxml':
                import lxml
            elif package == 'dotenv':
                import dotenv
            elif package == 'playwright':
                import playwright

            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (not installed)")
            all_ok = False

    return all_ok


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("\nChecking Playwright browsers...")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("  ✓ Chromium browser installed")
                return True
            except Exception as e:
                print(f"  ✗ Chromium browser not installed")
                print(f"     Run: playwright install chromium")
                return False

    except Exception as e:
        print(f"  ✗ Error checking browsers: {e}")
        return False


def check_config_files():
    """Check if config files exist."""
    print("\nChecking configuration files...")

    config_path = Path("config.yaml")
    env_path = Path(".env")

    config_exists = config_path.exists()
    env_exists = env_path.exists()

    if config_exists:
        print("  ✓ config.yaml exists")
    else:
        print("  ⚠ config.yaml not found")
        print("     Copy config.example.yaml to config.yaml")

    if env_exists:
        print("  ✓ .env exists")
    else:
        print("  ⚠ .env not found (optional)")
        print("     Copy .env.example to .env to set password")

    return config_exists


def check_config_validity():
    """Check if config is valid."""
    print("\nChecking configuration validity...")

    try:
        from apply.config import Config

        config = Config()

        # Check key fields
        email = config.get('profile.email')
        first_name = config.get('profile.first_name')
        last_name = config.get('profile.last_name')

        if email and first_name and last_name:
            print(f"  ✓ Profile configured: {first_name} {last_name}")
            print(f"    Email: {email}")

            # Check resume
            resume_path = config.get('profile.resume_path')
            if resume_path:
                resume_file = Path(resume_path)
                if resume_file.exists():
                    print(f"  ✓ Resume found: {resume_path}")
                else:
                    print(f"  ⚠ Resume not found: {resume_path}")
            else:
                print("  ⚠ Resume path not set")

            return True
        else:
            print("  ✗ Required profile fields not filled")
            print("    Please edit config.yaml")
            return False

    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False


def main():
    """Run all checks."""
    print("="*60)
    print("Job Application Automation - Setup Verification")
    print("="*60)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_playwright_browsers(),
        check_config_files(),
        check_config_validity()
    ]

    print("\n" + "="*60)

    if all(checks):
        print("✓ All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("  1. Review your config.yaml")
        print("  2. Set password in .env or prepare to enter it")
        print("  3. Run: python -m apply <URL>")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  • Install packages: pip install -r requirements.txt")
        print("  • Install browsers: playwright install chromium")
        print("  • Copy config: copy config.example.yaml config.yaml")
        print("  • Edit config.yaml with your information")

    print("="*60)


if __name__ == "__main__":
    main()
