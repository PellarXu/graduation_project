SENSITIVE_FIELDS = {"name", "gender", "age", "hometown"}


def _mask_value(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ["已脱敏" if item else item for item in value]
    return "已脱敏"


def build_masked_profile(profile_raw: dict):
    masked = {}
    for key, value in (profile_raw or {}).items():
        if key in SENSITIVE_FIELDS:
            masked[key] = _mask_value(value)
        else:
            masked[key] = value
    return masked


def build_sensitive_summary(profile_raw: dict, profile_masked: dict):
    masked_fields = []
    for field in SENSITIVE_FIELDS:
        if profile_raw.get(field):
            masked_fields.append(field)
    return {
        "masked_fields": masked_fields,
        "school_used_for_display_only": bool(profile_raw.get("schools")),
        "note": "姓名、性别、年龄、籍贯默认脱敏；院校信息仅展示，不参与总分。",
        "preview": {field: profile_masked.get(field) for field in masked_fields},
    }
