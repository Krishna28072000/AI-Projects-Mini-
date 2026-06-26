from pydantic import BaseModel, Field
from typing import List, Literal


class SkillGenerateRequest(BaseModel):
    requirement: str = Field(..., min_length=10)
    platform: Literal["openai", "claude", "generic"] = "openai"


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]


class GeneratedSkillFile(BaseModel):
    path: str
    content: str


class SkillGenerateResponse(BaseModel):
    platform: str
    skill_name: str
    skill_md: str
    files: List[GeneratedSkillFile]
    validation: ValidationResult


class SkillZipFile(BaseModel):
    path: str
    content: str


class SkillZipRequest(BaseModel):
    platform: Literal["openai", "claude", "generic"] = "openai"
    skill_name: str = Field(..., min_length=1)
    skill_md: str = Field(..., min_length=20)
    files: List[SkillZipFile] = []