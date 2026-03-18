from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.job_schema import JobCreate, JobUpdate, JobOut
from app.services.job_service import (
    create_job,
    list_jobs,
    get_job_by_id,
    update_job,
    delete_job
)

router = APIRouter()


@router.post("/", response_model=JobOut, summary="新增岗位")
def create_job_api(job: JobCreate, db: Session = Depends(get_db)):
    return create_job(db, job)


@router.get("/", response_model=list[JobOut], summary="查询岗位列表")
def list_jobs_api(db: Session = Depends(get_db)):
    return list_jobs(db)


@router.get("/{job_id}", response_model=JobOut, summary="查询单个岗位")
def get_job_api(job_id: int, db: Session = Depends(get_db)):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job


@router.put("/{job_id}", response_model=JobOut, summary="修改岗位")
def update_job_api(job_id: int, job: JobUpdate, db: Session = Depends(get_db)):
    updated_job = update_job(db, job_id, job)
    if not updated_job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return updated_job


@router.delete("/{job_id}", summary="删除岗位")
def delete_job_api(job_id: int, db: Session = Depends(get_db)):
    success = delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return {"message": "岗位删除成功"}