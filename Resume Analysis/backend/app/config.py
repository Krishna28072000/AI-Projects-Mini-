"""Application configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
BASE_DIR = BACKEND_DIR

# Support .env in project root (venv at root) or backend/
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Semantic skill match threshold (cosine similarity, 0–1)
SKILL_MATCH_THRESHOLD = float(os.getenv("SKILL_MATCH_THRESHOLD", "0.72"))

# Storage
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads").lstrip("./")
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data").lstrip("./")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

# Matching weightages (from spec)
MATCHING_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.20,
    "education": 0.10,
    "domain": 0.10,
    "certifications": 0.10,
    "location_notice": 0.10,
}
