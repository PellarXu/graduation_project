SENSITIVE_FIELDS = {"name", "gender", "age", "hometown", "phones", "emails"}


def _masked_value(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ["已脱敏" for _ in value] or ["已脱敏"]
    return "已脱敏"


def build_masked_profile(profile_raw: dict):
    profile_raw = profile_raw or {}
    return {
        "basic_info": {
            "name": _masked_value(profile_raw.get("name")),
            "gender": _masked_value(profile_raw.get("gender")),
            "age": _masked_value(profile_raw.get("age")),
            "hometown": _masked_value(profile_raw.get("hometown")),
        },
        "education": {
            "degrees": profile_raw.get("degrees") or [],
            "majors": profile_raw.get("majors") or [],
            "schools": profile_raw.get("schools") or [],
        },
        "experience": {
            "experience_years": profile_raw.get("experience_years"),
            "titles": profile_raw.get("titles") or [],
            "companies": profile_raw.get("companies") or [],
            "projects": profile_raw.get("projects") or [],
        },
        "skills": profile_raw.get("skills") or [],
        "analysis_summary": profile_raw.get("analysis_summary") or [],
        "scoring_scope": {
            "included": ["技能", "经验", "学历", "专业"],
            "display_only": ["院校", "项目经历", "岗位方向"],
            "masked": ["姓名", "性别", "年龄", "籍贯", "电话", "邮箱"],
        },
    }


def build_sensitive_summary(profile_raw: dict, profile_masked: dict):
    profile_raw = profile_raw or {}
    profile_masked = profile_masked or {}
    masked_fields = [field for field in ["name", "gender", "age", "hometown"] if profile_raw.get(field)]
    return {
        "masked_fields": masked_fields,
        "school_used_for_display_only": bool(profile_raw.get("schools")),
        "note": "姓名、性别、年龄、籍贯、电话、邮箱会先脱敏；院校与项目方向仅用于人工复核展示，不参与总分。",
        "preview": profile_masked.get("basic_info") or {},
    }
