from sqlalchemy import JSON, BigInteger, Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Resume(Base):
    __tablename__ = "resume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20))
    raw_text = Column(Text)
    clean_text = Column(Text)
    parse_status = Column(String(20), default="uploaded")
    extract_status = Column(String(20), default="pending")
    model_version = Column(String(100))
    entity_result = Column(JSON)
    profile_raw = Column(JSON)
    profile_masked = Column(JSON)
    sensitive_summary = Column(JSON)
    upload_time = Column(DateTime, server_default=func.now())
    analyzed_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
