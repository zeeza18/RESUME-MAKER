# Setup Guide for Claude-Powered Automation

## Quick Setup (3 Steps)

### Step 1: Get Claude API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Create a new key
5. Copy it (starts with `sk-ant-`)

### Step 2: Add to .env File

**IMPORTANT**: Add to `.env` in the **parent directory** (RESUME-MAKER root), NOT in test-apply!

Location: `C:\Users\azeez\PROJECTS\RESUME-MAKER\.env`

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Your `.env` file should look like:
```
# Claude API Key for automation
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# Job application password (optional)
JOB_APP_PASSWORD=your_password_here
```

### Step 3: Install New Dependency

```cmd
cd test-apply
pip install anthropic
```

Or reinstall all:
```cmd
pip install -r requirements.txt
```

## Verify Setup

```cmd
python verify_setup.py
```

Should show:
```
✓ Claude API key loaded
✓ Claude API client initialized
```

## Run Your First Claude-Powered Application

```cmd
python -m apply "YOUR_JOB_URL_HERE"
```

**Remember: Use quotes around the URL!**

## What Happens

1. **Extract**: Tool extracts all page elements
2. **Ask Claude**: Sends to Claude with goal
3. **Claude Decides**: Returns Playwright code + reasoning
4. **Execute**: Runs Claude's code
5. **Repeat**: On every page change

## Example Output

```
============================================================
🧠 ASKING CLAUDE FOR DECISION...
============================================================

ITERATION: 1
GOAL: Submit a job application

BUTTONS AVAILABLE:
1. 'Apply Now'
2. 'Sign In'
3. 'Save Job'

============================================================
🎯 CLAUDE'S DECISION: click_button
📝 Reasoning: Clicking 'Apply Now' will initiate the application process
============================================================

Executing: page.get_by_role('button', name='Apply Now').click()

✓ Action successful
```

## Cost Estimate

- **Per page**: ~$0.01-0.03
- **Typical application**: 5-10 pages
- **Total per application**: ~$0.10-0.50

Worth it for intelligent, adaptive automation!

## Troubleshooting

### Error: "Claude API key not found"

**Check:**
1. `.env` file is in RESUME-MAKER root (not test-apply)
2. Key starts with `sk-ant-`
3. No spaces around `=` in .env
4. File is named exactly `.env` (not `.env.txt`)

**Verify location:**
```cmd
# Should exist
type "C:\Users\azeez\PROJECTS\RESUME-MAKER\.env"
```

### Error: "anthropic package not installed"

```cmd
pip install anthropic
```

### Error: "Failed to parse Claude response"

- Claude's response wasn't valid JSON
- Check logs for raw response
- Usually self-corrects on next iteration

### Claude makes unexpected decision

- Check what Claude saw (logged in detail)
- Claude adapts on next page
- Goal is always "Submit a job application"

## Tips for Best Results

### 1. Let It Run
Don't interrupt - Claude adapts through multiple pages.

### 2. Watch the Reasoning
Read Claude's reasoning to understand decisions.

### 3. Check Logs
Everything is logged - see what Claude saw and decided.

### 4. Resume Path
Make sure your resume file exists:
```yaml
# config.yaml
profile:
  resume_path: "./your_resume.pdf"
```

## Advantages Over Rule-Based

### Rule-Based (Old):
```python
if "apply" in button_text:
    click()
```
- Brittle
- Breaks on different wording
- Can't handle complexity

### Claude-Powered (New):
```
Extract → Send to Claude → Claude analyzes → Generates code → Execute
```
- Intelligent
- Adapts to any wording
- Handles complexity naturally

## What Claude Sees Each Time

```
GOAL: Submit a job application

PAGE CONTENT:
- All buttons with text
- All links with URLs
- All form inputs with labels
- Page text excerpt

QUESTION: What should I do next?
```

Claude returns:
```json
{
  "action_type": "click_button",
  "reasoning": "...",
  "playwright_code": "page.click(...)",
  "element_identifier": "Apply Now"
}
```

## API Key Security

✅ **Secure**:
- Stored in `.env` (gitignored)
- Loaded from environment
- Never hardcoded
- Not shown in logs

❌ **Never**:
- Commit `.env` to git
- Share your API key
- Hardcode in files

## Ready!

You're all set to run Claude-powered job application automation!

```cmd
python -m apply "https://jobs.example.com/apply"
```

Watch as Claude intelligently navigates through the entire application process! 🚀🧠
