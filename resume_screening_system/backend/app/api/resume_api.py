import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.resume_schema import ResumeOut, ResumeExtractOut
from app.services.resume_service import create_resume_record, list_resumes, delete_resume_record
from app.services.parse_service import parse_resume_by_id
from app.services.extract_service import extract_resume_by_id

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeOut, summary="Upload resume")
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_ext = ["pdf", "docx", "txt"]
    file_name = file.filename
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""

    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Only pdf, docx and txt files are allowed")

    save_path = os.path.join(UPLOAD_DIR, file_name)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resume = create_resume_record(db, file_name, save_path, ext)
    return resume


@router.get("/", response_model=list[ResumeOut], summary="Get resume list")
def get_resume_list(db: Session = Depends(get_db)):
    return list_resumes(db)


@router.post("/{resume_id}/parse", response_model=ResumeOut, summary="Parse resume")
def parse_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = parse_resume_by_id(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/{resume_id}/extract", response_model=ResumeExtractOut, summary="Extract resume info")
def extract_resume(resume_id: int, db: Session = Depends(get_db)):
    result = extract_resume_by_id(db, resume_id)
    if not result:
        raise HTTPException(status_code=404, detail="Resume not found")
    return result


@router.delete("/{resume_id}", summary="Delete resume")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    success = delete_resume_record(db, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"message": "Resume deleted successfully"}