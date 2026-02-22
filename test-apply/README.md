# Job Application Automation Tool

An intelligent, goal-driven job application automation tool built with Playwright. This tool navigates modern React/JavaScript websites, intelligently extracts page content, and autonomously completes job applications while respecting CAPTCHAs and security measures.

## ⚠️ Important Disclaimer

This tool is designed for **personal use only** on websites where you have permission to apply. The tool:
- Will NOT bypass CAPTCHAs or anti-bot measures (pauses for manual completion)
- Will NOT use hardcoded site-specific selectors (works generically)
- Will NOT store passwords insecurely (uses environment variables or secure prompts)
- Should ONLY be used on sites you have legitimate access to

## 🌟 Features

### Intelligent Extraction
- **Network Interception**: Captures JSON responses (REST/GraphQL/Next.js data routes)
- **DOM Analysis**: Extracts structured element inventory with semantic understanding
- **Text Analysis**: Detects page state through visible text and key phrases
- **Lazy Loading**: Automatically scrolls to trigger dynamic content

### Goal-Driven Automation
- **State Machine**: Tracks application progress (landing → sign in → form fill → review → submit)
- **Semantic Understanding**: Identifies fields by purpose (email, name, phone, resume upload)
- **No Hardcoded Selectors**: Uses ARIA labels, accessible names, and semantic cues
- **Adaptive Navigation**: Handles redirects, SPAs, and multi-step forms

### Safety & Security
- **CAPTCHA Detection**: Pauses for manual completion when challenges detected
- **Credential Security**: Loads passwords from environment variables or secure prompts
- **Comprehensive Logging**: Saves HTML snapshots, network data, and action logs
- **Error Handling**: Detects blocking issues and provides clear failure reasons

## 📋 Requirements

- Python 3.9 or higher
- Windows/macOS/Linux

## 🚀 Installation

### 1. Clone or download this project

```bash
cd test-apply
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

## ⚙️ Configuration

### 1. Copy example configuration

```bash
# Windows
copy config.example.yaml config.yaml
copy .env.example .env

# macOS/Linux
cp config.example.yaml config.yaml
cp .env.example .env
```

### 2. Edit `config.yaml`

Fill in your profile information:

```yaml
profile:
  email: "your.email@example.com"
  first_name: "John"
  last_name: "Doe"
  phone: "+1234567890"
  linkedin_url: "https://linkedin.com/in/yourprofile"
  portfolio_url: "https://yourportfolio.com"
  resume_path: "./your_resume.pdf"
```

### 3. Set password securely

**Option A: Environment variable (recommended)**

Edit `.env`:
```
JOB_APP_PASSWORD=your_actual_password
```

**Option B: Command line (Linux/macOS)**
```bash
export JOB_APP_PASSWORD=your_password
```

**Option C: Interactive prompt**
Just run the tool and it will prompt you for the password.

### 4. Add your resume

Place your resume file in the project directory or specify the full path in `config.yaml`.

## 🎯 Usage

### Basic Usage

```bash
python -m apply https://example.com/jobs/apply
```

### With Custom Config

```bash
python -m apply https://example.com/jobs/apply --config my_config.yaml
```

### What Happens

1. **Browser Launch**: Opens a browser (visible by default, configurable)
2. **Navigation**: Goes to the target URL
3. **Extraction Loop**: On each page:
   - Captures network responses
   - Extracts DOM elements and text
   - Identifies current state (sign-in, form, review, etc.)
   - Plans next actions
   - Executes actions (fill forms, click buttons, upload files)
4. **Progress**: Continues through redirects and multi-step forms
5. **Completion**: Stops when confirmation page reached or blocked

### Browser Settings

Edit `config.yaml` to customize browser behavior:

```yaml
browser:
  # Set to true for background operation (can't solve CAPTCHAs)
  headless: false

  # chromium, firefox, or webkit
  browser_type: "chromium"

  # Slow down for debugging (milliseconds)
  slow_mo: 100
```

## 📁 Output

Each run creates a timestamped directory in `runs/`:

```
runs/
└── 20260211_143022/
    ├── actions.log              # Detailed action log
    ├── network.jsonl            # Captured API responses
    ├── page_iter1_*.html        # HTML snapshots per iteration
    ├── elements_iter1_*.json    # Element inventory per iteration
    └── final_status.json        # Final run status
```

## 🔍 How It Works

### State Detection

The tool identifies where you are in the application process:

- **LANDING**: Initial job listing page
- **SIGN_IN**: Login required
- **SIGN_UP**: Account creation
- **FORM_FILL**: Application form with inputs
- **REVIEW**: Review page before submission
- **CONFIRMATION**: Application submitted successfully
- **CAPTCHA**: Challenge detected (waits for manual completion)
- **BLOCKED**: Error or access issue

### Action Planning

Based on the detected state, the tool plans appropriate actions:

- **Job Listing**: Click "Apply" button
- **Sign In**: Fill email/password, click sign-in
- **Form Fill**:
  - Match inputs to profile fields semantically
  - Fill text inputs (name, email, phone, etc.)
  - Upload files (resume, cover letter)
  - Click "Next" or "Continue"
- **Review**: Click "Submit"

### Element Detection

No hardcoded selectors! The tool finds elements by:

- **Semantic analysis**: Autocomplete attributes, input types
- **Text matching**: Labels, placeholders, ARIA labels
- **Context**: Surrounding text and form structure
- **Purpose inference**: "email" field, "resume" upload, "submit" button

### Example: Email Field Detection

```python
# The tool tries multiple strategies:
1. Check autocomplete="email"
2. Check type="email"
3. Check label text contains "email"
4. Check placeholder contains "email"
5. Check name attribute contains "email"
```

## 🛡️ Safety Features

### CAPTCHA Handling

When a CAPTCHA is detected:
1. Tool pauses automation
2. Logs warning: "HUMAN INTERVENTION REQUIRED"
3. Waits up to 5 minutes for you to solve it
4. Resumes automatically after completion

### Password Security

Passwords are:
- Never hardcoded in code
- Never printed in logs (shown as `***`)
- Loaded from environment variables or secure prompts
- Masked in all output

### Error Detection

The tool detects and handles:
- Session expiration
- Access denied errors
- Required field validation
- Network failures
- Unexpected page states

## 🐛 Troubleshooting

### "Could not find element"

The tool uses semantic detection, but some sites may have unusual structures. Check:
- HTML snapshots in `runs/` to see what elements exist
- Element inventory JSON to see what was detected
- Logs to see what the tool tried

### "Maximum iterations reached"

Increase the limit in `config.yaml`:

```yaml
automation:
  max_iterations: 100  # Default is 50
```

### "CAPTCHA not solved in time"

Increase timeout in code or solve it faster. The tool waits 5 minutes by default.

### Forms not filling

Check:
- Profile data is complete in `config.yaml`
- Resume file path is correct and file exists
- Field detection in element inventory JSON

## 🔧 Advanced Configuration

### Timeouts

```yaml
automation:
  page_timeout: 30000        # Page load timeout (ms)
  element_timeout: 10000     # Element wait timeout (ms)
  action_delay: 1000         # Delay between actions (ms)
```

### Logging

```yaml
logging:
  level: "DEBUG"             # DEBUG, INFO, WARNING, ERROR
  save_snapshots: true       # Save HTML snapshots
  save_network: true         # Save API responses
  mask_secrets: true         # Mask passwords in logs
```

## 📝 Development

### Project Structure

```
test-apply/
├── apply/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── browser.py           # Playwright browser management
│   ├── config.py            # Configuration loader
│   ├── logger.py            # Logging utilities
│   ├── planner.py           # State machine & decision logic
│   ├── actor.py             # Action execution (click, fill, upload)
│   ├── detect.py            # CAPTCHA & success detection
│   └── extractors/
│       ├── __init__.py
│       ├── network.py       # Network response extraction
│       ├── dom.py           # DOM element extraction
│       └── text.py          # Text content extraction
├── runs/                    # Run artifacts
├── config.yaml              # Your configuration
├── .env                     # Environment variables
└── README.md
```

### Extending the Tool

#### Add New Field Types

Edit `apply/extractors/dom.py`, `_detect_input_purpose()`:

```python
if 'salary' in combined_text:
    return 'salary'
```

Edit `apply/planner.py`, `_plan_form_fill()`:

```python
field_mapping = {
    'salary': profile.get('expected_salary'),
    # ... other fields
}
```

#### Add New Page States

Edit `apply/planner.py`, add to `State` enum and implement handler:

```python
class State(Enum):
    # ... existing states
    QUESTIONNAIRE = "questionnaire"

def _plan_questionnaire(self, dom_data):
    # Your logic here
    pass
```

## ⚖️ Legal & Ethical Usage

This tool should be used responsibly:

✅ **Acceptable Use**:
- Applying to jobs where you meet qualifications
- Automating repetitive form filling for legitimate applications
- Using on sites where you have permission
- Personal use to speed up your job search

❌ **Unacceptable Use**:
- Mass spamming applications
- Bypassing security measures
- Applying to jobs you're not qualified for
- Using on sites that prohibit automation
- Commercial use without proper authorization

By using this tool, you agree to:
- Use it ethically and responsibly
- Respect website terms of service
- Not attempt to bypass CAPTCHAs or security measures
- Only apply to positions you're genuinely interested in

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `runs/` directory
3. Check element inventory to see what was detected

## 🎉 Credits

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [PyYAML](https://pyyaml.org/) - Configuration management

---

**Remember**: Use this tool ethically and responsibly. Good luck with your job search! 🚀
