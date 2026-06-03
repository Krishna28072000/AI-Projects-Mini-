"""Extract raw text from resume files (PDF, DOC, DOCX, TXT)."""
from pathlib import Path
from typing import Optional
import logging

import pypdf
from docx import Document

logger = logging.getLogger(__name__)


def extract_text(file_path: Path) -> str:
    """Route to the right extractor based on file extension."""
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return _extract_docx(file_path)
        elif ext == ".txt":
            return _extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path.name}: {e}")
        return ""


def _extract_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    text_parts = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_docx(file_path: Path) -> str:
    """Extract text from a DOCX file. Note: legacy .doc files may not parse fully."""
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # Also pull text out of tables (some resumes use tabular layouts)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text)
    return "\n".join(paragraphs).strip()


def _extract_txt(file_path: Path) -> str:
    """Extract text from a plain text file."""
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file content for duplicate detection."""
    import hashlib
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
