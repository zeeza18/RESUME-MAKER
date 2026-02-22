# 🎯 COMPLETE UNIVERSAL EXTRACTOR

## Single Call - Everything Extracted!

The **CompleteUniversalExtractor** pulls EVERYTHING from a page in **one structured JSON** output.

### Single Method Call:
```python
complete_data = extractor.extract_complete_page(page, html)
```

### Returns Complete Page State:

```json
{
  "metadata": {
    "url": "https://...",
    "title": "AI / ML Engineer | HomeServe",
    "viewport": {"width": 1280, "height": 720},
    "charset": "utf-8",
    "language": "en"
  },

  "interactive_elements": {
    "buttons": [
      {
        "text": "Apply now",
        "tag": "button",
        "type": "submit",
        "id": "apply-btn",
        "name": "submit",
        "class": ["btn", "btn-primary"],
        "aria_label": "Submit application",
        "disabled": false,
        "purpose": "apply",           ← AI-DETECTED PURPOSE!
        "form_id": "job-application",
        "data_attrs": {
          "data-job-id": "12345",     ← HIDDEN DATA!
          "data-action": "submit"
        },
        "selectors": {
          "id": "#apply-btn",
          "name": "[name='submit']",
          "aria_label": "[aria-label='Submit application']"
        }
      }
    ],

    "inputs": [
      {
        "label": "Email Address",
        "placeholder": "you@example.com",
        "type": "email",
        "name": "email",
        "id": "email-input",
        "value": "",
        "purpose": "email",            ← SEMANTIC PURPOSE!
        "required": true,
        "disabled": false,
        "readonly": false,
        "autocomplete": "email",
        "pattern": "[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$",
        "min": "",
        "max": "",
        "minlength": "",
        "maxlength": "100",
        "aria_label": "Enter your email address",
        "aria_required": "true",
        "data_attrs": {
          "data-validate": "email",   ← VALIDATION RULES!
          "data-required": "true"
        },
        "selectors": {
          "id": "#email-input",
          "name": "[name='email']"
        }
      }
    ],

    "selects": [
      {
        "label": "Work Authorization",
        "name": "work_auth",
        "id": "work-auth-select",
        "purpose": "work-authorization", ← PURPOSE DETECTED!
        "required": true,
        "disabled": false,
        "multiple": false,
        "options": [
          {"value": "citizen", "text": "US Citizen", "selected": false},
          {"value": "green_card", "text": "Green Card Holder", "selected": false},
          {"value": "h1b", "text": "H1-B Visa", "selected": false},
          {"value": "f1", "text": "F1 Student", "selected": false},
          {"value": "other", "text": "Other", "selected": false}
        ],
        "option_count": 5,
        "aria_label": "Select work authorization status",
        "data_attrs": {},
        "selectors": {
          "id": "#work-auth-select",
          "name": "[name='work_auth']"
        }
      }
    ],

    "links": [...],
    "textareas": [...],
    "checkboxes": [...],
    "radios": [...],
    "file_uploads": [
      {
        "label": "Resume / CV",
        "name": "resume",
        "id": "resume-upload",
        "accept": ".pdf,.doc,.docx",
        "multiple": false,
        "required": true,
        "purpose": "resume",           ← KNOWS IT'S RESUME!
        "aria_label": "Upload your resume",
        "selectors": {
          "id": "#resume-upload",
          "name": "[name='resume']"
        }
      }
    ]
  },

  "hidden_data": {
    "hidden_fields": [
      {
        "name": "__RequestVerificationToken",
        "value": "abc123def456...",
        "id": ""
      }
    ],
    "csrf_tokens": [
      {
        "name": "__RequestVerificationToken",
        "value": "abc123def456..."
      }
    ],
    "local_storage": {
      "token": "xyz789...",
      "user_id": "12345"
    },
    "session_storage": {},
    "cookies": [
      {
        "name": "session_id",
        "value": "...",
        "domain": ".ultipro.com"
      }
    ],
    "data_attributes": [
      {
        "tag": "div",
        "id": "job-container",
        "data": {
          "data-job-id": "12345",
          "data-company": "HomeServe",
          "data-location": "Chattanooga, TN"
        }
      }
    ]
  },

  "page_state": {
    "platform": "ultipro",           ← JOB BOARD DETECTED!
    "page_type": "form",             ← PAGE TYPE!
    "has_forms": true,
    "form_count": 1,
    "required_fields": [
      {
        "tag": "input",
        "type": "email",
        "name": "email",
        "label": "Email Address"
      },
      {
        "tag": "input",
        "type": "file",
        "name": "resume",
        "label": "Resume / CV"
      }
    ],
    "validation_rules": [
      {
        "name": "email",
        "required": true,
        "pattern": "[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$",
        "min": "",
        "max": "",
        "minlength": "",
        "maxlength": "100"
      }
    ],
    "frameworks": {
      "react": false,
      "vue": false,
      "angular": false
    }
  },

  "content": {
    "page_text": "AI / ML Engineer | HomeServe... [full text]",
    "headings": [
      {"level": "h1", "text": "AI / ML Engineer"},
      {"level": "h2", "text": "Job Details"},
      {"level": "h3", "text": "Description"}
    ],
    "semantic_structure": {
      "header": 1,
      "nav": 1,
      "main": 1,
      "article": 0,
      "section": 3,
      "aside": 0,
      "footer": 1
    },
    "meta_tags": [...],
    "title": "AI / ML Engineer | HomeServe"
  },

  "javascript": {
    "window_data": {
      "location": {
        "href": "https://...",
        "pathname": "/OpportunityDetail",
        "search": "?opportunityId=..."
      },
      "innerWidth": 1280,
      "innerHeight": 720
    },
    "global_vars": {
      "appConfig": {...},
      "jobData": {...}
    }
  },

  "api_hints": {
    "endpoints": [
      "/api/v1/applications",
      "/api/v1/upload"
    ],
    "graphql_detected": false
  },

  "stats": {
    "total_elements": 42,
    "buttons": 4,
    "inputs": 8,
    "selects": 3,
    "links": 15,
    "textareas": 2,
    "checkboxes": 5,
    "radios": 3,
    "file_uploads": 2,
    "hidden_fields": 5,
    "required_fields": 12,
    "platform": "ultipro",
    "page_type": "form"
  }
}
```

