# Architecture Documentation

## Overview

This tool uses a **goal-driven state machine** architecture with intelligent extraction and semantic understanding to automate job applications without hardcoded selectors.

## Core Components

### 1. Configuration Management (`config.py`)

**Purpose**: Load and validate configuration, handle credentials securely.

**Key Features**:
- YAML-based configuration
- Environment variable support for secrets
- Password masking in logs
- Validation of required fields

**Security**:
- Never stores passwords in memory longer than necessary
- Masks sensitive data in all logs
- Supports keyring/environment variables

### 2. Browser Management (`browser.py`)

**Purpose**: Manage Playwright browser lifecycle and navigation.

**Key Features**:
- Browser launch with configurable options
- Network response interception
- Navigation and wait utilities
- Lazy loading through scrolling

**Network Interception**:
- Captures all JSON responses (REST/GraphQL)
- Associates responses with page URLs
- Logs structured data for analysis

### 3. Extraction System (`extractors/`)

#### A. Network Extractor (`network.py`)

Analyzes captured network responses:
- Identifies job-related data
- Detects user/profile information
- Finds form schemas
- Extracts application status

#### B. DOM Extractor (`dom.py`)

Builds structured inventory of page elements:
- **Inputs**: All attributes, label text, context, semantic purpose
- **Buttons**: Text, ARIA labels, disabled state, purpose
- **Links**: href, text, accessibility info
- **Forms**: Action, method, structure

**Purpose Detection**:
```python
# Example: Email input detection
1. Check autocomplete="email"
2. Check type="email"
3. Check label contains "email"
4. Check placeholder contains "email"
5. Check name/id contains "email"
```

#### C. Text Extractor (`text.py`)

Analyzes visible text content:
- Extracts clean visible text
- Detects key phrases (success, error, CAPTCHA)
- Determines page state from content
- Identifies application progress indicators

### 4. State Machine (`planner.py`)

**Purpose**: Track application state and plan actions toward goal.

#### States

```
INITIAL → JOB_LISTING → SIGN_IN → FORM_FILL → REVIEW → SUBMIT → CONFIRMATION
                ↓            ↓         ↓          ↓        ↓
              CAPTCHA     BLOCKED   CAPTCHA   BLOCKED  SUCCESS
```

#### State Detection

Combines multiple signals:
1. **Text analysis**: Key phrases, page content
2. **DOM analysis**: Input types, button purposes
3. **URL patterns**: /apply, /jobs, /confirmation
4. **Network responses**: Application status

#### Action Planning

Each state has a dedicated planner:
- **JOB_LISTING**: Find and click "Apply" button
- **SIGN_IN**: Fill credentials, click sign-in
- **FORM_FILL**: Map inputs to profile, fill and continue
- **REVIEW**: Click submit button
- **CONFIRMATION**: Return success

### 5. Action Execution (`actor.py`)

**Purpose**: Execute planned actions using semantic selectors.

#### Strategies

Every action tries multiple strategies:

**Click Button**:
1. By button role + text (exact)
2. By text content (partial)
3. By ARIA label
4. By visual text matching

**Fill Input**:
1. By label text
2. By placeholder text
3. By name attribute
4. By ID

**Upload File**:
1. By label
2. By name
3. Any file input

### 6. Detection System (`detect.py`)

**Purpose**: Detect special conditions and blocking issues.

#### CAPTCHA Detection

Multiple indicators:
- Common CAPTCHA iframes (reCAPTCHA, hCaptcha)
- Cloudflare challenge pages
- Text-based indicators
- Bot detection services

#### Success Detection

Looks for:
- Confirmation page states
- Success text phrases
- URL patterns (/success, /confirmation)
- Network response status

#### Blocking Issue Detection

Detects:
- Error messages
- Session expiration
- Access denied
- Validation failures

### 7. Logging System (`logger.py`)

**Purpose**: Comprehensive logging and artifact saving.

**Artifacts**:
- `actions.log`: Detailed action log
- `network.jsonl`: JSON responses per request
- `page_*.html`: HTML snapshots
- `elements_*.json`: Element inventories
- `final_status.json`: Run result

**Security**: All logs are masked for sensitive data.

## Data Flow

```
1. Navigate to URL
   ↓
2. Wait for page load + network idle
   ↓
3. Scroll to trigger lazy loading
   ↓
4. EXTRACT:
   - Capture network responses
   - Parse DOM for elements
   - Extract visible text
   ↓
5. DETECT:
   - Check for CAPTCHA → pause if found
   - Check for success → end if confirmed
   - Check for errors → fail if blocked
   ↓
6. PLAN:
   - Determine current state
   - Map state to actions
   - Select next actions
   ↓
7. ACT:
   - Fill inputs
   - Upload files
   - Click buttons
   - Navigate
   ↓
8. LOOP: Go to step 2 until:
   - Success detected
   - Blocked/failed
   - Max iterations reached
```

## Semantic Understanding

### How the Tool "Understands" Elements

#### Input Purpose Detection

```python
# Priority order:
1. autocomplete attribute (most reliable)
2. type attribute (email, tel, password)
3. name attribute (firstName, last-name)
4. label text (visible association)
5. placeholder text (hint to user)
6. ARIA labels (accessibility)
7. context text (surrounding content)
```

