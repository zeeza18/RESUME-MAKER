# Debug Guide - Iteration-by-Iteration Tracking

## 🔍 What Gets Saved

For each iteration, the system now saves 5 detailed debug files:

### **Per Iteration Files:**
```
runs/20260212_165816/
├── iteration1_extraction.txt    # What was extracted from page
├── iteration1_prompt.txt         # What was sent to OpenAI
├── iteration1_response.txt       # What OpenAI responded
├── iteration1_code.txt          # Playwright code executed
├── iteration1_result.txt        # Execution result (success/error)
├── iteration2_extraction.txt
├── iteration2_prompt.txt
├── ... (and so on for each iteration)
```

### **Always Saved:**
```
├── actions.log                  # Full debug log
├── page_iter1.html             # HTML snapshot each iteration
├── elements_iter1.json         # Element inventory
├── network.jsonl               # All network requests
├── final_status.json           # Final result
```

---

## 📋 **File Contents**

### **1. iterationN_extraction.txt**
What was extracted from the page:
```
URL: https://careers.example.com/login

BUTTONS (3):
1. 'Accept All Cookies' (id=accept-btn, class=cookie-accept)
2. 'Sign In' (id=signin-btn, class=btn-primary)
3. 'Create Account' (id=signup-btn, class=btn-secondary)

LINKS (5):
1. 'Privacy Policy' -> https://example.com/privacy
2. 'Terms of Service' -> https://example.com/terms
...

INPUTS (2):
1. Email Address (type=email, name=email) [REQUIRED]
2. Password (type=password, name=password) [REQUIRED]

FULL PAGE TEXT:
Welcome to our careers page...
```

### **2. iterationN_prompt.txt**
Exactly what was sent to OpenAI:
```
ITERATION: 1
URL: https://careers.example.com/login

YOUR PROFILE DATA:
NAME: Mohammed Azeezulla
EMAIL: mohammedazeezulla6996@gmail.com
PHONE: 8723302122
...

PAGE CONTENT:
BUTTONS (3 total):
1. 'Accept All Cookies' (id='accept-btn')
...

TASK: Apply to this job successfully.

Based on the page content above, decide the next action.
...
```

### **3. iterationN_response.txt**
OpenAI's full JSON response:
```json
{
    "status": "continue",
    "reasoning": "I see a cookie consent banner with 'Accept All Cookies' button. I should accept it first before proceeding with the login.",
    "playwright_code": "page.get_by_role('button', name='Accept All Cookies').click()",
    "description": "Accept cookie consent"
}
```

### **4. iterationN_code.txt**
The Playwright code that was executed:
```python
page.get_by_role('button', name='Accept All Cookies').click()
```

### **5. iterationN_result.txt**
Result of execution:
```
SUCCESS
Description: Accept cookie consent
Code: page.get_by_role('button', name='Accept All Cookies').click()
```

OR if failed:
```
FAILED
Error: Error: locator.click: Timeout 10000ms exceeded
Code: page.get_by_role('button', name='Accept All Cookies').click()
```

---

## 🧪 **Testing 3 Sites**

When you test 3 different job sites, you'll get separate run directories:

```
runs/
├── 20260212_170001/    # Site 1 (e.g., Teradata)
│   ├── iteration1_extraction.txt
│   ├── iteration1_prompt.txt
│   ├── iteration1_response.txt
│   ├── iteration1_code.txt
│   ├── iteration1_result.txt
│   ├── iteration2_...
│   └── final_status.json
│
├── 20260212_170530/    # Site 2 (e.g., LinkedIn)
│   ├── iteration1_extraction.txt
│   ├── ...
│   └── final_status.json
│
└── 20260212_171100/    # Site 3 (e.g., Indeed)
    ├── iteration1_extraction.txt
    ├── ...
    └── final_status.json
```

---

## 🔧 **How to Debug**

### **If something fails:**

1. **Open the run directory:**
   ```
   cd runs/20260212_165816
   ```

2. **Check final_status.json:**
   ```json
   {
     "status": "STUCK",
     "reason": "Could not find apply button",
     "iteration": 5
   }
   ```

3. **Go to that iteration:**
   - Open `iteration5_extraction.txt` - See what was on the page
   - Open `iteration5_prompt.txt` - See what OpenAI saw
   - Open `iteration5_response.txt` - See what OpenAI decided
   - Open `iteration5_code.txt` - See what code ran
   - Open `iteration5_result.txt` - See if it worked

4. **Find the problem:**
   - ❌ **Extraction wrong?** - Check DOM extractors
   - ❌ **OpenAI confused?** - Improve prompt
   - ❌ **Code failed?** - Check Playwright selector
   - ❌ **Element not found?** - Check page_iter5.html

5. **Keep the working iterations:**
   - If iteration 1-4 worked, keep those approaches
   - Only fix iteration 5

---

## 📊 **Example Debug Session**

```bash
# Run test
python -m apply https://careers.teradata.com/job/123

# Check result
cat runs/20260212_165816/final_status.json
# Shows: STUCK at iteration 3

# Debug iteration 3
cat runs/20260212_165816/iteration3_extraction.txt
# Shows: Found "Apply Now" button

cat runs/20260212_165816/iteration3_response.txt
# OpenAI decided: Click "Apply Now"

cat runs/20260212_165816/iteration3_code.txt
# Code: page.get_by_text('Apply Now').click()

cat runs/20260212_165816/iteration3_result.txt
# FAILED: Timeout - element not found

# Check HTML snapshot
cat runs/20260212_165816/page_iter3.html | grep -i "apply"
# Button actually says "Easy Apply" not "Apply Now"!

# Fixed! OpenAI will learn from this in next run
```

---

## ✅ **Ready to Test!**

Now run your test and you'll have complete visibility into every step:

```bash
python -m apply https://careers.teradata.com/job/123
```

Then check:
```bash
cd runs/[latest]/
ls iteration*
```

You'll see every step documented! 🎉
