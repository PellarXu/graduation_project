import os
from sqlalchemy.orm import Session
from app.models.resume import Resume


def create_resume_record(db: Session, file_name: str, file_path: str, file_type: str):
    resume = Resume(
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        parse_status="uploaded"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def list_resumes(db: Session):
    return db.query(Resume).order_by(Resume.id.desc()).all()


def delete_resume_record(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return False

    file_path = resume.file_path

    db.delete(resume)
    db.commit()

    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return True