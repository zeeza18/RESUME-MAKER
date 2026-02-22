# Quick Setup Guide

Follow these steps to get started with the Job Application Automation Tool.

## Step 1: Install Dependencies

```bash
# Navigate to project directory
cd test-apply

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Step 2: Configure Your Profile

```bash
# Copy example files
copy config.example.yaml config.yaml  # Windows
cp config.example.yaml config.yaml    # macOS/Linux

copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

Edit `config.yaml` with your information:
```yaml
profile:
  email: "your.email@example.com"
  first_name: "Your First Name"
  last_name: "Your Last Name"
  phone: "+1234567890"
  resume_path: "./your_resume.pdf"  # Place your resume here
  # ... fill in other fields
```

## Step 3: Set Your Password Securely

Edit `.env` file:
```
JOB_APP_PASSWORD=your_password_here
```

**OR** just run the tool and it will prompt you for the password.

## Step 4: Add Your Resume

Copy your resume PDF to the project directory:
```bash
copy "C:\path\to\your\resume.pdf" resume.pdf
```

Or specify the full path in `config.yaml`:
```yaml
profile:
  resume_path: "C:/path/to/your/resume.pdf"
```

## Step 5: Test Run

```bash
python -m apply https://example.com/jobs/apply
```

Watch the browser open and the tool start working!

## What to Expect

1. **Browser opens** (you'll see it by default)
2. **Tool navigates** to the URL you provided
3. **Extracts page info** and determines what to do
4. **Fills forms** and clicks buttons automatically
5. **Pauses for CAPTCHAs** if detected (solve manually)
6. **Continues** through multi-step forms
7. **Stops** when application is submitted or blocked

## Output Location

Check `runs/` folder for:
- Action logs
- HTML snapshots
- Network captures
- Final status

## Common First-Time Issues

### "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### "config.yaml not found"
Make sure you copied `config.example.yaml` to `config.yaml`

### "Resume not found"
Check the path in `config.yaml` points to your actual resume file

### "Password prompt appears"
Either set `JOB_APP_PASSWORD` in `.env` or just enter it when prompted

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize `config.yaml` browser and automation settings
- Review run logs in `runs/` to see what happened
- Adjust timeouts or max iterations if needed

## Need Help?

Check:
1. This guide
2. Main README.md
3. Logs in `runs/latest/`
4. HTML snapshots to see what the tool saw

Happy job hunting! 🎯
