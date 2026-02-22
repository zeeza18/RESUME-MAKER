"""
Analyze and display universal extraction results.
Shows what the powerful extractor captured.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def print_section(title: str, data: Any, indent: int = 0):
    """Print a section with proper formatting."""
    prefix = "  " * indent
    print(f"\n{prefix}{'='*60}")
    print(f"{prefix}{title}")
    print(f"{prefix}{'='*60}")

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                print(f"{prefix}  {key}:")
                if isinstance(value, list):
                    print(f"{prefix}    Items: {len(value)}")
                    # Show first few items
                    for i, item in enumerate(value[:3], 1):
                        if isinstance(item, dict):
                            print(f"{prefix}      [{i}] {item}")
                        else:
                            print(f"{prefix}      [{i}] {item}")
                elif isinstance(value, dict):
                    for k, v in list(value.items())[:10]:  # Limit to first 10
                        print(f"{prefix}      {k}: {v}")
            else:
                print(f"{prefix}  {key}: {value}")
    elif isinstance(data, list):
        print(f"{prefix}  Total items: {len(data)}")
        for i, item in enumerate(data[:5], 1):
            print(f"{prefix}    [{i}] {item}")


def analyze_extraction(extraction_file: Path):
    """Analyze and display extraction results."""
    if not extraction_file.exists():
        print(f"❌ File not found: {extraction_file}")
        return

    print(f"\n🔍 Analyzing: {extraction_file.name}")
    print("=" * 80)

    with open(extraction_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Display statistics
    if '_stats' in data:
        print_section("📊 EXTRACTION STATISTICS", data['_stats'])

    # Display metadata
    if 'metadata' in data:
        print_section("📄 PAGE METADATA", data['metadata'])

    # Display forms
    if 'forms' in data and data['forms']:
        print_section("📝 FORMS", {
            'count': len(data['forms']),
            'forms': data['forms']
        })

    # Display inputs (comprehensive)
    if 'inputs' in data and data['inputs']:
        print(f"\n📥 INPUTS ({len(data['inputs'])} total)")
        print("="*80)
        for i, inp in enumerate(data['inputs'][:20], 1):  # Show first 20
            purpose = inp.get('purpose', 'unknown')
            label = inp.get('label', inp.get('placeholder', inp.get('name', 'N/A')))
            required = "⚠️ REQUIRED" if inp.get('required') else ""
            print(f"  [{i}] {label}")
            print(f"      Type: {inp.get('type', 'text')} | Purpose: {purpose} {required}")
            if inp.get('data_attributes'):
                print(f"      Data attrs: {inp['data_attributes']}")

    # Display buttons
    if 'buttons' in data and data['buttons']:
        print(f"\n🔘 BUTTONS ({len(data['buttons'])} total)")
        print("="*80)
        for i, btn in enumerate(data['buttons'][:15], 1):
            text = btn.get('text', btn.get('aria_label', 'N/A'))
            purpose = btn.get('purpose', 'unknown')
            disabled = " [DISABLED]" if btn.get('disabled') else ""
            print(f"  [{i}] \"{text}\" - {purpose}{disabled}")

    # Display selects/dropdowns
    if 'selects' in data and data['selects']:
        print(f"\n📋 DROPDOWNS ({len(data['selects'])} total)")
        print("="*80)
        for i, sel in enumerate(data['selects'][:10], 1):
            label = sel.get('label', sel.get('name', 'N/A'))
            options = sel.get('option_count', 0)
            print(f"  [{i}] {label} ({options} options)")

    # Display hidden fields
    if 'hidden_fields' in data and data['hidden_fields']:
        print(f"\n🔒 HIDDEN FIELDS ({len(data['hidden_fields'])})")
        print("="*80)
        for field in data['hidden_fields'][:10]:
            print(f"  {field.get('name', 'N/A')}: {field.get('value', '')[:50]}")

    # Display data attributes
    if 'data_attributes' in data:
        count = data['data_attributes'].get('count', 0)
        if count > 0:
            print(f"\n📦 DATA ATTRIBUTES ({count} elements with data-* attributes)")
            print("="*80)
            for elem in data['data_attributes'].get('elements_with_data', [])[:5]:
                print(f"  {elem.get('tag', 'N/A')} - {elem.get('data', {})}")

    # Display JavaScript context
    print_section("🔧 JAVASCRIPT CONTEXT", {
        'localStorage': f"{len(data.get('local_storage', {}))} keys" if data.get('local_storage') else "Empty",
        'sessionStorage': f"{len(data.get('session_storage', {}))} keys" if data.get('session_storage') else "Empty",
        'cookies': f"{len(data.get('cookies', []))} cookies" if data.get('cookies') else "No cookies",
        'global_vars': list(data.get('global_variables', {}).keys()) if data.get('global_variables') else "None detected",
    })

    # Display framework detection
    frameworks = []
    if data.get('react_state', {}).get('detected'):
        frameworks.append(f"React {data['react_state'].get('version', 'unknown')}")
    if data.get('vue_state', {}).get('detected'):
        frameworks.append(f"Vue {data['vue_state'].get('version', 'unknown')}")
    if data.get('angular_state', {}).get('detected'):
        frameworks.append(f"Angular {data['angular_state'].get('version', 'unknown')}")

    if frameworks:
        print(f"\n⚛️  FRAMEWORKS DETECTED: {', '.join(frameworks)}")

    # Display job application info
    if 'job_data' in data:
        print_section("💼 JOB APPLICATION DATA", data['job_data'])

    # Display file upload fields
    if 'file_upload_requirements' in data and data['file_upload_requirements']:
        print(f"\n📎 FILE UPLOADS ({len(data['file_upload_requirements'])})")
        print("="*80)
        for upload in data['file_upload_requirements']:
            label = upload.get('label', 'N/A')
            accept = upload.get('accept', 'any')
            required = "⚠️ REQUIRED" if upload.get('required') else ""
            print(f"  {label} ({upload.get('purpose', 'document')}) - Accepts: {accept} {required}")

    # Display CSRF tokens
    if 'csrf_tokens' in data and data['csrf_tokens']:
        print(f"\n🔐 CSRF TOKENS ({len(data['csrf_tokens'])})")
        print("="*80)
        for token in data['csrf_tokens']:
            print(f"  {token.get('name', 'N/A')}: {token.get('value', '')[:30]}...")

    # Display validation rules
    if 'input_constraints' in data and data['input_constraints']:
        print(f"\n✅ VALIDATION CONSTRAINTS ({len(data['input_constraints'])})")
        print("="*80)
        for constraint in data['input_constraints'][:10]:
            name = constraint.get('name', constraint.get('id', 'N/A'))
            rules = []
            if constraint.get('required'):
                rules.append('required')
            if constraint.get('pattern'):
                rules.append(f"pattern: {constraint['pattern']}")
            if constraint.get('minlength'):
                rules.append(f"minlength: {constraint['minlength']}")
            if constraint.get('maxlength'):
                rules.append(f"maxlength: {constraint['maxlength']}")
            print(f"  {name}: {', '.join(rules)}")

    # Display iframes
    if 'iframes' in data and data['iframes']:
        print(f"\n🖼️  IFRAMES ({len(data['iframes'])})")
        print("="*80)
        for iframe in data['iframes']:
            print(f"  {iframe.get('src', 'N/A')}")

    # Display shadow DOM
    if 'shadow_dom' in data:
        count = data['shadow_dom'].get('count', 0)
        if count > 0:
            print(f"\n👻 SHADOW DOM ({count} shadow roots detected)")

    # Display web components
    if 'web_components' in data and data['web_components']:
        print(f"\n🧩 CUSTOM WEB COMPONENTS ({len(data['web_components'])})")
        print("="*80)
        print(f"  {', '.join(data['web_components'])}")

    # Display API endpoints
    if 'api_endpoints' in data and data['api_endpoints']:
        print(f"\n🌐 API ENDPOINTS ({len(data['api_endpoints'])})")
        print("="*80)
        for endpoint in data['api_endpoints'][:10]:
            print(f"  {endpoint}")

    # Display accessibility info
    if 'aria_tree' in data:
        count = data['aria_tree'].get('count', 0)
        if count > 0:
            print(f"\n♿ ACCESSIBILITY - {count} ARIA attributes detected")

    # Display text analysis
    if 'text_analysis' in data:
        print_section("📝 TEXT ANALYSIS", data['text_analysis'])

    # Display semantic structure
    if 'semantic_structure' in data:
        print_section("🏗️  SEMANTIC HTML5 STRUCTURE", data['semantic_structure'])

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        # Find most recent run
        runs_dir = Path(__file__).parent / "runs"
        if not runs_dir.exists():
            print("❌ No runs directory found")
            return

        run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
        if not run_dirs:
            print("❌ No runs found")
            return

        latest_run = run_dirs[0]
        print(f"📂 Using latest run: {latest_run.name}")

        # Find universal extraction file
        extraction_files = list(latest_run.glob("universal_extraction_*.json"))
        if not extraction_files:
            print("❌ No universal extraction file found")
            print(f"   Looking in: {latest_run}")
            return

        extraction_file = extraction_files[0]
    else:
        extraction_file = Path(sys.argv[1])

    analyze_extraction(extraction_file)


if __name__ == "__main__":
    main()
