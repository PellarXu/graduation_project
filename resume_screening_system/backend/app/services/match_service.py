from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.resume import Resume
from app.services.extract_service import extract_resume_by_id
from algorithm.matcher.basic_matcher import calculate_match_score, get_weight_config


def match_resumes_for_job(db: Session, job_id: int, selected_resume_ids=None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None

    query = db.query(Resume).filter(Resume.parse_status == "parsed")

    if selected_resume_ids:
        query = query.filter(Resume.id.in_(selected_resume_ids))

    resumes = query.all()
    weights = get_weight_config(job.job_type)

    results = []

    for resume in resumes:
        extracted = extract_resume_by_id(db, resume.id)
        if not extracted:
            continue

        score_result = calculate_match_score(job, extracted)

        results.append({
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "phone": extracted.get("phone"),
            "email": extracted.get("email"),
            "degree": extracted.get("degree"),
            "major": extracted.get("major"),
            "skills": extracted.get("skills", []),
            "raw_skill_score": score_result["raw_skill_score"],
            "raw_degree_score": score_result["raw_degree_score"],
            "raw_major_score": score_result["raw_major_score"],
            "skill_score": score_result["skill_score"],
            "degree_score": score_result["degree_score"],
            "major_score": score_result["major_score"],
            "total_score": score_result["total_score"]
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "job_id": job.id,
        "job_name": job.job_name,
        "job_type": job.job_type,
        "skill_weight": weights["skill_weight"],
        "degree_weight": weights["degree_weight"],
        "major_weight": weights["major_weight"],
        "selected_resume_count": len(resumes),
        "results": results
    }