"""Local JSON storage for job applications."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


class JobStorage:
    """Manages job links storage in local JSON file."""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "data" / "jobs.json"
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create storage file if it doesn't exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._save_jobs([])

    def _load_jobs(self) -> List[Dict[str, Any]]:
        """Load jobs from JSON file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Save jobs to JSON file."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)

    def add_job(self, url: str, company: str = "", notes: str = "") -> Dict[str, Any]:
        """Add a new job link."""
        jobs = self._load_jobs()

        # Extract company name from URL if not provided
        if not company:
            company = self._extract_company_from_url(url)

        job = {
            "id": str(uuid.uuid4()),
            "url": url,
            "company": company,
            "notes": notes,
            "status": "pending",
            "date_added": datetime.now().isoformat(),
            "date_applied": None,
            "attempts": 0,
            "last_error": None
        }

        jobs.append(job)
        self._save_jobs(jobs)
        return job

    def _extract_company_from_url(self, url: str) -> str:
        """Try to extract company name from URL."""
        import re
        # Common job boards
        patterns = [
            r'(?:greenhouse|lever|workday|taleo|icims|smartrecruiters)\.(?:io|com)/([^/]+)',
            r'careers\.([^.]+)\.',
            r'jobs\.([^.]+)\.',
            r'(?:www\.)?([^.]+)\.(?:com|io|org)/(?:careers|jobs)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).title()
        return "Unknown"

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all stored jobs."""
        return self._load_jobs()

    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs that haven't been applied to yet."""
        jobs = self._load_jobs()
        return [j for j in jobs if j['status'] == 'pending']

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        jobs = self._load_jobs()
        for job in jobs:
            if job['id'] == job_id:
                return job
        return None

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job's fields."""
        jobs = self._load_jobs()
        for i, job in enumerate(jobs):
            if job['id'] == job_id:
                jobs[i].update(updates)
                self._save_jobs(jobs)
                return jobs[i]
        return None

    def mark_applied(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Mark a job as applied."""
        return self.update_job(job_id, {
            "status": "applied",
            "date_applied": datetime.now().isoformat()
        })

    def mark_failed(self, job_id: str, error: str) -> Optional[Dict[str, Any]]:
        """Mark a job application as failed."""
        job = self.get_job_by_id(job_id)
        if job:
            return self.update_job(job_id, {
                "status": "failed",
                "attempts": job.get('attempts', 0) + 1,
                "last_error": error
            })
        return None

    def delete_job(self, job_id: str) -> bool:
        """Delete a job from storage."""
        jobs = self._load_jobs()
        original_count = len(jobs)
        jobs = [j for j in jobs if j['id'] != job_id]
        if len(jobs) < original_count:
            self._save_jobs(jobs)
            return True
        return False

    def clear_all(self) -> None:
        """Clear all jobs (use with caution)."""
        self._save_jobs([])
