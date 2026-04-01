from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job_schema import JobCreate, JobUpdate


def _validate_job_weight_sum(job_data: dict):
    total = round(
        float(job_data.get("skill_weight", 0))
        + float(job_data.get("experience_weight", 0))
        + float(job_data.get("degree_weight", 0))
        + float(job_data.get("major_weight", 0)),
        4,
    )
    if abs(total - 1) > 0.0001:
        raise ValueError("四项权重之和必须等于 1")


def create_job(db: Session, job_data: JobCreate):
    payload = job_data.dict()
    _validate_job_weight_sum(payload)
    job = Job(**payload)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(db: Session):
    return db.query(Job).order_by(Job.id.desc()).all()


def get_job_by_id(db: Session, job_id: int):
    return db.query(Job).filter(Job.id == job_id).first()


def update_job(db: Session, job_id: int, job_data: JobUpdate):
    job = get_job_by_id(db, job_id)
    if not job:
        return None

    payload = job_data.dict(exclude_unset=True)
    merged = {
        "skill_weight": float(job.skill_weight),
        "experience_weight": float(job.experience_weight),
        "degree_weight": float(job.degree_weight),
        "major_weight": float(job.major_weight),
    }
    merged.update({key: value for key, value in payload.items() if value is not None})
    _validate_job_weight_sum(merged)

    for key, value in payload.items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job_id: int):
    job = get_job_by_id(db, job_id)
    if not job:
        return False

    db.delete(job)
    db.commit()
    return True
