from sqlalchemy import Column, BigInteger, String, DECIMAL
from app.core.database import Base


class WeightTemplate(Base):
    __tablename__ = "weight_template"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    template_name = Column(String(100))
    job_type = Column(String(50))
    skill_weight = Column(DECIMAL(5, 2))
    degree_weight = Column(DECIMAL(5, 2))
    major_weight = Column(DECIMAL(5, 2))
    experience_weight = Column(DECIMAL(5, 2))
    project_weight = Column(DECIMAL(5, 2))
    condition_weight = Column(DECIMAL(5, 2))