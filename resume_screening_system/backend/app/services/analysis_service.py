from datetime import datetime

from sqlalchemy.orm import Session

from algorithm.analysis.profile_builder import build_profile
from algorithm.analysis.sensitive import build_masked_profile, build_sensitive_summary
from algorithm.ner.inference import ModelNotReadyError, NERInferenceService
from app.models.resume import Resume


def _resume_to_analysis_payload(resume: Resume, message: str | None = None, source_type: str = "model"):
    entity_result = resume.entity_result or []
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "parse_status": resume.parse_status,
        "extract_status": resume.extract_status,
        "model_version": resume.model_version,
        "raw_text": resume.raw_text,
        "clean_text": resume.clean_text,
        "source_type": source_type,
        "message": message,
        "entity_result": entity_result,
        "profile_raw": resume.profile_raw or {},
        "profile_masked": resume.profile_masked or {},
        "sensitive_summary": resume.sensitive_summary or {},
    }


def get_resume_analysis_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None
    return _resume_to_analysis_payload(resume)


def analyze_resume_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None

    if resume.parse_status != "parsed" or not resume.clean_text:
        resume.extract_status = "pending"
        db.commit()
        db.refresh(resume)
        return _resume_to_analysis_payload(resume, message="请先完成简历解析，再执行分析。")

    service = NERInferenceService()
    try:
        entities, model_version = service.predict(resume.clean_text)
    except ModelNotReadyError as exc:
        resume.extract_status = "model_not_ready"
        resume.model_version = exc.model_version
        resume.entity_result = []
        resume.profile_raw = {}
        resume.profile_masked = {}
        resume.sensitive_summary = {}
        resume.analyzed_at = datetime.utcnow()
        db.commit()
        db.refresh(resume)
        return _resume_to_analysis_payload(resume, message=str(exc))

    profile_raw = build_profile(resume.clean_text, entities)
    profile_masked = build_masked_profile(profile_raw)
    sensitive_summary = build_sensitive_summary(profile_raw, profile_masked)

    resume.extract_status = "ready"
    resume.model_version = model_version
    resume.entity_result = entities
    resume.profile_raw = profile_raw
    resume.profile_masked = profile_masked
    resume.sensitive_summary = sensitive_summary
    resume.analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)

    return _resume_to_analysis_payload(resume, message="简历分析完成")
