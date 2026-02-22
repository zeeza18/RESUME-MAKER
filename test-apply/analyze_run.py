"""
Analyze a run to see what happened.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def find_latest_run():
    """Find the most recent run directory."""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        return None

    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        return None

    # Sort by modification time
    latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
    return latest


def analyze_run(run_dir):
    """Analyze a specific run."""
    print("=" * 60)
    print(f"Analyzing Run: {run_dir.name}")
    print("=" * 60)

    # Check final status
    status_file = run_dir / "final_status.json"
    if status_file.exists():
        with open(status_file, 'r') as f:
            status = json.load(f)

        print("\nFinal Status:")
        print(f"  Status: {status.get('status')}")
        print(f"  Reason: {status.get('reason')}")
        print(f"  Timestamp: {status.get('timestamp')}")

        details = status.get('details', {})
        if details:
            print(f"  Iterations: {details.get('iteration', 'N/A')}")

    # Check network data
    network_file = run_dir / "network.jsonl"
    if network_file.exists():
        print("\nNetwork Responses:")
        with open(network_file, 'r') as f:
            lines = f.readlines()

        print(f"  Total responses: {len(lines)}")

        if lines:
            print("\n  Recent responses:")
            for line in lines[-5:]:  # Last 5
                try:
                    entry = json.loads(line)
                    url = entry.get('url', '')
                    # Shorten URL for display
                    if len(url) > 60:
                        url = url[:57] + "..."
                    print(f"    - {url}")

                    # Check if it has success/status
                    data = entry.get('data', {})
                    if isinstance(data, dict):
                        if 'success' in data:
                            print(f"      ⚠ Has 'success': {data['success']}")
                        if 'status' in data:
                            print(f"      ⚠ Has 'status': {data['status']}")
                except:
                    pass

    # Check HTML snapshots
    html_files = list(run_dir.glob("page_*.html"))
    if html_files:
        print(f"\nHTML Snapshots: {len(html_files)}")
        latest_html = max(html_files, key=lambda f: f.stat().st_mtime)
        print(f"  Latest: {latest_html.name}")

        # Read and analyze
        with open(latest_html, 'r', encoding='utf-8') as f:
            html = f.read()

        print(f"  Size: {len(html):,} bytes")

        # Look for key indicators
        indicators = {
            'Apply button': ['apply now', 'apply for', 'easy apply'],
            'Sign in': ['sign in', 'log in', 'email', 'password'],
            'Form inputs': ['<input', '<textarea', '<select'],
            'Success': ['application submitted', 'thank you for applying', 'application received'],
            'Error': ['error', 'invalid', 'required field'],
        }

        print("\n  Page content indicators:")
        for category, keywords in indicators.items():
            count = sum(html.lower().count(kw) for kw in keywords)
            if count > 0:
                print(f"    {category}: {count} matches")

    # Check actions log
    actions_log = run_dir / "actions.log"
    if actions_log.exists():
        print("\nActions Taken:")
        with open(actions_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find ACTION lines
        action_lines = [l for l in lines if 'ACTION:' in l]
        if action_lines:
            print(f"  Total actions: {len(action_lines)}")
            print("\n  Actions performed:")
            for line in action_lines[-10:]:  # Last 10 actions
                # Extract the action part
                if 'ACTION:' in line:
                    action = line.split('ACTION:', 1)[1].strip()
                    print(f"    - {action}")
        else:
            print("  No actions found in log")

    print("\n" + "=" * 60)
    print("Run Location:")
    print(f"  {run_dir}")
    print("=" * 60)

    # Recommendations
    print("\nRecommendations:")

    if status_file.exists():
        with open(status_file, 'r') as f:
            status = json.load(f)

        if status.get('status') == 'SUCCESS':
            print("  [OK] Run completed successfully")
            print("  [!] However, verify in the browser that the application was actually submitted")
            print("  [>] Check the HTML snapshot to see the final page")

        elif status.get('status') == 'BLOCKED':
            print("  [X] Run was blocked")
            print("  [>] Check the HTML snapshot to see what went wrong")
            print("  [!] You may need to manually complete a step")

        elif status.get('status') == 'TIMEOUT':
            print("  [!] Run reached max iterations")
            print("  [>] Try increasing max_iterations in config.yaml")

    print()


def main():
    if len(sys.argv) > 1:
        # Specific run directory provided
        run_dir = Path(sys.argv[1])
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}")
            return
    else:
        # Use latest run
        run_dir = find_latest_run()
        if not run_dir:
            print("No runs found in runs/ directory")
            return

    analyze_run(run_dir)


if __name__ == "__main__":
    main()
