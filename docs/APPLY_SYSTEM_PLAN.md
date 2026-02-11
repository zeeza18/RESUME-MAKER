# Job Application Automation System - Implementation Plan

## Overview
Build an automated job application system with Playwright, Gemini vision analysis, and Claude code generation.

---

## Features to Build

### 1. Frontend Updates
- [ ] Add "APPLY" section with job link input
- [ ] Add "ATS CHECK" button/section
- [ ] Add "Download PDF" button (runs pdflatex)
- [ ] Job links management UI (add/view/delete)

### 2. Job Storage System
- [ ] Local JSON storage for job links
- [ ] Fields: url, company, status, date_added, date_applied

### 3. Playwright Automation
- [ ] Browser automation setup
- [ ] Dynamic login system:
  - Email: mohammedazeezulla6996@gmail.com
  - Password: Zeeza_{first 3 letters}@6996
- [ ] Screenshot capture (full page)
- [ ] Form detection and filling

### 4. AI-Powered Form Analysis
- [ ] Gemini API for screenshot/layout analysis
- [ ] Claude API for Playwright code generation
- [ ] Self-healing: retry with new code on failure

### 5. Form Data Management
- [ ] script.txt for common Q&A
- [ ] Resume-based field filling
- [ ] Claude for unknown questions

---

## Architecture

```
Frontend (React)
    ↓
FastAPI Backend
    ↓
┌─────────────────────────────────────┐
│  Application Engine                  │
│  ├── JobStorage (JSON)              │
│  ├── PlaywrightRunner               │
│  ├── GeminiVision (layout analysis) │
│  ├── ClaudeCodeGen (form filling)   │
│  └── SelfHealer (retry logic)       │
└─────────────────────────────────────┘
```

---

## File Structure

```
scripts/
├── apply/
│   ├── __init__.py
│   ├── job_storage.py      # JSON storage for jobs
│   ├── browser_engine.py   # Playwright automation
│   ├── vision_analyzer.py  # Gemini screenshot analysis
│   ├── code_generator.py   # Claude code generation
│   ├── form_filler.py      # Form filling logic
│   └── self_healer.py      # Retry/healing logic
├── data/
│   ├── jobs.json           # Stored job links
│   └── script.txt          # Common Q&A answers
```

---

## Password Generation Logic

```python
def generate_password(company_name: str) -> str:
    prefix = company_name.lower()[:3]
    return f"Zeeza_{prefix}@6996"

# Examples:
# Amazon → Zeeza_ama@6996
# GE Health → Zeeza_geh@6996
# Google → Zeeza_goo@6996
# Microsoft → Zeeza_mic@6996
```

---

## AI Integration Flow

1. **Screenshot** → Playwright captures full page
2. **Analyze** → Gemini identifies form fields, buttons, layout
3. **Generate** → Claude creates Playwright code to fill/click
4. **Execute** → Run generated code
5. **Heal** → If fails, send error to Claude, regenerate code
6. **Repeat** → Until application submitted or max retries

---

## API Endpoints

```
POST /api/jobs              # Add job link
GET  /api/jobs              # List all jobs
DELETE /api/jobs/{id}       # Remove job

POST /api/apply             # Start application
POST /api/apply/screenshot  # Capture current state
POST /api/apply/analyze     # Gemini analysis
POST /api/apply/generate    # Claude code gen
POST /api/apply/execute     # Run code

GET  /api/pdf/download      # Generate & download PDF
POST /api/ats/check         # Run ATS check
```
