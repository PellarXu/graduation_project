import re
from collections import defaultdict


FIELD_ALIASES = {
    "name": ["姓名", "name"],
    "phones": ["电话", "手机号", "联系方式", "联系电话", "phone", "mobile", "contact"],
    "emails": ["邮箱", "电子邮箱", "email", "e-mail"],
    "gender": ["性别", "gender"],
    "age": ["年龄", "age"],
    "hometown": ["籍贯", "户籍", "生源地", "hometown", "native place"],
    "schools": ["学校", "毕业院校", "院校", "school", "university", "college"],
    "degrees": ["学历", "学位", "degree", "education"],
    "majors": ["专业", "major"],
    "titles": ["求职意向", "应聘岗位", "目标岗位", "岗位", "职位", "title", "target role", "position"],
    "skills": ["技能", "专业技能", "技能特长", "skills", "technical skills"],
    "experience_years": ["工作年限", "经验年限", "工作经验", "years of experience", "experience"],
}

PHONE_PATTERN = re.compile(r"1\d{10}")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
KEY_VALUE_PATTERN = re.compile(r"^\s*([^:：]{1,20})[:：]\s*(.+?)\s*$")
SKILL_SPLIT_PATTERN = re.compile(r"[、,，/；;\s]+")
VALID_DEGREES = {"中专", "大专", "专科", "本科", "学士", "硕士", "研究生", "博士", "associate", "bachelor", "master", "phd", "doctor"}


SECTION_ALIASES = {
    "education": ["教育经历", "教育背景", "学历背景", "education", "education background"],
    "work": ["工作经历", "工作经验", "任职经历", "work experience", "employment history"],
    "internship": ["实习经历", "实践经历", "internship", "internship experience"],
    "project": ["项目经历", "项目经验", "科研项目", "project experience", "projects"],
    "skills": ["技能", "专业技能", "技能特长", "skills", "technical skills"],
}


def _group_entities(entities):
    grouped = defaultdict(list)
    for entity in entities:
        text = (entity.get("text") or "").strip()
        label = entity.get("label")
        if text and label:
            grouped[label].append(text)
    return {key: list(dict.fromkeys(values)) for key, values in grouped.items()}


def _deduplicate(values):
    return [item for item in dict.fromkeys(value.strip() for value in values if value and value.strip())]


def _extract_first_phone(value: str):
    matched = PHONE_PATTERN.search(value or "")
    return matched.group(0) if matched else None


def _extract_first_email(value: str):
    matched = EMAIL_PATTERN.search(value or "")
    return matched.group(0) if matched else None


def _split_skills(value: str):
    return [item.strip() for item in SKILL_SPLIT_PATTERN.split(value or "") if item and item.strip()]


def _parse_key_values(text: str):
    parsed = {key: [] for key in FIELD_ALIASES.keys()}
    alias_to_field = {
        alias.lower(): field_name
        for field_name, aliases in FIELD_ALIASES.items()
        for alias in aliases
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = KEY_VALUE_PATTERN.match(line)
        if not matched:
            continue

        key = matched.group(1).strip().lower()
        value = matched.group(2).strip()
        field_name = alias_to_field.get(key)
        if not field_name or not value:
            continue

        if field_name == "phones":
            phone = _extract_first_phone(value)
            if phone:
                parsed[field_name].append(phone)
            continue

        if field_name == "emails":
            email = _extract_first_email(value)
            if email:
                parsed[field_name].append(email)
            continue

        if field_name == "skills":
            parsed[field_name].extend(_split_skills(value))
            continue

        if field_name in {"name", "gender", "age", "hometown", "experience_years"}:
            parsed[field_name] = [value]
            continue

        parsed[field_name].append(value)

    return {key: _deduplicate(values) for key, values in parsed.items()}


def _merge_list_values(parsed_values, entity_values):
    return _deduplicate((parsed_values or []) + (entity_values or []))


def _prefer_parsed_or_merge(parsed_values, entity_values, validator=None):
    parsed_values = _deduplicate(parsed_values or [])
    entity_values = _deduplicate(entity_values or [])
    if validator:
        parsed_values = [item for item in parsed_values if validator(item)]
        entity_values = [item for item in entity_values if validator(item)]
    if parsed_values:
        return parsed_values
    return entity_values


def _is_reasonable_skill(value: str):
    value = (value or "").strip()
    if not value or ":" in value or "\n" in value:
        return False
    if len(value) < 2 or len(value) > 30:
        return False
    return True


def _is_reasonable_major(value: str):
    value = (value or "").strip()
    return bool(value) and ":" not in value and "\n" not in value and len(value) >= 2


def _is_reasonable_degree(value: str):
    value = (value or "").strip().lower()
    return value in VALID_DEGREES


def _detect_sections(text: str):
    sections = {key: [] for key in SECTION_ALIASES.keys()}
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched_section = None
        for section, aliases in SECTION_ALIASES.items():
            if any(alias in line for alias in aliases):
                matched_section = section
                break
        if matched_section:
            current = matched_section
            continue
        if current:
            sections[current].append(line)
    return sections


def _extract_years(text: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*年", text or "")
    return float(match.group(1)) if match else 0


def build_profile(text: str, entities):
    grouped = _group_entities(entities)
    parsed = _parse_key_values(text)
    sections = _detect_sections(text)
    work_texts = sections.get("work", [])
    internship_texts = sections.get("internship", [])
    project_texts = sections.get("project", [])

    return {
        "name": (parsed.get("name") or grouped.get("NAME") or [None])[0],
        "phones": _prefer_parsed_or_merge(parsed.get("phones"), grouped.get("PHONE"), _extract_first_phone),
        "emails": _prefer_parsed_or_merge(parsed.get("emails"), grouped.get("EMAIL"), _extract_first_email),
        "gender": (parsed.get("gender") or grouped.get("GENDER") or [None])[0],
        "age": (parsed.get("age") or grouped.get("AGE") or [None])[0],
        "hometown": (parsed.get("hometown") or grouped.get("HOMETOWN") or [None])[0],
        "schools": _prefer_parsed_or_merge(parsed.get("schools"), grouped.get("SCHOOL")),
        "degrees": _prefer_parsed_or_merge(parsed.get("degrees"), grouped.get("DEGREE"), _is_reasonable_degree),
        "majors": _prefer_parsed_or_merge(parsed.get("majors"), grouped.get("MAJOR"), _is_reasonable_major),
        "companies": grouped.get("COMPANY", []),
        "titles": _prefer_parsed_or_merge(parsed.get("titles"), grouped.get("TITLE")),
        "skills": _merge_list_values(
            parsed.get("skills"),
            [item for item in grouped.get("SKILL", []) if _is_reasonable_skill(item)],
        ),
        "projects": grouped.get("PROJECT", []),
        "experience_years": (parsed.get("experience_years") or grouped.get("EXPERIENCE_YEARS") or [None])[0],
        "experience_summary": {
            "work_texts": work_texts,
            "internship_texts": internship_texts,
            "project_texts": project_texts,
            "work_years": max(
                [_extract_years(item) for item in work_texts + internship_texts] + [0]
            ),
        },
        "raw_sections": sections,
    }
