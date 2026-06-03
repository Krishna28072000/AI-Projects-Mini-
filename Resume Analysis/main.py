"""FastAPI app: Upload, Parse, Match, Rank endpoints."""
import logging
import sys
import uuid
from pathlib import Path
from typing import List, Optional

# main.py lives at project root; app package is under backend/
_BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from app.models.schemas import CandidateProfile, JobRequirement
from app.services import storage
from app.services.text_extractor import extract_text, compute_file_hash
from app.services.resume_parser import parse_resume, extract_skills_from_description
from app.services.matching_engine import rank_candidates
from app.services.excel_export import candidates_to_excel, ranked_to_excel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Resume Shortlisting Tool",
    description="Upload resumes, define a job, get ranked candidates.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = FRONTEND_DIR / "templates" / "index.html"
    if not html_path.is_file():
        raise HTTPException(
            500,
            f"Frontend not found at {html_path}. "
            "Ensure the frontend/ folder is next to main.py.",
        )
    return html_path.read_text(encoding="utf-8")


@app.post("/api/resumes/upload")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Upload one or more resume files. Returns parsed candidate profiles."""
    if not files:
        raise HTTPException(400, "No files uploaded.")

    results = {
        "parsed": [],
        "duplicates": [],
        "errors": [],
        "skipped": [],
    }

    for upload in files:
        try:
            filename = upload.filename or "unknown"
            ext = Path(filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                results["skipped"].append({
                    "filename": filename,
                    "reason": f"Unsupported file type: {ext}",
                })
                continue

            content = await upload.read()
            if len(content) > MAX_FILE_SIZE:
                results["skipped"].append({
                    "filename": filename,
                    "reason": f"File exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit",
                })
                continue
            if len(content) == 0:
                results["skipped"].append({
                    "filename": filename,
                    "reason": "Empty file",
                })
                continue

            safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = UPLOAD_DIR / safe_name
            file_path.write_bytes(content)

            file_hash = compute_file_hash(file_path)
            if storage.is_duplicate(file_hash):
                results["duplicates"].append({"filename": filename})
                file_path.unlink(missing_ok=True)
                continue

            raw_text = extract_text(file_path)
            if not raw_text.strip():
                results["errors"].append({
                    "filename": filename,
                    "reason": "Could not extract text from file",
                })
                file_path.unlink(missing_ok=True)
                continue

            profile = parse_resume(filename, raw_text)
            storage.save_candidate(profile)
            storage.record_hash(file_hash, filename)
            results["parsed"].append(profile.model_dump(mode="json"))

        except Exception as e:
            logger.exception(f"Failed to process {upload.filename}")
            results["errors"].append({
                "filename": upload.filename,
                "reason": str(e),
            })

    return results


@app.get("/api/candidates")
def list_all_candidates():
    candidates = storage.list_candidates()
    return {
        "count": len(candidates),
        "candidates": [c.model_dump(mode="json") for c in candidates],
    }


@app.get("/api/candidates/{candidate_id}")
def get_one_candidate(candidate_id: str):
    c = storage.get_candidate(candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return c.model_dump(mode="json")


@app.delete("/api/candidates")
def clear_all_candidates():
    storage.clear_candidates()
    for f in UPLOAD_DIR.glob("*"):
        if f.is_file():
            f.unlink(missing_ok=True)
    return {"status": "cleared"}


@app.get("/api/candidates/export/excel")
def export_candidates_excel():
    candidates = storage.list_candidates()
    if not candidates:
        raise HTTPException(404, "No candidates to export")
    content = candidates_to_excel(candidates)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=candidates.xlsx"},
    )


@app.post("/api/jobs")
def create_job(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    skills_input: Optional[str] = Form(None),
    min_experience_years: Optional[float] = Form(None),
    domain: Optional[str] = Form(None),
    preferred_location: Optional[str] = Form(None),
    preferred_education: Optional[str] = Form(None),
):
    if not description and not skills_input:
        raise HTTPException(400, "Provide either a job description or a skills list.")

    skills = []
    if skills_input:
        skills = [s.strip() for s in skills_input.split(",") if s.strip()]

    job = JobRequirement(
        job_id=str(uuid.uuid4())[:8],
        title=title,
        description=description,
        required_skills=skills,
        min_experience_years=min_experience_years,
        domain=domain,
        preferred_location=preferred_location,
        preferred_education=preferred_education,
    )

    if description and not skills:
        try:
            job.required_skills = extract_skills_from_description(description)
        except Exception as e:
            logger.warning(f"Could not extract skills from JD: {e}")

    storage.save_job(job)
    return job.model_dump(mode="json")


@app.get("/api/jobs")
def list_all_jobs():
    jobs = storage.list_jobs()
    return {"jobs": [j.model_dump(mode="json") for j in jobs]}


@app.get("/api/jobs/{job_id}")
def get_one_job(job_id: str):
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job.model_dump(mode="json")


@app.post("/api/match/{job_id}")
def match_candidates(job_id: str):
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    candidates = storage.list_candidates()
    if not candidates:
        raise HTTPException(400, "No candidates parsed yet. Upload resumes first.")

    ranked = rank_candidates(candidates, job)
    return {
        "job": job.model_dump(mode="json"),
        "ranked": [r.model_dump(mode="json") for r in ranked],
    }


@app.post("/api/match/{job_id}/export")
def export_ranked_excel(job_id: str):
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    candidates = storage.list_candidates()
    if not candidates:
        raise HTTPException(400, "No candidates to rank")
    ranked = rank_candidates(candidates, job)
    content = ranked_to_excel(ranked)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=ranked_candidates_{job_id}.xlsx"
        },
    )


@app.get("/api/health")
def health():
    from app.config import OPENAI_API_KEY

    return {
        "status": "ok",
        "api_key_configured": bool(OPENAI_API_KEY),
        "candidate_count": len(storage.list_candidates()),
        "job_count": len(storage.list_jobs()),
    }


if __name__ == "__main__":
    import uvicorn

    host = "127.0.0.1"
    port = 8000
    print()
    print("=" * 56)
    print(f"  Resume Shortlist UI:  http://{host}:{port}/")
    print(f"  API docs (optional):  http://{host}:{port}/docs")
    print("=" * 56)
    print("  Open the first URL above — /docs is not the main UI.")
    print()
    uvicorn.run("main:app", host=host, port=port, reload=True)
