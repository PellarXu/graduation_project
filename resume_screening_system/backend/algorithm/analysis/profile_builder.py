import re
from collections import defaultdict


SECTION_ALIASES = {
    "education": ["教育经历", "教育背景", "学历背景"],
    "work": ["工作经历", "工作经验", "任职经历"],
    "internship": ["实习经历", "实践经历"],
    "project": ["项目经历", "项目经验", "科研项目"],
    "skills": ["技能", "专业技能", "技能特长"],
}


def _group_entities(entities):
    grouped = defaultdict(list)
    for entity in entities:
        text = (entity.get("text") or "").strip()
        label = entity.get("label")
        if text and label:
            grouped[label].append(text)
    return {key: list(dict.fromkeys(values)) for key, values in grouped.items()}


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
    sections = _detect_sections(text)
    work_texts = sections.get("work", [])
    internship_texts = sections.get("internship", [])
    project_texts = sections.get("project", [])

    return {
        "name": grouped.get("NAME", [None])[0],
        "phones": grouped.get("PHONE", []),
        "emails": grouped.get("EMAIL", []),
        "gender": grouped.get("GENDER", [None])[0],
        "age": grouped.get("AGE", [None])[0],
        "hometown": grouped.get("HOMETOWN", [None])[0],
        "schools": grouped.get("SCHOOL", []),
        "degrees": grouped.get("DEGREE", []),
        "majors": grouped.get("MAJOR", []),
        "companies": grouped.get("COMPANY", []),
        "titles": grouped.get("TITLE", []),
        "skills": grouped.get("SKILL", []),
        "projects": grouped.get("PROJECT", []),
        "experience_years": grouped.get("EXPERIENCE_YEARS", [None])[0],
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
