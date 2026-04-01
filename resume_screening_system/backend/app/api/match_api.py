from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.match_schema import MatchListOut, MatchRequest
from app.services.match_service import match_resumes_for_job

router = APIRouter()


@router.post("/jobs/{job_id}", response_model=MatchListOut, summary="执行岗位匹配")
def match_job(job_id: int, payload: MatchRequest, db: Session = Depends(get_db)):
    result = match_resumes_for_job(db, job_id, payload.resume_ids)
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result
