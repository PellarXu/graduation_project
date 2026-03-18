from sqlalchemy.orm import Session
from app.models.resume import Resume
from algorithm.extractor.rule_extractor import extract_resume_info


def extract_resume_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None

    text = resume.clean_text or resume.raw_text or ""
    extracted = extract_resume_info(text)

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "parse_status": resume.parse_status,
        "raw_text": resume.raw_text,
        "clean_text": resume.clean_text,
        "phone": extracted["phone"],
        "email": extracted["email"],
        "degree": extracted["degree"],
        "major": extracted["major"],
        "skills": extracted["skills"],
    }