"""AI Matching Engine: scores and ranks candidates against a Job Requirement.

Uses OpenAI embeddings for:
  - Semantic skill matching (React ≈ ReactJS, Postgres ≈ PostgreSQL, etc.)
  - Domain and certification relevance

Uses deterministic Python for:
  - Experience, education, location & notice-period scoring
  - Weighted aggregation
"""
import logging
import math
from typing import Dict, List, Optional, Tuple

from app.config import (
    MATCHING_WEIGHTS,
    OPENAI_EMBEDDING_MODEL,
    SKILL_MATCH_THRESHOLD,
)
from app.models.schemas import (
    CandidateProfile,
    JobRequirement,
    RankedCandidate,
    ScoreBreakdown,
)
from app.services.openai_client import get_client

logger = logging.getLogger(__name__)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_texts(texts: List[str]) -> Dict[str, List[float]]:
    """Return a map of input text -> embedding vector (batched API call)."""
    unique = [t for t in dict.fromkeys(texts) if t and t.strip()]
    if not unique:
        return {}
    client = get_client()
    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=unique,
    )
    ordered = sorted(response.data, key=lambda x: x.index)
    return {text: item.embedding for text, item in zip(unique, ordered)}


def _skill_match(
    required_skills: List[str],
    candidate_skills: List[str],
    embeddings: Dict[str, List[float]],
) -> Tuple[float, List[str], List[str], Dict[str, str]]:
    """Match required skills to candidate skills via embedding similarity."""
    if not required_skills:
        return 0.0, [], [], {}

    matched: List[str] = []
    missing: List[str] = []
    similar: Dict[str, str] = {}
    scores: List[float] = []

    cand_embs = [
        (skill, embeddings.get(skill))
        for skill in candidate_skills
        if embeddings.get(skill)
    ]

    for req in required_skills:
        req_emb = embeddings.get(req)
        if not req_emb:
            missing.append(req)
            continue

        best_sim = 0.0
        best_skill: Optional[str] = None
        for cand_skill, cand_emb in cand_embs:
            sim = _cosine_similarity(req_emb, cand_emb)
            if sim > best_sim:
                best_sim = sim
                best_skill = cand_skill

        if best_sim >= SKILL_MATCH_THRESHOLD and best_skill:
            matched.append(req)
            scores.append(best_sim * 100)
            if best_skill.lower() != req.lower():
                similar[req] = best_skill
        else:
            missing.append(req)

    skill_score = round(sum(scores) / len(required_skills), 2) if scores else 0.0
    return skill_score, matched, missing, similar


def _embedding_score(
    text_a: str,
    text_b: str,
    embeddings: Dict[str, List[float]],
    neutral_if_empty: float = 70.0,
) -> float:
    if not text_a.strip() or not text_b.strip():
        return neutral_if_empty
    emb_a = embeddings.get(text_a)
    emb_b = embeddings.get(text_b)
    if not emb_a or not emb_b:
        return neutral_if_empty
    return round(max(0.0, min(100.0, _cosine_similarity(emb_a, emb_b) * 100)), 2)


def _build_recommendation(
    overall: float,
    matched: List[str],
    missing: List[str],
    candidate: CandidateProfile,
) -> str:
    name = candidate.name or candidate.filename
    if overall >= 80:
        tone = "Strong fit"
    elif overall >= 60:
        tone = "Moderate fit"
    else:
        tone = "Weak fit"
    parts = [f"{tone} for {name}."]
    if matched:
        parts.append(f"Matched {len(matched)} required skill(s): {', '.join(matched[:8])}.")
    if missing:
        parts.append(f"Gaps: {', '.join(missing[:8])}.")
    return " ".join(parts)


