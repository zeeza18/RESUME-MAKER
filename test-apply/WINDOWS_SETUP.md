# Windows Setup Guide

## Quick Fix for Your Current Issues

### Issue 1: Configuration Not Set Up

You need to fill in your personal information in `config.yaml`.

**Easy Way:**
```cmd
python quick_setup.py
```

This will ask you questions and set up your config automatically.

**Manual Way:**
Edit `config.yaml` and replace:
```yaml
profile:
  email: "your.email@example.com"  # ← Change this
  first_name: "John"                # ← Change this
  last_name: "Doe"                  # ← Change this
  phone: "+1234567890"              # ← Change this
  resume_path: "./resume.pdf"       # ← Change this
```

### Issue 2: URL Contains Special Characters

The error `'src' is not recognized` happens because Windows cmd treats `&` as a command separator.

**SOLUTION: Always wrap URLs in quotes!**

❌ **Wrong:**
```cmd
python -m apply https://jobs.lenovo.com/...?jobId=73488&src=LinkedIn
```

✅ **Correct:**
```cmd
python -m apply "https://jobs.lenovo.com/...?jobId=73488&src=LinkedIn"
```

### Issue 3: Cookie Consent Dialogs

The tool now automatically handles cookie consent dialogs! It will:
1. Detect "Accept", "Accept All", "I Agree" buttons
2. Click them automatically
3. Continue with the application

### Issue 4: Cloudflare Protection

The tool detects Cloudflare challenges and:
1. Waits 5 seconds for automatic completion
2. If still blocked, pauses and asks you to complete it manually
3. Resumes once you solve it

## Complete Setup Steps

### 1. Install Dependencies (One Time)

```cmd
cd test-apply

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Your Profile

**Option A: Interactive Setup (Recommended)**
```cmd
python quick_setup.py
```

**Option B: Manual Edit**
Edit `config.yaml` with your information.

### 3. Set Password Securely

**Option A: Environment Variable (Best)**
```cmd
set JOB_APP_PASSWORD=your_actual_password
```

**Option B: .env File**
Edit `.env` file:
```
JOB_APP_PASSWORD=your_actual_password
```

**Option C: Interactive Prompt**
Just run the tool and it will ask for your password.

### 4. Add Your Resume

Put your resume in the project folder:
```cmd
copy "C:\path\to\your\resume.pdf" resume.pdf
```

Or update the path in `config.yaml`:
```yaml
profile:
  resume_path: "C:/path/to/your/resume.pdf"  # Use forward slashes
```

### 5. Verify Setup

```cmd
python verify_setup.py
```

This checks everything is configured correctly.

### 6. Run the Tool

```cmd
python -m apply "YOUR_JOB_URL_HERE"
```

**IMPORTANT: Always use quotes around the URL!**

## Example: Running on Lenovo Jobs

```cmd
# Activate virtual environment (if not already activated)
venv\Scripts\activate

# Set password (if not in .env)
set JOB_APP_PASSWORD=your_password

# Run with URL in quotes
python -m apply "https://jobs.lenovo.com/en_US/careers/JobDetail?jobId=73488&src=LinkedIn&source=LinkedIn"
```

## What Happens When You Run It

1. **Browser Opens** - You'll see Chrome open (not hidden)
2. **Navigates to URL** - Goes to the job page
3. **Handles Cookie Consent** - Automatically clicks "Accept" if present
4. **Checks for Cloudflare** - Waits or asks you to complete
5. **Analyzes Page** - Extracts form fields, buttons, text
6. **Takes Actions** - Clicks "Apply", fills forms, uploads resume
7. **Continues** - Follows through sign-in, multi-step forms
8. **Completes** - Stops when application submitted or blocked

## Common Windows Issues

### 1. "python is not recognized"

Install Python 3.9+ from python.org or Microsoft Store.

### 2. "playwright not found"

```cmd
pip install playwright
playwright install chromium
```

### 3. "Permission denied" when installing

Run cmd as Administrator.

### 4. URLs not working

Always wrap URLs in quotes:
```cmd
python -m apply "URL_HERE"
```

### 5. Browser doesn't open

Check config.yaml:
```yaml
browser:
  headless: false  # Must be false to see browser
```

### 6. "Module not found"

Make sure virtual environment is activated:
```cmd
venv\Scripts\activate
```

## Viewing Results

After each run, check the `runs` folder:
```
runs\
└── 20260211_192716\
    ├── actions.log          ← What the tool did
    ├── page_*.html          ← Page snapshots
    ├── elements_*.json      ← What was found
    └── final_status.json    ← Why it stopped
```

## Debugging

### Turn on detailed logging

Edit `config.yaml`:
```yaml
logging:
  level: "DEBUG"  # Change from INFO to DEBUG
```

### Check what happened

```cmd
# View the latest run's log
type runs\latest\actions.log

# Or open the folder
explorer runs
```

## Cookie Consent Handling

The tool automatically handles these common cookie dialogs:
- "Accept"
- "Accept All"
- "I Agree"
- "Allow All"
- OneTrust cookie banners
- Generic cookie consent popups

It tries multiple strategies to find and click the accept button.

## Cloudflare Handling

If Cloudflare protection is detected:

1. **Automatic**: Tool waits 5 seconds for it to pass
2. **Manual**: If still blocked, you'll see:
   ```
   HUMAN INTERVENTION REQUIRED: Cloudflare challenge detected
   Please complete the task in the browser. Waiting up to 300 seconds...
   ```
3. Complete the challenge in the browser
4. Tool automatically resumes

## Next Steps After Setup

1. **Test on a simple job posting** first
2. **Watch what happens** in the browser
3. **Review the logs** in `runs/` folder
4. **Adjust config** if needed (timeouts, delays)
5. **Use on real applications**

## For the Lenovo Job Specifically

```cmd
# Full command with proper URL quoting
python -m apply "https://jobs.lenovo.com/en_US/careers/JobDetail?jobId=73488&src=LinkedIn&source=LinkedIn#"
```

The tool will:
1. Navigate to the Lenovo job page
2. Handle any cookie consent
3. Find and click "Apply" or "Apply Now" button
4. Follow through their application process
5. Fill in your information from config.yaml
6. Upload your resume
7. Submit the application

## Getting Help

If something goes wrong:

1. **Check logs**: `runs\latest\actions.log`
2. **Check config**: Run `python verify_setup.py`
3. **Check snapshots**: Open `runs\latest\*.html` in browser
4. **Enable debug**: Set logging level to DEBUG

## Tips for Success

✅ **DO:**
- Always wrap URLs in quotes
- Use forward slashes in paths: `C:/Users/...`
- Keep browser visible (headless: false)
- Review logs after each run
- Test on simple job postings first

❌ **DON'T:**
- Run URLs without quotes
- Use backslashes in paths
- Run in headless mode initially
- Ignore error messages
- Skip the verification step

## Quick Reference

```cmd
# Activate environment
venv\Scripts\activate

# Setup (first time)
python quick_setup.py

# Verify
python verify_setup.py

# Run (always quote URL)
python -m apply "YOUR_URL"

# Set password
set JOB_APP_PASSWORD=your_password
```

---

**You're ready to go! Start with the quick_setup.py script.**
