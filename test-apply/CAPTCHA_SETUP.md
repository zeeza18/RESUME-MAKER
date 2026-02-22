# 2Captcha Setup Guide

## 🔧 Quick Setup (5 minutes)

### **Step 1: Get 2Captcha API Key**

1. **Sign up:** https://2captcha.com/enterpage
2. **Add funds:** Minimum $3 (solves ~1000 CAPTCHAs)
3. **Get API key:** https://2captcha.com/setting/api-key
4. **Copy your API key**

### **Step 2: Add to .env**

Open `.env` and add your key:
```
TWOCAPTCHA_API_KEY=your_api_key_here
```

### **Step 3: Install Package**

```bash
pip install twocaptcha-python
```

### **Step 4: Done!** ✅

CAPTCHAs will now be solved automatically!

---

## 💰 **Pricing**

| CAPTCHA Type | Price per 1000 |
|--------------|----------------|
| reCAPTCHA v2 | $2.99 |
| reCAPTCHA v3 | $2.99 |
| hCaptcha | $2.99 |

**Example:**
- 10 job applications × 2 CAPTCHAs each = 20 CAPTCHAs
- Cost: ~$0.06 (6 cents)

---

## 🎯 **How It Works**

### **When CAPTCHA Detected:**

```
1. System detects CAPTCHA (reCAPTCHA v2, hCaptcha, etc.)
2. Extracts site key and page URL
3. Sends to 2Captcha API
4. Waits 10-30 seconds for human solver
5. Receives solution token
6. Submits to page
7. Continues automation ✅
```

### **What You'll See:**

```
ITERATION 3
URL: https://careers.example.com/signup
Extracted: 3 inputs, 2 buttons, 1 links
OpenAI Decision: human_needed
Reasoning: reCAPTCHA v2 detected on signup page

CAPTCHA/Human intervention needed: reCAPTCHA detected
Attempting automatic CAPTCHA solving with 2Captcha...
Detecting CAPTCHA type...
Detected: reCAPTCHA v2
Solving reCAPTCHA v2 with 2Captcha...
Page URL: https://careers.example.com/signup
Site Key: 6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-
CAPTCHA solved! Token: 03AGdBq25SxXT-pmSeBXhgqGd...
CAPTCHA solution submitted successfully
CAPTCHA solved automatically! Continuing...

ITERATION 4
[continues normally]
```

---

## 🛡️ **Fallback to Manual**

If 2Captcha fails (rare):
1. System automatically waits for you
2. You solve CAPTCHA manually
3. System continues

**You're always covered!** ✅

---

## 📊 **Supported CAPTCHA Types**

✅ **reCAPTCHA v2** (checkbox "I'm not a robot")
✅ **reCAPTCHA v2 Invisible**
✅ **reCAPTCHA v3**
✅ **hCaptcha**
✅ **FunCaptcha**
❌ Image CAPTCHAs (rare on job sites)

---

## ⚙️ **Without 2Captcha API Key**

If you don't add the API key:
- System works normally
- **Manual mode:** Pauses when CAPTCHA appears
- You solve it manually
- System continues

---

## 🎉 **Ready!**

Add your API key to `.env` and test it:

```bash
cd test-apply
python -m apply https://site-with-captcha.com
```

Watch it auto-solve! 🚀