---

## What Makes This COMPLETE?

### ✅ Everything in One Call
- Single method: `extract_complete_page(page, html)`
- Returns one structured JSON object
- No need to call multiple extractors

### ✅ Rich Context for Every Element
- **Purpose Detection**: Knows if button is "apply", "cancel", "next", etc.
- **Semantic Understanding**: Knows if input wants "email", "password", "name", etc.
- **Multiple Selectors**: Provides ID, name, aria-label selectors
- **Data Attributes**: Exposes all data-* attributes
- **Validation Rules**: Pattern, min/max, required, etc.

### ✅ Page Intelligence
- **Platform Detection**: Greenhouse, Lever, Workday, etc.
- **Page Type**: login, signup, form, confirmation
- **Framework Detection**: React, Vue, Angular
- **Required Fields**: Lists all required inputs
- **File Uploads**: With purpose detection (resume, cover letter)

### ✅ Hidden Data Exposed
- CSRF tokens
- Hidden fields
- localStorage / sessionStorage
- Cookies
- Data attributes

### ✅ AI-Ready Format
- Structured JSON (not text blobs!)
- Semantic purposes (not just tags)
- Multiple selectors (choose best one)
- Validation rules (know constraints)
- **OpenAI can make PERFECT decisions!**

---

## Usage:

```python
from apply.extractors import CompleteUniversalExtractor

extractor = CompleteUniversalExtractor(logger)
complete_data = extractor.extract_complete_page(page, html)

# Access structured data:
buttons = complete_data['interactive_elements']['buttons']
inputs = complete_data['interactive_elements']['inputs']
required = complete_data['page_state']['required_fields']
platform = complete_data['page_state']['platform']
```

---

## Result:

🎯 **ONE EXTRACTION → COMPLETE PAGE STATE → BETTER AI DECISIONS!**

No hardcoding. No guessing. Pure extraction intelligence.
