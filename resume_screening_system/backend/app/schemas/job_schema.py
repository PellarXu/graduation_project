from pydantic import BaseModel
from typing import Optional


class JobBase(BaseModel):
    job_name: str
    job_type: str
    degree_requirement: Optional[str] = None
    major_requirement: Optional[str] = None
    skill_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    weight_template_id: Optional[int] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    job_name: Optional[str] = None
    job_type: Optional[str] = None
    degree_requirement: Optional[str] = None
    major_requirement: Optional[str] = None
    skill_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    weight_template_id: Optional[int] = None


class JobOut(JobBase):
    id: int

    class Config:
        orm_mode = True