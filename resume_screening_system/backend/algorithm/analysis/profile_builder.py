from __future__ import annotations

import re
from collections import defaultdict
from datetime import date


KEY_ALIASES = {
    "name": ["姓名", "名字", "candidate name", "name"],
    "gender": ["性别", "gender"],
    "age": ["年龄", "age"],
    "hometown": ["籍贯", "户口地", "户籍", "生源地", "家乡", "hometown"],
    "phone": ["电话", "手机号", "手机", "联系电话", "phone", "mobile"],
    "email": ["邮箱", "电子邮箱", "email", "e-mail", "mail"],
}

SECTION_ALIASES = {
    "education": ["教育背景", "教育经历", "教育信息", "学历背景"],
    "skills": ["专业技能", "技能特长", "技能清单", "技能标签", "专业能力", "技术栈", "核心技能"],
    "work": ["工作经历", "工作经验", "职业经历", "就业经历"],
    "internship": ["实习经历", "实习经验"],
    "project": ["项目经历", "项目经验", "项目背景"],
}

DEGREE_KEYWORDS = ["中专", "大专", "专科", "本科", "学士", "硕士", "研究生", "博士", "phd", "bachelor", "master"]
MAJOR_SUFFIXES = [
    "计算机科学与技术",
    "软件工程",
    "网络工程",
    "信息安全",
    "人工智能",
    "数据科学与大数据技术",
    "通信工程",
    "电子信息工程",
    "自动化",
    "数学与应用数学",
    "统计学",
    "工商管理",
    "市场营销",
    "广告学",
    "新闻学",
    "传播学",
    "视觉传达设计",
    "数字媒体艺术",
    "产品设计",
]

TITLE_HINTS = (
    "工程师",
    "开发",
    "经理",
    "专员",
    "运营",
    "产品",
    "设计师",
    "分析师",
    "测试",
    "顾问",
    "架构师",
    "负责人",
)
COMPANY_HINTS = ("公司", "科技", "集团", "信息", "网络", "软件", "银行", "医院", "学院", "大学")
PROJECT_HINTS = ("项目", "平台", "系统", "APP", "App", "小程序")
SKILL_LINE_SKIP = {
    "精通技术栈",
    "熟悉技术栈",
    "了解技术栈",
    "专业技能",
    "技术栈",
    "核心技能",
}
CHINESE_SKILL_HINTS = ("开发", "设计", "优化", "架构", "算法", "测试", "数据", "网络", "渲染", "分析", "运维")
KNOWN_CHINESE_SKILLS = {
    "性能优化",
    "内存管理",
    "UI渲染优化",
    "移动端架构设计",
    "数据结构与算法",
    "操作系统",
    "计算机网络",
    "移动应用开发",
}

PHONE_PATTERN = re.compile(r"(?<!\d)(1[3-9]\d[-\s]?\d{4}[-\s]?\d{4})(?!\d)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DATE_RANGE_PATTERN = re.compile(
    r"(?P<start_year>(?:19|20)\d{2})\s*年?(?P<start_month>\d{1,2})?\s*月?"
    r"\s*(?:-|~|—|–|至|到)\s*"
    r"(?P<end>(?:19|20)\d{2}|至今|现在|目前)\s*年?(?P<end_month>\d{1,2})?\s*月?"
)
EXPERIENCE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*年")
MAJOR_INLINE_PATTERN = re.compile(r"([A-Za-z\u4e00-\u9fa5]{2,30})(?:专业)")
ENGLISH_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-/]{1,30}")


def _dedupe(items):
    seen = set()
    result = []
    for item in items or []:
        if item is None:
            continue
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _normalize_key(text: str) -> str:
    return re.sub(r"[\s:：_-]+", "", (text or "").strip().lower())


