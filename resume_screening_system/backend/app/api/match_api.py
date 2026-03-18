from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.match_schema import MatchListOut
from app.services.match_service import match_resumes_for_job

router = APIRouter()


@router.get("/{job_id}", response_model=MatchListOut, summary="Match resumes for a job")
def match_job(
    job_id: int,
    resume_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db)
):
    result = match_resumes_for_job(db, job_id, resume_ids)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result