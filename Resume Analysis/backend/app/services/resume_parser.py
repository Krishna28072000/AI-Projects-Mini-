"""Parse raw resume text into structured CandidateProfile using OpenAI."""
import json
import logging
from typing import Optional
import uuid

from app.config import OPENAI_CHAT_MODEL
from app.models.schemas import CandidateProfile
from app.services.openai_client import get_client

logger = logging.getLogger(__name__)

PARSER_SYSTEM_PROMPT = """You are a resume parser. Extract structured information from resume text.

Return ONLY valid JSON (no markdown fences, no preamble) with this exact shape:
{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "skills": ["skill1", "skill2"],
  "total_experience_years": number or null,
  "experience_summary": "1-2 sentence summary",
  "education": ["degree1", "degree2"],
  "certifications": ["cert1", "cert2"],
  "current_company": "string or null",
  "notice_period": "string or null (e.g. '30 days', 'Immediate', '2 months')",
  "location": "city, country or null",
  "domain": "primary domain like 'Web Development', 'Data Science', 'DevOps', etc."
}

Rules:
- Normalize skill names (e.g., "ReactJS" and "React.js" -> "React")
- Extract ALL technical and soft skills mentioned
- For experience, calculate total years from work history if not explicitly stated
- For notice period, only fill if explicitly mentioned in the resume
- Keep education entries concise: "B.Tech Computer Science, IIT Delhi"
"""


def parse_resume(filename: str, raw_text: str) -> CandidateProfile:
    """Send resume text to OpenAI and parse the structured response."""
    candidate_id = str(uuid.uuid4())[:8]

    if not raw_text or len(raw_text.strip()) < 50:
        logger.warning(f"Resume {filename} has too little text to parse.")
        return CandidateProfile(
            candidate_id=candidate_id,
            filename=filename,
            raw_text_preview=raw_text[:200],
        )

    client = get_client()
    text_for_parsing = raw_text[:15000]

    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this resume:\n\n{text_for_parsing}"},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        return CandidateProfile(
            candidate_id=candidate_id,
            filename=filename,
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            skills=data.get("skills", []) or [],
            total_experience_years=data.get("total_experience_years"),
            experience_summary=data.get("experience_summary"),
            education=data.get("education", []) or [],
            certifications=data.get("certifications", []) or [],
            current_company=data.get("current_company"),
            notice_period=data.get("notice_period"),
            location=data.get("location"),
            domain=data.get("domain"),
            raw_text_preview=raw_text[:500],
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for {filename}: {e}")
        return CandidateProfile(
            candidate_id=candidate_id,
            filename=filename,
            raw_text_preview=raw_text[:500],
        )
    except Exception as e:
        logger.error(f"Error parsing {filename}: {e}")
        return CandidateProfile(
            candidate_id=candidate_id,
            filename=filename,
            raw_text_preview=raw_text[:500],
        )


def extract_skills_from_description(description: str) -> list[str]:
    """Extract required technical skills from a job description."""
    client = get_client()
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        max_tokens=500,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract required technical skills from a job description. "
                    'Return JSON: {"skills": ["skill1", "skill2"]}'
                ),
            },
            {"role": "user", "content": f"Job description:\n\n{description}"},
        ],
    )
    content = (response.choices[0].message.content or "").strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    data = json.loads(content)
    if isinstance(data, list):
        return data
    return data.get("skills", data.get("required_skills", [])) or []
