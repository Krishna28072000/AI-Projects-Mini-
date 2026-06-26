import uvicorn
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from schemas import SkillGenerateRequest, SkillGenerateResponse, SkillZipRequest
from openai_service import generate_skill_package
from skill_validator import validate_skill_md
from zip_service import create_skill_zip_bytes


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

app = FastAPI(title="Multi-Platform Skill Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static",
    )


@app.get("/")
def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return {
            "message": "Frontend index.html not found",
            "expected_path": str(index_file),
        }

    return FileResponse(index_file)


@app.post("/generate-skill-md", response_model=SkillGenerateResponse)
def generate_skill(request: SkillGenerateRequest):
    package = generate_skill_package(
        requirement=request.requirement,
        platform=request.platform,
    )

    skill_md = package["skill_md"]
    validation = validate_skill_md(skill_md)

    return {
        "platform": package["platform"],
        "skill_name": package["skill_name"],
        "skill_md": skill_md,
        "files": package["files"],
        "validation": validation,
    }


@app.post("/download-skill-zip")
def download_skill_zip(request: SkillZipRequest):
    validation = validate_skill_md(request.skill_md)

    if not validation["is_valid"]:
        return {
            "error": "Invalid skill markdown. Please fix validation errors before downloading ZIP.",
            "validation": validation,
        }

    zip_bytes, zip_filename = create_skill_zip_bytes(
        platform=request.platform,
        skill_name=request.skill_name,
        skill_md=request.skill_md,
        files=[file.model_dump() for file in request.files],
    )

    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )