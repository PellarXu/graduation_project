from app.models.resume import Resume


PARSE_STATUS_LABELS = {
    "uploaded": "待解析",
    "pending": "待解析",
    "parsed": "已完成",
    "failed": "解析失败",
}

EXTRACT_STATUS_LABELS = {
    "pending": "待分析",
    "ready": "已完成",
    "failed": "分析失败",
    "model_not_ready": "分析失败",
}


def format_parse_status(status: str | None) -> str:
    return PARSE_STATUS_LABELS.get(status or "", "待解析")


def format_extract_status(status: str | None) -> str:
    return EXTRACT_STATUS_LABELS.get(status or "", "待分析")


def build_resume_summary_payload(resume: Resume) -> dict:
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_path": resume.file_path,
        "file_type": resume.file_type,
        "raw_text": resume.raw_text,
        "clean_text": resume.clean_text,
        "parse_status": format_parse_status(resume.parse_status),
        "extract_status": format_extract_status(resume.extract_status),
        "model_version": resume.model_version,
    }


def build_resume_analysis_payload(resume: Resume, message: str | None = None) -> dict:
    payload = build_resume_summary_payload(resume)
    payload.update(
        {
            "message": message,
            "entity_result": resume.entity_result or [],
            "profile_raw": resume.profile_raw or {},
            "profile_masked": resume.profile_masked or {},
            "sensitive_summary": resume.sensitive_summary or {},
        }
    )
    return payload
