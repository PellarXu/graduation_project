from sqlalchemy.orm import Session
from app.models.resume import Resume
from algorithm.parser.txt_parser import parse_txt
from algorithm.parser.docx_parser import parse_docx
from algorithm.parser.pdf_parser import parse_pdf
from algorithm.parser.cleaner import clean_text


def parse_resume_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None

    file_type = (resume.file_type or "").lower()

    if file_type == "txt":
        raw_text = parse_txt(resume.file_path)
    elif file_type == "docx":
        raw_text = parse_docx(resume.file_path)
    elif file_type == "pdf":
        raw_text = parse_pdf(resume.file_path)
    else:
        raw_text = ""

    cleaned_text = clean_text(raw_text)

    resume.raw_text = raw_text
    resume.clean_text = cleaned_text
    resume.parse_status = "parsed"

    db.commit()
    db.refresh(resume)

    return resume