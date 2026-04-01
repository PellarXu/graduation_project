from sqlalchemy.orm import Session

from algorithm.matcher.scorer import calculate_match_result
from app.models.job import Job
from app.models.resume import Resume


def match_resumes_for_job(db: Session, job_id: int, selected_resume_ids=None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None

    query = db.query(Resume).filter(Resume.parse_status == "parsed")
    if selected_resume_ids:
        query = query.filter(Resume.id.in_(selected_resume_ids))

    resumes = query.order_by(Resume.id.desc()).all()
    weights = {
        "skill_weight": float(job.skill_weight),
        "experience_weight": float(job.experience_weight),
        "degree_weight": float(job.degree_weight),
        "major_weight": float(job.major_weight),
    }

    results = []
    available_resume_count = 0
    for resume in resumes:
        profile_masked = resume.profile_masked or {}
        if resume.extract_status != "ready" or not resume.profile_raw:
            results.append(
                {
                    "resume_id": resume.id,
                    "file_name": resume.file_name,
                    "analysis_status": resume.extract_status or "pending",
                    "total_score": None,
                    "dimension_scores": {},
                    "matched_skills": [],
                    "missing_skills": [],
                    "final_explanations": ["模型尚未就绪或该简历尚未完成分析，暂不能生成正式匹配结果。"],
                    "fairness_notes": [],
                    "profile_masked": profile_masked,
                }
            )
            continue

        available_resume_count += 1
        match_result = calculate_match_result(job, resume.profile_raw, profile_masked)
        results.append(
            {
                "resume_id": resume.id,
                "file_name": resume.file_name,
                "analysis_status": "ready",
                **match_result,
            }
        )

    results.sort(key=lambda item: item["total_score"] if item["total_score"] is not None else -1, reverse=True)
    return {
        "job_id": job.id,
        "job_name": job.job_name,
        "job_type": job.job_type,
        "weights": weights,
        "selected_resume_count": len(resumes),
        "available_resume_count": available_resume_count,
        "results": results,
    }
