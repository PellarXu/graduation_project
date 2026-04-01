from sqlalchemy.orm import Session

from app.services.analysis_service import get_resume_analysis_by_id


def extract_resume_by_id(db: Session, resume_id: int):
    return get_resume_analysis_by_id(db, resume_id)
