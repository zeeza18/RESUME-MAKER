"""Self-healing retry logic for application automation."""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field


@dataclass
class HealingAttempt:
    """Record of a healing attempt."""
    attempt_number: int
    action_type: str
    original_code: str
    error: str
    healed_code: Optional[str] = None
    success: bool = False


@dataclass
class ApplicationState:
    """Current state of the application process."""
    job_id: str
    current_url: str = ""
    current_step: int = 0
    page_type: str = "unknown"
    attempts: int = 0
    max_attempts: int = 5
    errors: list = field(default_factory=list)
    healing_history: list = field(default_factory=list)
    completed: bool = False
    success: bool = False
    # Pipeline phase tracking
    phase: str = "init"
    job_description: str = ""
    job_title: str = ""
    tailored_score: int = 0
    pdf_path: str = ""


class SelfHealer:
    """Manages retry logic and code healing for failed automation attempts."""

    def __init__(
        self,
        browser_engine,
        vision_analyzer,
        code_generator,
        max_attempts: int = 5
    ):
        self.browser = browser_engine
        self.vision = vision_analyzer
        self.code_gen = code_generator
        self.max_attempts = max_attempts

    async def execute_with_healing(
        self,
        state: ApplicationState,
        action_type: str,
        initial_code: str,
        on_progress: Optional[Callable[[str], None]] = None,
        form_filler=None,
    ) -> Tuple[bool, str]:
        """
        Execute code with automatic healing on failure.

        Returns:
            Tuple of (success, final_code_or_error)
        """
        current_code = initial_code
        last_error = ""

        for attempt in range(1, self.max_attempts + 1):
            state.attempts = attempt

            if on_progress:
                on_progress(f"Attempt {attempt}/{self.max_attempts}: {action_type}")

            # Take screenshot before action
            before_screenshot = await self.browser.take_screenshot(f"before_{attempt}")

            # Try to execute the code
            success, error = await self.browser.execute_code(current_code)

            healing_attempt = HealingAttempt(
                attempt_number=attempt,
                action_type=action_type,
                original_code=current_code,
                error=error if not success else "",
                success=success
            )

            if success:
                # Take screenshot after to verify
                after_screenshot = await self.browser.take_screenshot(f"after_{attempt}")

                # Compare screenshots to verify action worked
                comparison = self.vision.compare_screenshots(before_screenshot, after_screenshot)

                if comparison.get('action_successful', True) or comparison.get('progress_made', False):
                    state.healing_history.append(healing_attempt)
                    return True, current_code
                else:
                    # Action executed but didn't achieve goal
                    error = f"Action executed but no progress detected: {comparison.get('summary', 'Unknown')}"
                    healing_attempt.success = False
                    healing_attempt.error = error

            state.errors.append(error)
            last_error = error

            if attempt < self.max_attempts:
                if on_progress:
                    on_progress(f"Attempt {attempt} failed, generating healed code...")

                # Take fresh screenshot for analysis
                current_screenshot = await self.browser.take_screenshot(f"heal_{attempt}")
                page_analysis = self.vision.analyze_screenshot(current_screenshot)

                # Generate healed code based on error + full context
                healed_code = self._generate_healed_code(
                    action_type,
                    page_analysis,
                    current_code,
                    error,
                    form_filler=form_filler,
                )

                healing_attempt.healed_code = healed_code
                current_code = healed_code

            state.healing_history.append(healing_attempt)

            # Small delay before retry
            await asyncio.sleep(1)

        return False, f"Max attempts ({self.max_attempts}) reached. Last error: {last_error}"

    def _generate_healed_code(
        self,
        action_type: str,
        page_analysis: Dict[str, Any],
        failed_code: str,
        error: str,
        form_filler=None,
    ) -> str:
        """Generate healed code based on failure analysis."""

        prev = f"Previous code:\n{failed_code}\n\nError:\n{error}"

        if action_type == "login":
            return self.code_gen.generate_login_code(
                page_analysis,
                "mohammedazeezulla6996@gmail.com",
                self.browser.generate_password(page_analysis.get('company', 'unknown')),
                previous_error=prev,
            )
        elif action_type == "fill_form":
            form_data = {}
            resume_text = ""
            if form_filler:
                detected = page_analysis.get('detected_fields_purpose', {})
                form_data = form_filler.prepare_form_data(detected)
                resume_pdf = form_filler.get_resume_pdf_path()
                if resume_pdf:
                    form_data['resume_path'] = str(resume_pdf)
                resume_text = form_filler.load_resume()
            return self.code_gen.generate_form_code(
                page_analysis, form_data,
                previous_error=prev,
                resume_text=resume_text,
            )
        else:
            return self.code_gen.generate_navigation_code(
                page_analysis, action_type, previous_error=prev,
            )

    async def run_full_application(
        self,
        job_url: str,
        job_id: str,
        company: str,
        form_filler,
        on_progress: Optional[Callable[[str], None]] = None,
        on_detailed_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ApplicationState:
        """
        Run the full auto-apply pipeline:
        Phase A: JD Extraction
        Phase B: Tailoring (3 rounds)
        Phase C: PDF Compilation
        Phase D: Form Filling (self-healing loop)
        """
        state = ApplicationState(job_id=job_id, current_url=job_url)

        def _emit(event_data: Dict[str, Any]) -> None:
            """Send structured progress event."""
            if on_detailed_progress:
                on_detailed_progress(event_data)
            if on_progress and "message" in event_data:
                on_progress(event_data["message"])

        try:
            # ── Initialize browser ──
            state.phase = "init"
            _emit({"event": "progress", "phase": "init", "message": "Initializing browser..."})
            await self.browser.initialize(headless=False)

            _emit({"event": "progress", "phase": "init", "message": f"Navigating to {job_url}..."})
            await self.browser.navigate(job_url)
            state.current_url = job_url

            # ══════════════════════════════════════
            # Phase A: JD Extraction
            # ══════════════════════════════════════
            state.phase = "jd_extraction"
            _emit({"event": "phase", "phase": "jd_extraction", "message": "Extracting job description..."})

            screenshot = await self.browser.take_screenshot("jd_page")
            page_text = await self.browser.get_page_text()

            jd_result = self.vision.extract_job_description(screenshot, page_text)
            jd_text = jd_result.get("job_description", "")
            state.job_title = jd_result.get("job_title", "Unknown")
            confidence = jd_result.get("confidence", 0)

            # Fallback: use raw page text if vision extraction is weak
            if not jd_text or len(jd_text.split()) < 50:
                if page_text and len(page_text.split()) >= 50:
                    jd_text = page_text[:5000]
                    _emit({"event": "progress", "phase": "jd_extraction",
                           "message": "Vision extraction weak, falling back to page text"})
                else:
                    _emit({"event": "error", "phase": "jd_extraction",
                           "message": "Could not extract job description (page text too short)"})
                    state.errors.append("JD extraction failed: insufficient text on page")
                    state.phase = "failed"
                    return state

            state.job_description = jd_text
            _emit({
                "event": "jd_extracted",
                "phase": "jd_extraction",
                "job_description": jd_text[:500],
                "job_title": state.job_title,
                "company": jd_result.get("company", company),
                "confidence": confidence,
                "message": f"Extracted JD: {state.job_title} ({len(jd_text.split())} words, confidence {confidence}%)",
            })

            # ══════════════════════════════════════
            # Phase B: Resume Tailoring
            # ══════════════════════════════════════
            state.phase = "tailoring"
            _emit({"event": "phase", "phase": "tailoring", "message": "Starting resume tailoring..."})

            # Load resume
            resume_text = form_filler.load_resume()
            if not resume_text or len(resume_text.split()) < 30:
                _emit({"event": "error", "phase": "tailoring",
                       "message": "Resume file is empty or too short. Continuing with original resume."})
                # Continue without tailoring
            else:
                try:
                    import anyio
                    # Add project root to path for imports
                    project_root = Path(__file__).resolve().parents[2]
                    scripts_dir = project_root / "scripts"
                    for p in (str(project_root), str(scripts_dir)):
                        if p not in sys.path:
                            sys.path.insert(0, p)

                    from resume_crew import ResumeCrew
                    crew = ResumeCrew()

                    def _tailoring_progress(evt: Dict[str, Any]) -> None:
                        """Forward tailoring events to the pipeline stream."""
                        if evt.get("event") == "round_complete":
                            round_num = evt.get("round", 0)
                            score = evt.get("evaluation", {}).get("score", 0)
                            try:
                                score = int(float(score))
                            except (TypeError, ValueError):
                                score = 0
                            state.tailored_score = score
                            _emit({
                                "event": "tailoring_round_complete",
                                "phase": "tailoring",
                                "round": round_num,
                                "score": score,
                                "message": f"Tailoring round {round_num}/3 complete - score: {score}/100",
                            })
                        elif evt.get("event") == "keywords_extracted":
                            _emit({
                                "event": "progress",
                                "phase": "tailoring",
                                "message": "Keywords extracted, starting tailoring rounds...",
                            })

                    result = await anyio.to_thread.run_sync(
                        lambda: crew.run_tailoring_process(
                            jd_text,
                            resume_text,
                            progress_callback=_tailoring_progress,
                        )
                    )

                    final_resume = result.get("final_resume", resume_text)
                    final_score = result.get("final_score", 0)
                    try:
                        final_score = int(float(final_score))
                    except (TypeError, ValueError):
                        final_score = 0
                    state.tailored_score = final_score

                    _emit({
                        "event": "tailoring_complete",
                        "phase": "tailoring",
                        "score": final_score,
                        "message": f"Tailoring complete! Final score: {final_score}/100",
                    })

                    # Update form filler with tailored resume
                    form_filler.set_tailored_resume(final_resume)

                except Exception as exc:
                    _emit({
                        "event": "progress",
                        "phase": "tailoring",
                        "message": f"Tailoring failed ({exc}), continuing with original resume",
                    })
                    state.errors.append(f"Tailoring failed: {exc}")

            # ══════════════════════════════════════
            # Phase C: PDF Compilation
            # ══════════════════════════════════════
            state.phase = "pdf_compilation"
            _emit({"event": "phase", "phase": "pdf_compilation", "message": "Compiling PDF..."})

            try:
                from apply.pdf_compiler import compile_latex_to_pdf

                project_root = Path(__file__).resolve().parents[2]
                tex_file = project_root / "docs" / "latex" / "main.tex"

                if tex_file.exists():
                    success, pdf_path, error_msg = compile_latex_to_pdf(tex_file)
                    if success:
                        state.pdf_path = str(pdf_path)
                        form_filler.set_tailored_resume(
                            form_filler._tailored_resume_text or form_filler.load_resume(),
                            pdf_path,
                        )
                        _emit({
                            "event": "pdf_compiled",
                            "phase": "pdf_compilation",
                            "pdf_path": str(pdf_path),
                            "message": "PDF compiled successfully",
                        })
                    else:
                        _emit({
                            "event": "progress",
                            "phase": "pdf_compilation",
                            "message": f"PDF compilation failed: {error_msg}. Using existing PDF if available.",
                        })
                        state.errors.append(f"PDF compile: {error_msg}")
                else:
                    _emit({
                        "event": "progress",
                        "phase": "pdf_compilation",
                        "message": "No LaTeX source found, skipping PDF compilation",
                    })
            except Exception as exc:
                _emit({
                    "event": "progress",
                    "phase": "pdf_compilation",
                    "message": f"PDF compilation error: {exc}",
                })
                state.errors.append(f"PDF compile: {exc}")

            # ══════════════════════════════════════
            # Phase D: Form Filling (self-healing)
            # ══════════════════════════════════════
            state.phase = "form_filling"
            _emit({"event": "phase", "phase": "form_filling", "message": "Starting form filling..."})

            max_steps = 20
            step = 0

            while step < max_steps and not state.completed:
                step += 1
                state.current_step = step

                _emit({"event": "progress", "phase": "form_filling",
                       "message": f"Step {step}: Analyzing page..."})

                screenshot = await self.browser.take_screenshot(f"step_{step}")
                # Get DOM content for fallback analysis
                page_content = await self.browser.get_page_content()
                analysis = self.vision.analyze_screenshot(screenshot, page_content=page_content)
                state.page_type = analysis.get('page_type', 'unknown')

                _emit({"event": "progress", "phase": "form_filling",
                       "message": f"Step {step}: Page type: {state.page_type}"})

                next_action = self.vision.detect_next_action(screenshot, page_content=page_content)
                action_type = next_action.get('action_type', 'error')

                if action_type == 'complete':
                    state.completed = True
                    state.success = True
                    break
                elif action_type == 'error':
                    state.errors.append(next_action.get('reasoning', 'Unknown error'))
                    if step >= 3:
                        break
                    continue
                elif action_type == 'login':
                    login_code = self.code_gen.generate_login_code(
                        analysis,
                        self.browser.email,
                        self.browser.generate_password(company)
                    )
                    success, result = await self.execute_with_healing(
                        state, 'login', login_code, on_progress,
                        form_filler=form_filler,
                    )
                    if not success:
                        state.errors.append(f"Login failed: {result}")
                        break
                elif action_type == 'fill_form':
                    detected_purposes = analysis.get('detected_fields_purpose', {})
                    form_data = form_filler.prepare_form_data(detected_purposes)

                    resume_pdf = form_filler.get_resume_pdf_path()
                    if resume_pdf:
                        form_data['resume_path'] = str(resume_pdf)

                    form_code = self.code_gen.generate_form_code(
                        analysis, form_data,
                        resume_text=form_filler.load_resume(),
                    )
                    success, result = await self.execute_with_healing(
                        state, 'fill_form', form_code, on_progress,
                        form_filler=form_filler,
                    )
                    if not success:
                        state.errors.append(f"Form fill failed: {result}")
                elif action_type == 'click_button':
                    target = next_action.get('css_selector_suggestion', '')
                    nav_code = self.code_gen.generate_navigation_code(
                        analysis,
                        f"Click button: {next_action.get('target_element', target)}"
                    )
                    success, result = await self.execute_with_healing(
                        state, 'click', nav_code, on_progress,
                        form_filler=form_filler,
                    )
                elif action_type == 'upload_file':
                    resume_pdf = form_filler.get_resume_pdf_path()
                    if resume_pdf:
                        nav_code = self.code_gen.generate_navigation_code(
                            analysis,
                            f"Upload resume file from {resume_pdf}"
                        )
                        success, result = await self.execute_with_healing(
                            state, 'upload', nav_code, on_progress,
                            form_filler=form_filler,
                        )
                elif action_type == 'wait':
                    await asyncio.sleep(2)

                state.current_url = self.browser.get_current_url() or job_url

        except Exception as e:
            state.errors.append(f"Unexpected error: {str(e)}")
            _emit({"event": "error", "phase": state.phase,
                   "message": f"Unexpected error: {e}"})
        finally:
            await self.browser.close()

        return state
