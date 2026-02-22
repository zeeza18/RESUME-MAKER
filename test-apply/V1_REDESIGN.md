# V1 Universal OpenAI-Driven Automation - Complete Redesign

## 🎯 What Changed

### **Before (Old System):**
- Hardcoded action types and flows
- Limited to specific patterns
- Complex state machine
- Site-specific logic

### **After (V1 New System):**
- ✅ **100% OpenAI-driven** - No hardcoded flows
- ✅ **Universal** - Works on ANY job site
- ✅ **Simple loop:** Extract → OpenAI → Execute → Repeat
- ✅ **Conversation memory** - OpenAI remembers what it did
- ✅ **Auto-handles cookies/policies**
- ✅ **Creative liberty** - Generates answers for open-ended questions
- ✅ **Retry mechanism** - 3 attempts if code fails
- ✅ **Full page text** sent to OpenAI

---

## 📁 New/Updated Files

### **1. config.yaml**
- Updated with your profile:
  - Name: Mohammed Azeezulla
  - Email: mohammedazeezulla6996@gmail.com
  - Phone: 8723302122
  - Resume: `docs/latex/main.pdf`
  - F1 Student visa status
- Max iterations: 50
- Auto-accept cookies: true
- Max retries: 3

### **2. apply/brain.py** (NEW)
**Universal OpenAI Brain**
- Maintains conversation history (memory)
- Sends full page extraction to OpenAI
- Gets Playwright code back
- Handles 4 statuses:
  - `continue` - Keep going
  - `success` - Application submitted!
  - `stuck` - Can't proceed
  - `human_needed` - CAPTCHA or manual action required

### **3. apply/executor.py** (NEW)
**Code Executor with Retry**
- Executes Playwright code from OpenAI
- Retries up to 3 times if fails
- Logs all errors
- Can ask OpenAI for new code if needed

### **4. apply/__main__.py** (UPDATED)
**Simplified Main Loop**
```python
while iteration < 50:
    # 1. Extract page (text, buttons, links, inputs)
    extraction = extract_page()

    # 2. Ask OpenAI what to do
    action = brain.decide_next_action(extraction)

    # 3. Check status
    if action.status == 'success':
        return SUCCESS!
    elif action.status == 'stuck':
        return FAILED
    elif action.status == 'human_needed':
        wait_for_you()
    elif action.status == 'continue':
        # 4. Execute Playwright code
        executor.execute(action.playwright_code)
```

### **5. browser.py** (UPDATED)
- Changed default wait from `networkidle` to `domcontentloaded`
- Increased timeout to 60 seconds
- Fixes navigation timeout issues

### **6. logger.py** (UPDATED)
- UTF-8 encoding for console
- No more Unicode errors on Windows

### **7. config.py** (UPDATED)
- Removed resume warning

---

## 🚀 How It Works

### **Flow:**
```
User: python -m apply https://job-site.com/apply

1. Browser opens to URL

2. LOOP (max 50 iterations):

   a. EXTRACT PAGE:
      - Full text content
      - All buttons (with id, class, aria-label, text)
      - All links (with text, href)
      - All inputs (with id, name, type, label, placeholder)

   b. SEND TO OPENAI:
      - Current URL
      - Full page extraction
      - Your profile data (name, email, phone, resume, visa status)
      - Conversation history (what was done before)
      - Goal: "Apply to this job"

   c. OPENAI DECIDES:
      - Sees "Accept Cookies" → Generates code to click it
      - Sees login form → Generates code to fill email/password
      - Sees job description → Clicks "Apply Now"
      - Sees form fields → Fills name, email, phone, uploads resume
      - Sees "Why do you want to work here?" → Generates professional answer
      - Sees "Application Submitted" → Returns status: success

   d. EXECUTE CODE:
      - Runs the Playwright code OpenAI generated
      - If fails, retries 3 times
      - If still fails, OpenAI sees error next iteration and tries different approach

   e. CHECK STATUS:
      - continue → Loop again
      - success → DONE! ✅
      - stuck → STOP ❌
      - human_needed → Pause, wait for you to solve CAPTCHA, then continue

3. END: Success or failure saved to runs/TIMESTAMP/final_status.json
```

