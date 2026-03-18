from sqlalchemy import Column, BigInteger, String, DateTime, Text
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
    upload_time = Column(DateTime, server_default=func.now())