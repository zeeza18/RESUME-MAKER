"""
Quick setup script to help configure the tool.
"""

import yaml
from pathlib import Path


def main():
    print("=" * 60)
    print("Job Application Tool - Quick Setup")
    print("=" * 60)

    config_path = Path("config.yaml")

    if not config_path.exists():
        print("\nError: config.yaml not found!")
        print("Creating from example...")
        import shutil
        shutil.copy("config.example.yaml", "config.yaml")

    print("\nPlease provide your information:")
    print("(Press Enter to skip optional fields)\n")

    # Collect information
    email = input("Email address: ").strip()
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    phone = input("Phone number (e.g., +1234567890): ").strip() or "+1234567890"

    linkedin = input("LinkedIn URL (optional): ").strip() or "https://linkedin.com/in/yourprofile"
    portfolio = input("Portfolio URL (optional): ").strip() or ""
    github = input("GitHub URL (optional): ").strip() or ""

    resume_path = input("Resume file path (e.g., ./resume.pdf): ").strip() or "./resume.pdf"

    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Update profile
    config['profile']['email'] = email
    config['profile']['first_name'] = first_name
    config['profile']['last_name'] = last_name
    config['profile']['phone'] = phone
    config['profile']['linkedin_url'] = linkedin
    config['profile']['resume_path'] = resume_path

    if portfolio:
        config['profile']['portfolio_url'] = portfolio
    if github:
        config['profile']['github_url'] = github

    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("\n" + "=" * 60)
    print("✓ Configuration saved!")
    print("=" * 60)

    print(f"\nProfile:")
    print(f"  Name: {first_name} {last_name}")
    print(f"  Email: {email}")
    print(f"  Phone: {phone}")
    print(f"  Resume: {resume_path}")

    # Check resume
    if not Path(resume_path).exists():
        print(f"\n⚠ WARNING: Resume file not found at {resume_path}")
        print("  Please make sure your resume file is in the correct location.")

    # Password setup
    print("\n" + "=" * 60)
    print("Password Setup")
    print("=" * 60)
    print("\nFor security, set your password as an environment variable:")
    print("\nWindows:")
    print('  set JOB_APP_PASSWORD=your_password')
    print('\nOr edit .env file:')
    print('  JOB_APP_PASSWORD=your_password')

    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n1. Set your password (see above)")
    print("2. Verify setup: python verify_setup.py")
    print('3. Run automation: python -m apply "YOUR_JOB_URL"')
    print("\n⚠ IMPORTANT: Wrap the URL in quotes to avoid Windows cmd issues!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
