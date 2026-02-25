"""FastAPI server exposing the resume tools for frontend and integrations."""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"

for path in (BASE_DIR, SCRIPTS_DIR):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

import anyio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from resume_crew import ResumeCrew
from tools.tool1 import KeywordExtractor
from tools.tool2 import ResumeTailor
from tools.tool3 import ResumeEvaluator
from apply.job_storage import JobStorage
from apply.browser_engine import BrowserEngine
from apply.vision_analyzer import VisionAnalyzer
from apply.code_generator import CodeGenerator
from apply.form_filler import FormFiller
from apply.self_healer import SelfHealer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize job storage
job_storage = JobStorage()

app = FastAPI(title="Resume Crew API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


def _word_count(value: str) -> int:
    return len([token for token in value.strip().split() if token])


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., alias="jobDescription")

    @validator("job_description")
    def validate_length(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Job description must be at least 50 words.")
        return value

    class Config:
        populate_by_name = True
        extra = "forbid"


class TailorRequest(JobDescriptionRequest):
    current_resume: str = Field(..., alias="currentResume")

    @validator("current_resume")
    def validate_resume(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Current resume must be at least 50 words.")
        return value

    class Config(JobDescriptionRequest.Config):
        pass


class TailorStepRequest(BaseModel):
    original_resume: str = Field(..., alias="originalResume")
    job_description: str = Field(..., alias="jobDescription")
    keywords: Dict[str, Any]
    feedback: Optional[str] = None

    @validator("original_resume")
    def validate_original(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Resume must be at least 50 words.")
        return value

    @validator("job_description")
    def validate_jd(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Job description must be at least 50 words.")
        return value

    class Config:
        populate_by_name = True
        extra = "forbid"


class EvaluateRequest(JobDescriptionRequest):
    tailored_resume: str = Field(..., alias="tailoredResume")
    keywords: Dict[str, Any]

    @validator("tailored_resume")
    def validate_tailored(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Tailored resume must be at least 50 words.")
        return value

    class Config(JobDescriptionRequest.Config):
        pass


@app.get("/api/health")
async def healthcheck() -> Dict[str, str]:
    """Simple health endpoint for monitoring."""
    return {"status": "ok"}


@app.post("/api/keywords")
async def extract_keywords(payload: JobDescriptionRequest) -> Dict[str, Any]:
    """Run Tool 1 (Keyword Extractor)."""
    extractor = KeywordExtractor()

    try:
        result = await anyio.to_thread.run_sync(
            extractor.extract_keywords,
            payload.job_description,
        )
        return result
    except Exception as exc:
        logger.exception("Keyword extraction failed")
        raise HTTPException(status_code=500, detail=f"Keyword extraction failed: {exc}") from exc


@app.post("/api/tailor-step")
async def tailor_step(payload: TailorStepRequest) -> Dict[str, Any]:
    """Run Tool 2 (Resume Tailor) directly."""
    tailor = ResumeTailor()

    try:
        result = await anyio.to_thread.run_sync(
            tailor.tailor_resume,
            payload.original_resume,
            payload.keywords,
            payload.job_description,
            payload.feedback,
        )
        return result
    except Exception as exc:
        logger.exception("Resume tailoring step failed")
        raise HTTPException(status_code=500, detail=f"Tailoring step failed: {exc}") from exc


@app.post("/api/evaluate")
async def evaluate_resume(payload: EvaluateRequest) -> Dict[str, Any]:
    """Run Tool 3 (Resume Evaluator) directly."""
    evaluator = ResumeEvaluator()

    try:
        result = await anyio.to_thread.run_sync(
            evaluator.evaluate_resume,
            payload.job_description,
            payload.tailored_resume,
            payload.keywords,
        )
        return result
    except Exception as exc:
        logger.exception("Resume evaluation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/tailor")
async def run_full_process(payload: TailorRequest) -> StreamingResponse:
    """Run the complete three-tool crew pipeline with incremental updates."""
    crew = ResumeCrew()
    send_stream, receive_stream = anyio.create_memory_object_stream(20)

    def progress_callback(event: Dict[str, Any]) -> None:
        try:
            anyio.from_thread.run(send_stream.send, event)
        except RuntimeError:
            logger.debug("Progress stream closed; dropping event: %s", event.get("event"))

    def run_process() -> None:
        try:
            result = crew.run_tailoring_process(
                payload.job_description,
                payload.current_resume,
                progress_callback=progress_callback,
            )
            anyio.from_thread.run(
                send_stream.send,
                {"event": "complete", "payload": result},
            )
        except ValueError as exc:
            logger.warning("Input validation error during processing: %s", exc)
            anyio.from_thread.run(
                send_stream.send,
                {"event": "error", "message": str(exc)},
            )
        except Exception as exc:
            logger.exception("Full tailoring process failed")
            anyio.from_thread.run(
                send_stream.send,
                {"event": "error", "message": f"Tailoring process failed: {exc}"},
            )
        finally:
            with contextlib.suppress(RuntimeError):
                anyio.from_thread.run(send_stream.aclose)

    async def start_processing() -> None:
        await anyio.to_thread.run_sync(run_process)

    async def event_stream():
        processing_task = asyncio.create_task(start_processing())
        try:
            yield b"\n"
            async with receive_stream:
                async for event in receive_stream:
                    try:
                        payload_str = json.dumps(event, ensure_ascii=False)
                    except TypeError as exc:
                        logger.exception("Failed to serialise stream event")
                        payload = {"event": "error", "message": f"Serialisation error: {exc}"}
                        payload_str = json.dumps(payload, ensure_ascii=False)
                    yield (payload_str + "\n").encode("utf-8")
        except Exception as stream_exc:
            logger.exception("Stream failed")
            payload_str = json.dumps({"event": "error", "message": f"Stream failure: {stream_exc}"}, ensure_ascii=False)
            yield (payload_str + "\n").encode("utf-8")
        finally:
            if not processing_task.done():
                processing_task.cancel()
            with contextlib.suppress(Exception):
                await processing_task

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


# ============== JOB MANAGEMENT ENDPOINTS ==============

class JobRequest(BaseModel):
    url: str
    company: Optional[str] = ""
    notes: Optional[str] = ""

    class Config:
        extra = "forbid"


class JobUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    company: Optional[str] = None

    class Config:
        extra = "forbid"


@app.get("/api/jobs")
async def list_jobs() -> List[Dict[str, Any]]:
    """Get all stored jobs."""
    return job_storage.get_all_jobs()


@app.post("/api/jobs")
async def add_job(payload: JobRequest) -> Dict[str, Any]:
    """Add a new job link."""
    try:
        job = job_storage.add_job(payload.url, payload.company or "", payload.notes or "")
        return job
    except Exception as exc:
        logger.exception("Failed to add job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    """Get a specific job by ID."""
    job = job_storage.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.patch("/api/jobs/{job_id}")
async def update_job(job_id: str, payload: JobUpdateRequest) -> Dict[str, Any]:
    """Update a job's fields."""
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    job = job_storage.update_job(job_id, updates)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Delete a job."""
    if job_storage.delete_job(job_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Job not found")


# ============== PDF GENERATION ENDPOINT ==============

@app.get("/api/pdf/download")
async def download_pdf():
    """Generate PDF from LaTeX and return for download."""
    import subprocess
    from fastapi.responses import FileResponse

    latex_dir = BASE_DIR / "docs" / "latex"
    tex_file = latex_dir / "main.tex"

    if not tex_file.exists():
        raise HTTPException(status_code=404, detail="LaTeX file not found. Run tailoring first.")

    # Read company name from keyword_analysis.json written by Tool 1
    company_name = "RESUME"
    json_path = BASE_DIR / "output" / "keyword_analysis.json"
    logger.info(f"[PDF DEBUG] BASE_DIR = {BASE_DIR}")
    logger.info(f"[PDF DEBUG] keyword_analysis.json path = {json_path}")
    logger.info(f"[PDF DEBUG] keyword_analysis.json exists = {json_path.exists()}")
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"[PDF DEBUG] JSON contents = {data}")
            raw = data.get("company_name", "").strip()
            logger.info(f"[PDF DEBUG] raw company_name = '{raw}'")
            _invalid = {'', 'RESUME', 'UNKNOWN_COMPANY', 'UNNAMED_COMPANY', 'UNKNOWN',
                        'UNNAMED', 'N_A', 'NA', 'NONE', 'NOT_MENTIONED', 'COMPANY_NAME'}
            if raw and raw.upper() not in _invalid:
                company_name = raw
                logger.info(f"[PDF DEBUG] Using company_name = '{company_name}'")
            else:
                logger.warning(f"[PDF DEBUG] company_name '{raw}' invalid, falling back to RESUME")
        except Exception as e:
            logger.warning(f"[PDF DEBUG] Could not read keyword_analysis.json: {e}")
    else:
        logger.warning(f"[PDF DEBUG] keyword_analysis.json NOT FOUND at {json_path} — run the tailoring pipeline first")

    # Try to find pdflatex - check common paths on Windows
    pdflatex_cmd = "pdflatex"
    miktex_paths = [
        r"C:\Users\Owner\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
    ]
    for path in miktex_paths:
        if Path(path).exists():
            pdflatex_cmd = path
            break

    try:
        result = subprocess.run(
            [pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(latex_dir), str(tex_file)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(latex_dir)
        )

        pdf_file = latex_dir / "main.pdf"
        if not pdf_file.exists():
            logger.error(f"pdflatex output: {result.stdout}\n{result.stderr}")
            raise HTTPException(status_code=500, detail="PDF generation failed. Check LaTeX syntax.")

        # Build filename from config.json name + company name
        candidate_name = "CANDIDATE"
        config_path = BASE_DIR / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as cf:
                    cfg = json.load(cf)
                raw_name = cfg.get("name", "").strip()
                if raw_name:
                    candidate_name = re.sub(r'[^A-Z0-9]', '_', raw_name.upper()).strip('_')
            except Exception:
                pass
        pdf_filename = f"{candidate_name}_({company_name}).pdf"
        logger.info(f"[PDF DEBUG] Final PDF filename = '{pdf_filename}'")

        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename=pdf_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"'
            }
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="PDF generation timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pdflatex not found. Install TeX distribution.")
    except Exception as exc:
        logger.exception("PDF generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============== ATS CHECK ENDPOINT ==============

class ATSCheckRequest(BaseModel):
    resume: str = Field(..., alias="resume")
    job_description: str = Field(..., alias="jobDescription")

    class Config:
        populate_by_name = True
        extra = "forbid"


@app.post("/api/ats/check")
async def ats_check(payload: ATSCheckRequest) -> Dict[str, Any]:
    """Run ATS compatibility check on resume against job description."""
    extractor = KeywordExtractor()
    evaluator = ResumeEvaluator()

    try:
        keywords = await anyio.to_thread.run_sync(
            extractor.extract_keywords,
            payload.job_description
        )

        evaluation = await anyio.to_thread.run_sync(
            evaluator.evaluate_resume,
            payload.job_description,
            payload.resume,
            keywords
        )

        return {
            "keywords": keywords,
            "evaluation": evaluation,
            "score": evaluation.get("score", 0),
            "status": "complete"
        }
    except Exception as exc:
        logger.exception("ATS check failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============== APPLICATION AUTOMATION ENDPOINT ==============

class ApplyRequest(BaseModel):
    job_id: str

    class Config:
        extra = "forbid"


def _create_apply_stream(job: Dict[str, Any]) -> StreamingResponse:
    """Create a streaming response for the full auto-apply pipeline."""
    send_stream, receive_stream = anyio.create_memory_object_stream(50)

    async def run_application():
        try:
            browser = BrowserEngine()
            vision = VisionAnalyzer()
            code_gen = CodeGenerator()
            form_filler = FormFiller()
            healer = SelfHealer(browser, vision, code_gen)

            job_storage.update_job(job['id'], {"status": "in_progress"})

            await send_stream.send(
                {"event": "started", "job_id": job['id'], "url": job['url']}
            )

            async def _async_send(event_data):
                await send_stream.send(event_data)

            def detailed_progress(event_data: Dict[str, Any]) -> None:
                """Send structured event. Works from both async and sync contexts."""
                try:
                    # Try async path first (from within event loop)
                    loop = asyncio.get_running_loop()
                    asyncio.ensure_future(_async_send(event_data), loop=loop)
                except RuntimeError:
                    # We're in a worker thread (e.g. tailoring callback)
                    try:
                        anyio.from_thread.run(send_stream.send, event_data)
                    except RuntimeError:
                        pass

            def progress_callback(message: str) -> None:
                detailed_progress({"event": "progress", "message": message})

            state = await healer.run_full_application(
                job_url=job['url'],
                job_id=job['id'],
                company=job.get('company', ''),
                form_filler=form_filler,
                on_progress=progress_callback,
                on_detailed_progress=detailed_progress,
            )

            if state.success:
                job_storage.mark_applied(job['id'])
                await send_stream.send(
                    {"event": "complete", "success": True, "message": "Application submitted successfully"}
                )
            else:
                job_storage.mark_failed(job['id'], "; ".join(state.errors[-3:]))
                await send_stream.send(
                    {"event": "complete", "success": False, "errors": state.errors}
                )
        except Exception as exc:
            logger.exception("Application automation failed")
            job_storage.mark_failed(job['id'], str(exc))
            await send_stream.send(
                {"event": "error", "message": str(exc)}
            )
        finally:
            with contextlib.suppress(Exception):
                await send_stream.aclose()

    async def event_stream():
        task = asyncio.create_task(run_application())
        try:
            async with receive_stream:
                async for event in receive_stream:
                    yield (json.dumps(event) + "\n").encode("utf-8")
        finally:
            if not task.done():
                task.cancel()
            with contextlib.suppress(Exception):
                await task

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/api/apply/start")
async def start_application(payload: ApplyRequest) -> StreamingResponse:
    """Start automated job application process for an existing job."""
    job = job_storage.get_job_by_id(payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify at least one resume source exists (txt or LaTeX)
    resume_txt = BASE_DIR / "data" / "resume.txt"
    resume_tex = BASE_DIR / "docs" / "latex" / "main.tex"
    if not (resume_txt.exists() and resume_txt.stat().st_size > 0) and not resume_tex.exists():
        raise HTTPException(
            status_code=400,
            detail="No resume found. Place resume at data/resume.txt or ensure docs/latex/main.tex exists.",
        )

    return _create_apply_stream(job)


@app.post("/api/jobs/add-and-apply")
async def add_and_apply(payload: JobRequest) -> StreamingResponse:
    """Add a new job and immediately start the full auto-apply pipeline."""
    # Verify at least one resume source exists (txt or LaTeX)
    resume_txt = BASE_DIR / "data" / "resume.txt"
    resume_tex = BASE_DIR / "docs" / "latex" / "main.tex"
    if not (resume_txt.exists() and resume_txt.stat().st_size > 0) and not resume_tex.exists():
        raise HTTPException(
            status_code=400,
            detail="No resume found. Place resume at data/resume.txt or ensure docs/latex/main.tex exists.",
        )

    try:
        job = job_storage.add_job(payload.url, payload.company or "", payload.notes or "")
    except Exception as exc:
        logger.exception("Failed to add job")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _create_apply_stream(job)


def start() -> None:
    """Entry point for `python mcp_server.py`."""
    import uvicorn

    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start()
