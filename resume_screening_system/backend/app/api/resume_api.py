import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.resume_schema import ResumeAnalysisOut, ResumeOut
from app.services.analysis_service import analyze_resume_by_id, get_resume_analysis_by_id
from app.services.parse_service import parse_resume_by_id
from app.services.resume_service import create_resume_record, delete_resume_record, list_resumes

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=ResumeOut, summary="上传简历")
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_ext = ["pdf", "docx", "txt"]
    file_name = file.filename or ""
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""

    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="仅支持 pdf、docx、txt 文件")

    save_path = UPLOAD_DIR / file_name
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return create_resume_record(db, file_name, str(save_path), ext)


@router.get("/", response_model=list[ResumeOut], summary="获取简历列表")
def get_resume_list(db: Session = Depends(get_db)):
    return list_resumes(db)


@router.get("/{resume_id}", response_model=ResumeAnalysisOut, summary="获取简历分析详情")
def get_resume_detail(resume_id: int, db: Session = Depends(get_db)):
    result = get_resume_analysis_by_id(db, resume_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历不存在")
    return result


@router.post("/{resume_id}/parse", response_model=ResumeOut, summary="解析简历文本")
def parse_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = parse_resume_by_id(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    return resume


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisOut, summary="执行简历分析")
def analyze_resume(resume_id: int, db: Session = Depends(get_db)):
    result = analyze_resume_by_id(db, resume_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历不存在")
    return result


@router.delete("/{resume_id}", summary="删除简历")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    success = delete_resume_record(db, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="简历不存在")
    return {"message": "简历删除成功"}
