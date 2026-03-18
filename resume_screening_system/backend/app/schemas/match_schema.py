from pydantic import BaseModel
from typing import List, Optional


class MatchResultItem(BaseModel):
    resume_id: int
    file_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    skills: List[str] = []
    raw_skill_score: float
    raw_degree_score: float
    raw_major_score: float
    skill_score: float
    degree_score: float
    major_score: float
    total_score: float


class MatchListOut(BaseModel):
    job_id: int
    job_name: str
    job_type: str
    skill_weight: float
    degree_weight: float
    major_weight: float
    selected_resume_count: int
    results: List[MatchResultItem]