#### Button Purpose Detection

```python
# Keyword matching:
- "submit", "send" → SUBMIT
- "apply now" → APPLY
- "next", "continue" → NEXT
- "sign in", "log in" → SIGNIN
- "review" → REVIEW
```

### Why No Hardcoded Selectors?

Traditional approach:
```python
# BAD: Site-specific, breaks easily
driver.find_element_by_class("job-apply-button-2024-v3")
```

This tool's approach:
```python
# GOOD: Semantic, works across sites
page.get_by_role('button', name=re.compile('apply', re.I))
```

**Benefits**:
- Works on any site structure
- Resilient to redesigns
- Respects accessibility standards
- Future-proof

## State Machine Details

### State Transitions

```
Initial Page
  ├─ Has "Apply" button → JOB_LISTING
  ├─ Has email+password → SIGN_IN
  └─ Has form inputs → FORM_FILL

Sign In
  ├─ Successful → Next state (usually FORM_FILL)
  └─ Failed → BLOCKED

Form Fill
  ├─ Has "Next" button → Stay in FORM_FILL (multi-step)
  ├─ Has "Submit" button → REVIEW (if no inputs)
  └─ Has "Submit" button → Can submit from FORM_FILL

Review
  └─ Click submit → CONFIRMATION or BLOCKED

Confirmation
  └─ SUCCESS (terminal state)

CAPTCHA (can occur anywhere)
  └─ Wait for human → Resume previous state

BLOCKED (can occur anywhere)
  └─ FAILED (terminal state)
```

### Decision Logic

```python
def determine_next_state(current_state, page_data):
    # Check terminal conditions first
    if detected_success(page_data):
        return CONFIRMATION

    if detected_captcha(page_data):
        return CAPTCHA

    if detected_error(page_data):
        return BLOCKED

    # Check page type
    if has_signin_form(page_data):
        return SIGN_IN

    if has_application_form(page_data):
        return FORM_FILL

    # Transition based on current state
    return next_logical_state(current_state, page_data)
```

## Error Handling

### Retry Strategy

- **Navigation failures**: Retry once
- **Element not found**: Try multiple strategies, then warn and continue
- **Action failures**: Log and proceed (non-critical)
- **CAPTCHA**: Pause for human
- **Critical errors**: Fail and log

### Graceful Degradation

If a field can't be filled:
1. Try all strategies
2. Log warning
3. Continue with next field
4. Don't fail entire run

Reasoning: Better to submit incomplete than to fail completely.

## Extension Points

### Adding New States

1. Add to `State` enum in `planner.py`
2. Implement `_plan_<state>()`
3. Add detection logic in `_determine_state()`

### Adding New Field Types

1. Add detection in `dom.py` → `_detect_input_purpose()`
2. Add mapping in `planner.py` → `_plan_form_fill()`
3. Add profile field in `config.example.yaml`

### Adding New Extractors

1. Create new file in `extractors/`
2. Implement `extract()` method
3. Add to `__init__.py`
4. Use in main loop

## Performance Considerations

### Network Efficiency

- Only capture JSON responses (filter by content-type)
- Limit HTML snapshots to key iterations
- Clear network buffer between pages

### Memory Management

- Process pages iteratively
- Don't accumulate full history
- Clear browser cache periodically

### Speed vs Reliability

Current settings favor reliability:
- Wait for network idle
- Add delays after actions
- Scroll to trigger lazy loading

For faster runs (less reliable):
```yaml
automation:
  action_delay: 0
  max_scroll_attempts: 3
browser:
  slow_mo: 0
```

## Security Considerations

### Credentials

- Never in code
- Never in logs (masked)
- Only from env vars or secure prompt
- Cleared from memory after use

### Data Privacy

- All artifacts saved locally
- No external API calls (no OpenAI, no tracking)
- User controls all data

### Bot Detection

- Respects CAPTCHA
- Adds human-like delays
- Uses real browser (not headless-only)
- Doesn't bypass security

## Testing Strategy

### Manual Testing

1. Test on known public job boards
2. Verify each state transition
3. Check artifact output
4. Validate form filling

### Automated Testing

Potential additions:
- Mock Playwright responses
- Test extraction logic with fixtures
- Validate state transitions
- Test configuration loading

## Future Enhancements

Possible improvements:
- Machine learning for better field detection
- Screenshot-based verification
- Multi-language support
- Resume parsing and matching
- Application tracking dashboard
- Browser extension mode

## Dependencies Rationale

- **Playwright**: Modern browser automation, better than Selenium for SPAs
- **BeautifulSoup**: Fast HTML parsing, simple API
- **PyYAML**: Human-readable config format
- **python-dotenv**: Standard env var loading
- **lxml**: Fast XML/HTML parsing backend

## Conclusion

This architecture prioritizes:
1. **Robustness**: Works across different sites
2. **Security**: No credential leaks
3. **Transparency**: Full logging and artifacts
4. **Ethics**: Respects CAPTCHAs and security

The goal-driven state machine ensures the tool always works toward application submission while handling various page structures and flows.
