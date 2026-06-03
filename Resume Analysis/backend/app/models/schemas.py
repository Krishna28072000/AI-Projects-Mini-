"""Pydantic data models."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class CandidateProfile(BaseModel):
    """Parsed resume data."""
    candidate_id: str
    filename: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    total_experience_years: Optional[float] = None
    experience_summary: Optional[str] = None
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    current_company: Optional[str] = None
    notice_period: Optional[str] = None
    location: Optional[str] = None
    domain: Optional[str] = None
    raw_text_preview: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class JobRequirement(BaseModel):
    """Job description or skills to match against."""
    job_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    min_experience_years: Optional[float] = None
    preferred_education: Optional[str] = None
    domain: Optional[str] = None
    preferred_location: Optional[str] = None
    max_notice_period_days: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoreBreakdown(BaseModel):
    """Per-parameter score breakdown."""
    skills: float = 0.0
    experience: float = 0.0
    education: float = 0.0
    domain: float = 0.0
    certifications: float = 0.0
    location_notice: float = 0.0


class RankedCandidate(BaseModel):
    """A candidate with their match score and analysis."""
    candidate: CandidateProfile
    overall_score: float
    breakdown: ScoreBreakdown
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    similar_skills: Dict[str, str] = Field(default_factory=dict)
    recommendation: str = ""
    rank: int = 0


class JobUploadRequest(BaseModel):
    """Request body for creating a job."""
    title: Optional[str] = None
    description: Optional[str] = None
    skills_input: Optional[str] = None
    min_experience_years: Optional[float] = None
    domain: Optional[str] = None
    preferred_location: Optional[str] = None