def _normalize_skill_key(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fa5+#.]+", "", (text or "").strip().lower())


def _is_heading(line: str) -> bool:
    compact = line.replace(" ", "")
    if len(compact) > 12:
        return False
    return any(compact == alias for aliases in SECTION_ALIASES.values() for alias in aliases)


def _detect_section(line: str) -> str | None:
    compact = line.replace(" ", "")
    for section, aliases in SECTION_ALIASES.items():
        if compact in aliases:
            return section
    return None


def _split_lines(clean_text: str) -> list[str]:
    return [_normalize_space(line) for line in (clean_text or "").splitlines() if _normalize_space(line)]


def _collect_key_values(lines: list[str]) -> dict[str, str]:
    values = {}
    for line in lines:
        if ":" not in line and "：" not in line:
            continue
        parts = re.split(r"[:：]", line, maxsplit=1)
        if len(parts) != 2:
            continue
        key, raw_value = parts
        normalized_key = _normalize_key(key)
        for field, aliases in KEY_ALIASES.items():
            if normalized_key in {_normalize_key(alias) for alias in aliases}:
                values[field] = raw_value.strip()
                break
    return values


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = defaultdict(list)
    current = None
    for line in lines:
        section = _detect_section(line)
        if section:
            current = section
            continue
        if current:
            sections[current].append(line)
    return dict(sections)


def _clean_entity_text(text: str) -> str:
    cleaned = _normalize_space(str(text or ""))
    cleaned = cleaned.strip(",:：;；，。()（）[]【】|/-")
    return cleaned


def _is_valid_text(text: str, min_len: int = 2, max_len: int = 40) -> bool:
    if not text:
        return False
    if len(text) < min_len or len(text) > max_len:
        return False
    if re.search(r"\d{3,}", text):
        return False
    if text.count("?") >= 1:
        return False
    return True


def _entity_values(entities: list[dict], label: str) -> list[str]:
    values = []
    for entity in entities or []:
        if entity.get("label") != label:
            continue
        cleaned = _clean_entity_text(entity.get("text", ""))
        if _is_valid_text(cleaned):
            values.append(cleaned)
    return _dedupe(values)


def _extract_emails(text: str, fallback: str | None = None) -> list[str]:
    values = EMAIL_PATTERN.findall(text or "")
    if fallback:
        values.extend(EMAIL_PATTERN.findall(fallback))
        if "@" in fallback and fallback not in values:
            values.append(fallback)
    return _dedupe(values)


def _extract_phones(text: str, fallback: str | None = None) -> list[str]:
    values = [phone.replace(" ", "") for phone in PHONE_PATTERN.findall(text or "")]
    if fallback:
        values.extend(phone.replace(" ", "") for phone in PHONE_PATTERN.findall(fallback))
        if PHONE_PATTERN.search(fallback):
            values.append(PHONE_PATTERN.search(fallback).group(1).replace(" ", ""))
    return _dedupe(values)


def _extract_degrees(education_lines: list[str], entities: list[dict]) -> list[str]:
    found = []
    for line in education_lines:
        lowered = line.lower()
        for keyword in DEGREE_KEYWORDS:
            if keyword.lower() in lowered:
                if keyword in ("bachelor", "master", "phd"):
                    continue
                found.append(keyword)
    found.extend(_entity_values(entities, "DEGREE"))
    normalized = []
    for item in found:
        lowered = item.lower()
        if lowered == "bachelor":
            normalized.append("本科")
        elif lowered == "master":
            normalized.append("硕士")
        elif lowered == "phd":
            normalized.append("博士")
        elif item == "学士":
            normalized.append("本科")
        elif item == "研究生":
            normalized.append("硕士")
        else:
            normalized.append(item)
    return _dedupe(normalized)


def _extract_majors(education_lines: list[str], entities: list[dict]) -> list[str]:
    majors = []
    for line in education_lines:
        if any(keyword in line for keyword in DEGREE_KEYWORDS):
            left = re.split(r"[|｜/]", line)[0].strip()
            left = re.sub(r"(专业|学历|学位)$", "", left).strip()
            if _is_valid_text(left):
                majors.append(left)
        for match in MAJOR_INLINE_PATTERN.findall(line):
            cleaned = match.strip()
            if _is_valid_text(cleaned):
                majors.append(cleaned)
        for suffix in MAJOR_SUFFIXES:
            if suffix in line:
                majors.append(suffix)
    for value in _entity_values(entities, "MAJOR"):
        if (
            _is_valid_text(value)
            and not re.search(r"\d", value)
            and re.search(r"(学|工程|技术|设计|管理|统计|数学|传播)", value)
        ):
            majors.append(value)
    return _dedupe(majors)


def _extract_schools(education_lines: list[str], entities: list[dict]) -> list[str]:
    schools = []
    for line in education_lines:
        if any(token in line for token in ("大学", "学院", "学校")) and len(line) <= 24:
            schools.append(line)
    for value in _entity_values(entities, "SCHOOL"):
        if any(token in value for token in ("大学", "学院", "学校")):
            schools.append(value)
    return _dedupe(schools)


def _extract_titles(work_lines: list[str], entities: list[dict]) -> list[str]:
    titles = []
    for line in work_lines:
        if any(hint in line for hint in TITLE_HINTS) and len(line) <= 24:
            titles.append(line)
    for value in _entity_values(entities, "TITLE"):
        if any(hint in value for hint in TITLE_HINTS):
            titles.append(value)
    return _dedupe(titles)


def _extract_companies(work_lines: list[str], entities: list[dict]) -> list[str]:
    companies = []
    for line in work_lines:
        if any(hint in line for hint in COMPANY_HINTS) and len(line) <= 24 and "公司规模" not in line:
            companies.append(line)
    companies.extend(_entity_values(entities, "COMPANY"))
    return _dedupe(companies)


def _extract_projects(project_lines: list[str], entities: list[dict]) -> list[str]:
    projects = []
    for line in project_lines:
        if any(hint in line for hint in PROJECT_HINTS) and len(line) <= 40:
            projects.append(line)
    for value in _entity_values(entities, "PROJECT"):
        if any(hint in value for hint in PROJECT_HINTS):
            projects.append(value)
    return _dedupe(projects)


def _skill_tokens_from_line(line: str, section_name: str) -> list[str]:
    cleaned = line.strip()
    if not cleaned or cleaned in SKILL_LINE_SKIP:
        return []
    if any(cleaned.startswith(prefix) for prefix in ("负责", "参与", "贡献", "项目上线", "工作认真")):
        return []

    if section_name in {"project", "work"} and "技术选型" not in cleaned:
        return []

    if "技术选型" in cleaned and ":" in cleaned:
        cleaned = cleaned.split(":", 1)[1].strip()
    if "技术选型" in cleaned and "：" in cleaned:
        cleaned = cleaned.split("：", 1)[1].strip()

    results = []
    for token in ENGLISH_TOKEN_PATTERN.findall(cleaned):
        normalized = token.strip("()[]{}")
        if len(normalized) >= 2:
            results.append(normalized)

    parts = re.split(r"[、,，/|｜；;（）()\s]+", cleaned)
    for part in parts:
        token = part.strip()
        token = re.sub(r"(编程语言|网络框架|图片加载库|数据库|组件|技术栈|跨平台开发)$", "", token).strip()
        if not token or token in SKILL_LINE_SKIP:
            continue
        if re.search(r"\d{4}年", token):
            continue
        if len(token) == 1:
            continue
        if "%" in token or "：" in token or ":" in token:
            continue
        if re.search(r"[A-Za-z]", token):
            if len(token) >= 2:
                results.append(token)
            continue
        if token in KNOWN_CHINESE_SKILLS or any(hint in token for hint in CHINESE_SKILL_HINTS):
            results.append(token)
    return _dedupe(results)


def _extract_skills(sections: dict[str, list[str]], entities: list[dict]) -> list[str]:
    skills = []
    for section_name in ("skills", "project", "work"):
        for line in sections.get(section_name, []):
            skills.extend(_skill_tokens_from_line(line, section_name))
    cleaned = []
    for skill in _dedupe(skills):
        normalized_key = _normalize_skill_key(skill)
        if not normalized_key:
            continue
        if normalized_key in {"sdk29", "500人以下", "2019年7月"}:
            continue
        cleaned.append(skill)
    return _dedupe(cleaned)


def _parse_date_range(text: str):
    match = DATE_RANGE_PATTERN.search(text or "")
    if not match:
        return None
    start_year = int(match.group("start_year"))
    start_month = int(match.group("start_month") or 1)
    end_value = match.group("end")
    if end_value in {"至今", "现在", "目前"}:
        today = date.today()
        end_year = today.year
        end_month = today.month
    else:
        end_year = int(end_value)
        end_month = int(match.group("end_month") or 12)
    if end_year < start_year or start_month < 1 or start_month > 12 or end_month < 1 or end_month > 12:
        return None
    return (start_year, start_month, end_year, end_month)


def _months_between(start_year: int, start_month: int, end_year: int, end_month: int) -> int:
    return max((end_year - start_year) * 12 + (end_month - start_month) + 1, 0)


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _estimate_work_years(lines: list[str]) -> float:
    numeric_ranges = []
    for line in lines:
        parsed = _parse_date_range(line)
        if not parsed:
            continue
        start_year, start_month, end_year, end_month = parsed
        start_index = start_year * 12 + start_month
        end_index = end_year * 12 + end_month
        numeric_ranges.append((start_index, end_index))
    merged = _merge_ranges(numeric_ranges)
    months = sum(end - start + 1 for start, end in merged)
    if not months:
        return 0.0
    return round(months / 12, 1)


def _extract_explicit_experience(value: str | None) -> float:
    if not value:
        return 0.0
    match = EXPERIENCE_PATTERN.search(value)
    return float(match.group(1)) if match else 0.0


def _build_analysis_summary(profile: dict) -> list[str]:
    summary = []
    if profile.get("degrees") or profile.get("majors"):
        degree_text = "、".join(profile.get("degrees") or ["未识别"])
        major_text = "、".join(profile.get("majors") or ["未识别"])
        summary.append(f"教育背景识别为 {degree_text}，专业方向为 {major_text}。")
    if profile.get("experience_years"):
        summary.append(f"根据工作时间区间估算，相关工作年限约为 {profile['experience_years']}。")
    if profile.get("skills"):
        summary.append(f"已提取 {len(profile['skills'])} 项技能关键词，主要包括：{'、'.join(profile['skills'][:6])}。")
    if profile.get("titles") or profile.get("companies"):
        title = "、".join(profile.get("titles")[:2] or ["未识别岗位"])
        company = "、".join(profile.get("companies")[:2] or ["未识别公司"])
        summary.append(f"岗位方向识别为 {title}，相关组织包括 {company}。")
    return summary


def build_profile(clean_text: str, entities: list[dict]):
    lines = _split_lines(clean_text)
    key_values = _collect_key_values(lines)
    sections = _split_sections(lines)

    education_lines = sections.get("education", [])
    work_lines = sections.get("work", [])
    internship_lines = sections.get("internship", [])
    project_lines = sections.get("project", [])

    emails = _extract_emails(clean_text, key_values.get("email"))
    phones = _extract_phones(clean_text, key_values.get("phone"))
    degrees = _extract_degrees(education_lines, entities)
    majors = _extract_majors(education_lines, entities)
    schools = _extract_schools(education_lines, entities)
    titles = _extract_titles(work_lines, entities)
    companies = _extract_companies(work_lines, entities)
    projects = _extract_projects(project_lines, entities)
    skills = _extract_skills(sections, entities)

    work_years = _estimate_work_years(work_lines + internship_lines)
    explicit_experience = _extract_explicit_experience(key_values.get("experience"))
    best_experience = max(work_years, explicit_experience)
    experience_years = f"{best_experience:.1f}年" if best_experience else None

    name = key_values.get("name")
    gender = key_values.get("gender")
    age = key_values.get("age")
    hometown = key_values.get("hometown")

    if not name:
        name_candidates = _entity_values(entities, "NAME")
        name = name_candidates[0] if name_candidates else None
    if not hometown:
        hometown_candidates = _entity_values(entities, "HOMETOWN")
        hometown = hometown_candidates[0] if hometown_candidates else None

    profile = {
        "name": name,
        "gender": gender,
        "age": age,
        "hometown": hometown,
        "emails": emails,
        "phones": phones,
        "degrees": degrees,
        "majors": majors,
        "schools": schools,
        "skills": skills,
        "titles": titles,
        "companies": companies,
        "projects": projects,
        "experience_years": experience_years,
        "raw_sections": {
            "education": education_lines,
            "skills": sections.get("skills", []),
            "work": work_lines,
            "internship": internship_lines,
            "project": project_lines,
        },
        "experience_summary": {
            "work_texts": work_lines,
            "internship_texts": internship_lines,
            "project_texts": project_lines,
            "work_years": best_experience,
        },
    }
    profile["analysis_summary"] = _build_analysis_summary(profile)
    return profile