def score_candidate(
    candidate: CandidateProfile,
    job: JobRequirement,
    embeddings: Dict[str, List[float]],
) -> RankedCandidate:
    """Score a single candidate against the job. Returns a RankedCandidate."""
    breakdown = ScoreBreakdown()
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    similar_skills: Dict[str, str] = {}

    try:
        breakdown.skills, matched_skills, missing_skills, similar_skills = _skill_match(
            job.required_skills,
            candidate.skills,
            embeddings,
        )
        job_domain = (job.domain or job.title or "").strip()
        cand_domain = (candidate.domain or "").strip()
        breakdown.domain = _embedding_score(job_domain, cand_domain, embeddings)

        job_cert_context = (
            f"Certifications for {job.title or 'role'}: "
            f"{', '.join(job.required_skills)}. {job.description or ''}"
        )[:2000]
        cand_certs = ", ".join(candidate.certifications) if candidate.certifications else ""
        breakdown.certifications = _embedding_score(
            job_cert_context,
            cand_certs,
            embeddings,
            neutral_if_empty=50.0 if not cand_certs else 70.0,
        )
    except Exception as e:
        logger.error(f"Embedding scoring failed for {candidate.filename}: {e}")
        breakdown.skills = _keyword_skill_score(candidate, job)

    breakdown.experience = _score_experience(candidate, job)
    breakdown.education = _score_education(candidate, job)
    breakdown.location_notice = _score_location_notice(candidate, job)

    w = MATCHING_WEIGHTS
    overall = (
        breakdown.skills * w["skills"]
        + breakdown.experience * w["experience"]
        + breakdown.education * w["education"]
        + breakdown.domain * w["domain"]
        + breakdown.certifications * w["certifications"]
        + breakdown.location_notice * w["location_notice"]
    )
    recommendation = _build_recommendation(
        overall, matched_skills, missing_skills, candidate
    )

    return RankedCandidate(
        candidate=candidate,
        overall_score=round(overall, 2),
        breakdown=breakdown,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        similar_skills=similar_skills,
        recommendation=recommendation,
    )


def _keyword_skill_score(candidate: CandidateProfile, job: JobRequirement) -> float:
    """Fallback if embedding call fails: simple case-insensitive overlap."""
    if not job.required_skills:
        return 0.0
    candidate_skills_lower = {s.lower().strip() for s in candidate.skills}
    matched = sum(
        1 for req in job.required_skills if req.lower().strip() in candidate_skills_lower
    )
    return round((matched / len(job.required_skills)) * 100, 2)


def _score_experience(candidate: CandidateProfile, job: JobRequirement) -> float:
    if job.min_experience_years is None:
        return 70.0
    cand_exp = candidate.total_experience_years or 0
    req = job.min_experience_years
    if cand_exp >= req:
        ratio = min(cand_exp / req, 1.5) if req > 0 else 1.0
        return min(100.0, 80 + (ratio - 1) * 40)
    return max(0.0, (cand_exp / req) * 70) if req > 0 else 0.0


def _score_education(candidate: CandidateProfile, job: JobRequirement) -> float:
    if not candidate.education:
        return 0.0
    if not job.preferred_education:
        return 70.0
    preferred_lower = job.preferred_education.lower()
    for edu in candidate.education:
        if preferred_lower in edu.lower():
            return 100.0
    return 50.0


def _score_location_notice(candidate: CandidateProfile, job: JobRequirement) -> float:
    score = 50.0
    if job.preferred_location and candidate.location:
        if (
            job.preferred_location.lower() in candidate.location.lower()
            or candidate.location.lower() in job.preferred_location.lower()
        ):
            score += 30
        else:
            score -= 10

    if candidate.notice_period:
        np_lower = candidate.notice_period.lower()
        if "immediate" in np_lower or "0" in np_lower:
            score += 20
        elif "15" in np_lower or "2 week" in np_lower:
            score += 15
        elif "30" in np_lower or "1 month" in np_lower:
            score += 10
        elif "60" in np_lower or "2 month" in np_lower:
            score += 5

    return max(0.0, min(100.0, score))


def _collect_embed_texts(
    candidates: List[CandidateProfile], job: JobRequirement
) -> List[str]:
    texts: List[str] = list(job.required_skills)
    job_domain = (job.domain or job.title or "").strip()
    if job_domain:
        texts.append(job_domain)
    job_cert_context = (
        f"Certifications for {job.title or 'role'}: "
        f"{', '.join(job.required_skills)}. {job.description or ''}"
    )[:2000]
    texts.append(job_cert_context)

    for c in candidates:
        texts.extend(c.skills)
        if c.domain:
            texts.append(c.domain.strip())
        if c.certifications:
            texts.append(", ".join(c.certifications))
    return texts


def rank_candidates(
    candidates: List[CandidateProfile], job: JobRequirement
) -> List[RankedCandidate]:
    """Score all candidates and return them ranked by overall_score descending."""
    embed_texts = _collect_embed_texts(candidates, job)
    try:
        embeddings = _embed_texts(embed_texts)
    except Exception as e:
        logger.error(f"Failed to compute embeddings: {e}")
        embeddings = {}

    ranked = [score_candidate(c, job, embeddings) for c in candidates]
    ranked.sort(key=lambda r: r.overall_score, reverse=True)
    for i, r in enumerate(ranked, start=1):
        r.rank = i
    return ranked
