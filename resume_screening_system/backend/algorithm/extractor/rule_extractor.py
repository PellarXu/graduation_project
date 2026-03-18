import re

PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

DEGREE_KEYWORDS = ["博士", "硕士", "本科", "大专", "专科", "研究生"]

MAJOR_KEYWORDS = [
    "计算机科学与技术",
    "软件工程",
    "网络工程",
    "人工智能",
    "数据科学与大数据技术",
    "信息管理与信息系统",
    "电子信息工程",
    "通信工程",
    "自动化",
    "工商管理",
    "行政管理",
    "项目管理",
    "艺术设计"
]

SKILL_KEYWORDS = [
    "Python", "Java", "C++", "C", "Go", "MySQL", "SQL", "FastAPI",
    "Flask", "Django", "Vue", "JavaScript", "TypeScript", "HTML",
    "CSS", "Linux", "Redis", "Git", "Spring", "PyTorch", "TensorFlow",
    "沟通", "管理", "文档", "Excel"
]


def extract_phone(text: str):
    match = PHONE_PATTERN.search(text or "")
    return match.group() if match else None


def extract_email(text: str):
    match = EMAIL_PATTERN.search(text or "")
    return match.group() if match else None


def extract_degree(text: str):
    for degree in DEGREE_KEYWORDS:
        if degree in (text or ""):
            return degree
    return None


def extract_major(text: str):
    text = text or ""
    for major in MAJOR_KEYWORDS:
        if major in text:
            return major
    return None


def deduplicate_skills(skills):
    sorted_skills = sorted(set(skills), key=lambda x: len(x), reverse=True)
    result = []

    for skill in sorted_skills:
        should_add = True
        for kept in result:
            if skill.lower() in kept.lower() and skill.lower() != kept.lower():
                should_add = False
                break
        if should_add:
            result.append(skill)

    return sorted(result, key=lambda x: x.lower())


def extract_skills(text: str):
    text = text or ""
    result = []

    for skill in SKILL_KEYWORDS:
        if skill.lower() in text.lower():
            result.append(skill)

    return deduplicate_skills(result)


def extract_resume_info(text: str):
    return {
        "phone": extract_phone(text),
        "email": extract_email(text),
        "degree": extract_degree(text),
        "major": extract_major(text),
        "skills": extract_skills(text),
    }