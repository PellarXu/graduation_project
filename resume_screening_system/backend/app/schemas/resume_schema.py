from pydantic import BaseModel
from typing import Optional, List


class ResumeOut(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    raw_text: Optional[str] = None
    clean_text: Optional[str] = None
    parse_status: Optional[str] = None

    class Config:
        orm_mode = True


class ResumeExtractOut(BaseModel):
    id: int
    file_name: str
    parse_status: Optional[str] = None
    raw_text: Optional[str] = None
    clean_text: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    skills: List[str] = []