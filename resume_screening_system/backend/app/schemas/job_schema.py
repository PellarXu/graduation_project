from typing import Optional

from pydantic import BaseModel, Field, validator


class JobBase(BaseModel):
    job_name: str
    job_type: str
    degree_requirement: Optional[str] = None
    major_requirement: Optional[str] = None
    skill_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    skill_weight: float = Field(..., ge=0, le=1)
    experience_weight: float = Field(..., ge=0, le=1)
    degree_weight: float = Field(..., ge=0, le=1)
    major_weight: float = Field(..., ge=0, le=1)

    @validator("job_name", "job_type")
    def strip_required_text(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @validator("skill_weight", "experience_weight", "degree_weight", "major_weight")
    def round_weight(cls, value: float):
        return round(float(value), 4)


class JobCreate(JobBase):
    @validator("major_weight")
    def validate_total_weight(cls, value: float, values):
        total = round(
            float(values.get("skill_weight", 0))
            + float(values.get("experience_weight", 0))
            + float(values.get("degree_weight", 0))
            + float(value),
            4,
        )
        if abs(total - 1) > 0.0001:
            raise ValueError("四项权重之和必须等于 1")
        return value


class JobUpdate(BaseModel):
    job_name: Optional[str] = None
    job_type: Optional[str] = None
    degree_requirement: Optional[str] = None
    major_requirement: Optional[str] = None
    skill_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    skill_weight: Optional[float] = Field(None, ge=0, le=1)
    experience_weight: Optional[float] = Field(None, ge=0, le=1)
    degree_weight: Optional[float] = Field(None, ge=0, le=1)
    major_weight: Optional[float] = Field(None, ge=0, le=1)


class JobOut(JobBase):
    id: int

    class Config:
        orm_mode = True
