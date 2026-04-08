from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResumeOut(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    raw_text: Optional[str] = None
    clean_text: Optional[str] = None
    parse_status: Optional[str] = None
    extract_status: Optional[str] = None
    model_version: Optional[str] = None

    class Config:
        orm_mode = True


class EntityItem(BaseModel):
    text: str
    label: str
    start: int
    end: int
    score: Optional[float] = None


class ResumeAnalysisOut(BaseModel):
    id: int
    file_name: str
    file_type: Optional[str] = None
    parse_status: Optional[str] = None
    extract_status: Optional[str] = None
    model_version: Optional[str] = None
    raw_text: Optional[str] = None
    clean_text: Optional[str] = None
    message: Optional[str] = None
    entity_result: List[EntityItem] = Field(default_factory=list)
    profile_raw: Dict[str, Any] = Field(default_factory=dict)
    profile_masked: Dict[str, Any] = Field(default_factory=dict)
    sensitive_summary: Dict[str, Any] = Field(default_factory=dict)
