"""Simple file-based storage. Swap for a real DB (Postgres/Mongo) for production."""
import json
from pathlib import Path
from typing import List, Optional, Dict
from threading import Lock

from app.config import DATA_DIR
from app.models.schemas import CandidateProfile, JobRequirement

_lock = Lock()

CANDIDATES_FILE = DATA_DIR / "candidates.json"
JOBS_FILE = DATA_DIR / "jobs.json"
HASHES_FILE = DATA_DIR / "file_hashes.json"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    tmp.replace(path)


# --- Candidates ---

def save_candidate(candidate: CandidateProfile) -> None:
    with _lock:
        all_candidates = _load_json(CANDIDATES_FILE, {})
        all_candidates[candidate.candidate_id] = candidate.model_dump(mode="json")
        _save_json(CANDIDATES_FILE, all_candidates)


def list_candidates() -> List[CandidateProfile]:
    raw = _load_json(CANDIDATES_FILE, {})
    return [CandidateProfile(**c) for c in raw.values()]


def get_candidate(candidate_id: str) -> Optional[CandidateProfile]:
    raw = _load_json(CANDIDATES_FILE, {})
    if candidate_id in raw:
        return CandidateProfile(**raw[candidate_id])
    return None


def clear_candidates() -> None:
    with _lock:
        _save_json(CANDIDATES_FILE, {})
        _save_json(HASHES_FILE, {})


# --- Jobs ---

def save_job(job: JobRequirement) -> None:
    with _lock:
        all_jobs = _load_json(JOBS_FILE, {})
        all_jobs[job.job_id] = job.model_dump(mode="json")
        _save_json(JOBS_FILE, all_jobs)


def get_job(job_id: str) -> Optional[JobRequirement]:
    raw = _load_json(JOBS_FILE, {})
    if job_id in raw:
        return JobRequirement(**raw[job_id])
    return None


def list_jobs() -> List[JobRequirement]:
    raw = _load_json(JOBS_FILE, {})
    return [JobRequirement(**j) for j in raw.values()]


# --- File hash tracking for duplicate detection ---

def is_duplicate(file_hash: str) -> bool:
    hashes = _load_json(HASHES_FILE, {})
    return file_hash in hashes


def record_hash(file_hash: str, filename: str) -> None:
    with _lock:
        hashes = _load_json(HASHES_FILE, {})
        hashes[file_hash] = filename
        _save_json(HASHES_FILE, hashes)
