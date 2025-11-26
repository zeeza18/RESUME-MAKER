"""FastAPI server exposing the resume tools for frontend and integrations."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"

for path in (BASE_DIR, SCRIPTS_DIR):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)

import anyio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from resume_crew import ResumeCrew
from tools.tool1 import KeywordExtractor
from tools.tool2 import ResumeTailor
from tools.tool3 import ResumeEvaluator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Resume Crew API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    keywords: Dict[str, Any]
    feedback: Optional[str] = None

    @validator("original_resume")
    def validate_original(cls, value: str) -> str:
        if _word_count(value) < 50:
            raise ValueError("Resume must be at least 50 words.")
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
    except Exception as exc:  # pragma: no cover - defensive guard
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
            payload.feedback,
        )
        return result
    except Exception as exc:  # pragma: no cover - defensive guard
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
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Resume evaluation failed")
        raise HTTPException(status_code=500, detail=f"Resume evaluation failed: {exc}") from exc


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
        except Exception as exc:  # pragma: no cover - defensive guard
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
            # Send an initial heartbeat chunk so the client sees the stream immediately
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
        except Exception as stream_exc:  # pragma: no cover - defensive guard
            logger.exception("Stream failed")
            payload_str = json.dumps({"event": "error", "message": f"Stream failure: {stream_exc}"}, ensure_ascii=False)
            yield (payload_str + "\n").encode("utf-8")
        finally:
            if not processing_task.done():
                processing_task.cancel()
            with contextlib.suppress(Exception):
                await processing_task

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


def start() -> None:
    """Entry point for `python mcp_server.py`."""
    import uvicorn

    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start()
