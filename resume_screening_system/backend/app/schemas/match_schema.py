from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume_ids: List[int] = Field(default_factory=list)


class MatchWeights(BaseModel):
    skill_weight: float
    experience_weight: float
    degree_weight: float
    major_weight: float


class MatchScoreDetail(BaseModel):
    raw_score: float
    weighted_score: float
    evidence: List[str] = Field(default_factory=list)


class MatchResultItem(BaseModel):
    resume_id: int
    file_name: str
    analysis_status: str
    total_score: Optional[float] = None
    dimension_scores: Dict[str, MatchScoreDetail] = Field(default_factory=dict)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    final_explanations: List[str] = Field(default_factory=list)
    fairness_notes: List[str] = Field(default_factory=list)
    profile_masked: Dict[str, Any] = Field(default_factory=dict)


class MatchListOut(BaseModel):
    job_id: int
    job_name: str
    job_type: str
    weights: MatchWeights
    selected_resume_count: int
    available_resume_count: int
    results: List[MatchResultItem] = Field(default_factory=list)
