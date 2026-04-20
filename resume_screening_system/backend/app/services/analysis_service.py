from datetime import datetime

from sqlalchemy.orm import Session

from algorithm.analysis.profile_builder import build_profile
from algorithm.analysis.sensitive import build_masked_profile, build_sensitive_summary
from algorithm.ner.inference import ModelNotReadyError, NERInferenceService
from app.models.resume import Resume
from app.services.resume_view_service import build_resume_analysis_payload


def get_resume_analysis_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None
    return build_resume_analysis_payload(resume)


def _mark_analysis_failed(resume: Resume, db: Session, message: str):
    resume.extract_status = "failed"
    resume.entity_result = []
    resume.profile_raw = {}
    resume.profile_masked = {}
    resume.sensitive_summary = {}
    resume.analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)
    return build_resume_analysis_payload(resume, message=message)


def analyze_resume_by_id(db: Session, resume_id: int):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None

    if resume.parse_status != "parsed" or not resume.clean_text:
        resume.extract_status = "pending"
        db.commit()
        db.refresh(resume)
        return build_resume_analysis_payload(resume, message="请先完成简历解析，再执行分析。")

    service = NERInferenceService()
    try:
        entities, model_version = service.predict(resume.clean_text)
    except ModelNotReadyError as exc:
        resume.model_version = exc.model_version
        return _mark_analysis_failed(resume, db, "模型尚未就绪，暂时无法执行结构化分析。")
    except Exception as exc:  # pragma: no cover - defensive error branch
        return _mark_analysis_failed(resume, db, f"实体抽取失败：{exc}")

    try:
        profile_raw = build_profile(resume.clean_text, entities)
        profile_masked = build_masked_profile(profile_raw)
        sensitive_summary = build_sensitive_summary(profile_raw, profile_masked)
    except Exception as exc:  # pragma: no cover - defensive error branch
        resume.model_version = model_version
        return _mark_analysis_failed(resume, db, f"画像构建失败：{exc}")

    resume.extract_status = "ready"
    resume.model_version = model_version
    resume.entity_result = entities
    resume.profile_raw = profile_raw
    resume.profile_masked = profile_masked
    resume.sensitive_summary = sensitive_summary
    resume.analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)

    return build_resume_analysis_payload(resume, message="简历分析完成。")
