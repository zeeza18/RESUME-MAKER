# Claude-Powered Job Application Automation

## 🧠 Pure Claude Intelligence - No Hardcoding!

The tool now uses **Claude API** to make ALL decisions. No predefined rules, no hardcoded keywords - just pure AI intelligence.

## How It Works

### 1. Extract Everything
```
- Buttons: ["Apply Now", "Sign In", "Save Job"]
- Links: ["Learn More", "Company Info"]
- Inputs: ["Email", "Password"]
- Page text: "Software Engineer position..."
```

### 2. Send to Claude
```
Goal: Submit a job application

Here's what's on the page:
- Buttons: [...]
- Inputs: [...]
- Page text: [...]

What should I do next?
```

### 3. Claude Decides
```json
{
  "action_type": "click_button",
  "reasoning": "The 'Apply Now' button will start the application process",
  "playwright_code": "page.get_by_role('button', name='Apply Now').click()",
  "element_identifier": "Apply Now"
}
```

### 4. Execute Claude's Code
```python
page.get_by_role('button', name='Apply Now').click()
```

### 5. Repeat on Page Change
```
Page changed → Extract again → Ask Claude again → Execute → Repeat
```

## Setup

### 1. Add Claude API Key

Edit `.env` in `RESUME-MAKER` root directory:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 2. Install Dependencies
```cmd
pip install -r requirements.txt
```

This now includes the `anthropic` package.

### 3. Run
```cmd
python -m apply "YOUR_JOB_URL"
```

## What You'll See

```
============================================================
🧠 ASKING CLAUDE FOR DECISION...
============================================================

ITERATION: 1
GOAL: Submit a job application
CURRENT URL: https://jobs.example.com/123

BUTTONS AVAILABLE:
1. 'Apply Now'
2. 'Sign In'
3. 'Save Job'

LINKS AVAILABLE:
1. 'Learn More' -> /about
2. 'Company Info' -> /company

FORM INPUTS AVAILABLE:
(none)

PAGE TEXT EXCERPT:
Software Engineer position at TechCorp...

============================================================
🎯 CLAUDE'S DECISION: click_button
📝 Reasoning: The 'Apply Now' button will start the application process
============================================================

Executing: page.get_by_role('button', name='Apply Now').click()
```

## Advantages

### ✅ **True Intelligence**
- Claude understands context and nuance
- Adapts to ANY page structure
- Handles complex scenarios

### ✅ **No Hardcoding**
- Zero predefined keywords
- No brittle rules
- Works on sites you've never seen

### ✅ **Transparent**
- See everything extracted
- Read Claude's reasoning
- Understand every decision

### ✅ **Self-Correcting**
- If something fails, Claude sees the new state
- Adapts strategy on the fly
- Learns from each page

## How Claude Decides

Claude analyzes:
1. **Goal**: "Submit a job application"
2. **Current state**: What's on the page
3. **Context**: Page text, available actions
4. **Strategy**: Best path to goal

Then generates:
- Specific Playwright code
- Reasoning for the action
- What to do next

## Example Flow

### Page 1: Job Listing
```
Claude sees: "Apply Now" button
Claude decides: Click it
Code: page.get_by_role('button', name='Apply Now').click()
```

### Page 2: Sign In
```
Claude sees: Email/Password inputs, "Sign In" button
Claude decides: Fill credentials and sign in
Code:
  page.get_by_label('Email').fill('user@example.com')
  page.get_by_label('Password').fill('password')
  page.get_by_role('button', name='Sign In').click()
```

### Page 3: Application Form
```
Claude sees: Name, Phone, Resume inputs, "Continue" button
Claude decides: Fill form fields
Code:
  page.get_by_label('First Name').fill('John')
  page.get_by_label('Last Name').fill('Doe')
  page.get_by_label('Phone').fill('+1234567890')
  page.get_by_role('button', name='Continue').click()
```

### Page 4: Confirmation
```
Claude sees: "Application submitted" text
Claude decides: Goal achieved, stop
```

## API Costs

- Claude API charges per token
- Typical run: 5-15 pages
- Each page: ~1,000-2,000 tokens
- Total: ~$0.10-0.50 per application

**Worth it for intelligent automation!**

## Configuration

Edit `.env` in parent directory:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional job application credentials
JOB_APP_PASSWORD=your_password
```

## Troubleshooting

### "Claude API key not found"
- Check `.env` file in `RESUME-MAKER` root
- Verify key starts with `sk-ant-`
- Ensure file is named exactly `.env`

### "anthropic package not installed"
```cmd
pip install anthropic
```

### Claude makes wrong decision
- Check logs to see what Claude saw
- Claude adapts on next iteration
- If stuck, will timeout and save state

## Why This Is Better

### Old Approach (Hardcoded):
```python
if button_text == "Apply":
    click_button()
```
❌ Brittle, breaks easily

### New Approach (Claude-Powered):
```
1. Extract: ["Apply Now", "Easy Apply", "Quick Apply"]
2. Claude: "All three start application, pick first one"
3. Execute: page.click("Apply Now")
```
✅ Intelligent, adaptive, robust

## The Bottom Line

**Claude is the brain, the tool is just the hands.**

- Tool extracts what's there
- Claude decides what to do
- Tool executes Claude's code
- Repeat until goal achieved

**No hardcoding. No assumptions. Pure intelligence.** 🧠✨