---

## 🎯 OpenAI's Intelligence

### **What OpenAI Does:**
1. **Cookies/Policies:** Automatically accepts them
2. **Sign-in:** Uses your email, handles password
3. **Form filling:** Uses profile data intelligently
4. **File uploads:** Uploads resume from `docs/latex/main.pdf`
5. **Open-ended questions:** Generates simple professional answers
6. **Multi-step forms:** Clicks "Next" → "Next" → "Submit"
7. **Success detection:** Recognizes "Application Submitted", "Thank you for applying"
8. **Error handling:** If code fails, tries different approach

### **Example Generations:**
```python
# Cookie prompt
page.get_by_role('button', name='Accept Cookies').click()

# Login form
page.get_by_label('Email').fill('mohammedazeezulla6996@gmail.com')
page.get_by_label('Password').fill('***')
page.get_by_role('button', name='Sign In').click()

# Application form
page.get_by_label('Full Name').fill('Mohammed Azeezulla')
page.get_by_label('Phone Number').fill('8723302122')
page.get_by_label('Email').fill('mohammedazeezulla6996@gmail.com')
page.locator('input[type="file"]').set_input_files('docs/latex/main.pdf')
page.get_by_role('button', name='Submit Application').click()

# Open-ended question
page.get_by_label('Why do you want to work here?').fill(
    'I am interested in this position because it aligns with my skills and career goals. I am eager to contribute to your team and grow professionally.'
)
```

---

## 🔧 Usage

### **Run:**
```bash
cd test-apply
python -m apply https://careers.example.com/job/123456
```

### **What You'll See:**
```
16:34:18 - INFO - OK OpenAI API key loaded
16:34:18 - INFO - OK OpenAI API client initialized
16:34:18 - INFO - Starting browser...
16:34:19 - INFO - Browser started (chromium, headless=False)
16:34:19 - INFO - Navigating to https://...

============================================================
ITERATION 1
URL: https://careers.example.com/job/123456
============================================================
Extracted: 0 inputs, 3 buttons, 5 links

OpenAI Decision: continue
Reasoning: I see an "Accept Cookies" button, clicking it first

Executing: Click accept cookies button
Code: page.get_by_role('button', name='Accept All').click()
Execution successful

============================================================
ITERATION 2
URL: https://careers.example.com/apply
============================================================
[continues until success or stuck]
```

---

## 🛡️ Safety Features

1. **Max 50 iterations** - Won't run forever
2. **3 retry attempts** - Code failures are handled
3. **CAPTCHA detection** - Pauses for you to solve
4. **Password handling** - Uses env variable (set `JOB_APP_PASSWORD`)
5. **All artifacts saved** - HTML snapshots, logs, final status

---

## 📝 Next Steps (V2)

- [ ] Extract profile data from resume PDF automatically
- [ ] Better prompts for creative answers
- [ ] Screenshot-based extraction (OpenAI vision)
- [ ] Multi-resume support (tailor to job)
- [ ] Cover letter generation
- [ ] Success rate tracking

---

## ⚙️ Config Reference

```yaml
profile:
  name: "Mohammed Azeezulla"
  email: "mohammedazeezulla6996@gmail.com"
  phone: "8723302122"
  resume_path: "docs/latex/main.pdf"
  visa_status: "F1 Student"
  work_authorization: "Requires Sponsorship"

automation:
  max_iterations: 50
  max_code_retries: 3
  auto_accept_cookies: true
```

---

## 🎉 Ready to Test!

Your V1 system is now **completely universal** and **OpenAI-driven**!

Try it on any job site - it will adapt automatically. 🚀
