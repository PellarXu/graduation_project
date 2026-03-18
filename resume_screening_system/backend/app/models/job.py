from sqlalchemy import Column, BigInteger, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Job(Base):
    __tablename__ = "job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(100), nullable=False)
    job_type = Column(String(50), nullable=False)
    degree_requirement = Column(String(50))
    major_requirement = Column(String(255))
    skill_requirement = Column(Text)
    experience_requirement = Column(String(50))
    city = Column(String(50))
    description = Column(Text)
    weight_template_id = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())