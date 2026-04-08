import re


DEGREE_ORDER = {
    "中专": 0,
    "大专": 1,
    "专科": 1,
    "associate": 1,
    "本科": 2,
    "学士": 2,
    "bachelor": 2,
    "硕士": 3,
    "研究生": 3,
    "master": 3,
    "博士": 4,
    "phd": 4,
    "doctor": 4,
}

RELATED_MAJOR_GROUPS = {
    "计算机类": {"计算机科学与技术", "软件工程", "网络工程", "人工智能", "数据科学与大数据技术", "信息安全"},
    "传媒类": {"新闻学", "传播学", "广告学", "广播电视编导", "网络与新媒体"},
    "设计类": {"视觉传达设计", "数字媒体艺术", "艺术设计", "产品设计"},
    "管理类": {"工商管理", "行政管理", "市场营销", "人力资源管理"},
    "Computer Science": {"Computer Science", "Software Engineering", "Information Security", "Artificial Intelligence"},
    "Data Science": {"Data Science", "Statistics", "Applied Mathematics", "Business Analytics"},
    "Marketing": {"Marketing", "Advertising", "Journalism", "New Media"},
    "Business Administration": {"Business Administration", "Management", "Project Management"},
}

SKILL_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+\-#.]{1,30}|[\u4e00-\u9fa5]{2,12}")
YEAR_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*年")


def _split_keywords(value: str):
    if not value:
        return []
    items = re.split(r"[、,，/\s]+", value)
    return [item.strip() for item in items if item.strip()]


def _normalize_text(value: str):
    return (value or "").strip().lower()


def _highest_degree(degrees):
    best = None
    best_order = -1
    for degree in degrees or []:
        normalized_degree = _normalize_text(degree)
        order = DEGREE_ORDER.get(normalized_degree, DEGREE_ORDER.get(degree, -1))
        if order > best_order:
            best_order = order
            best = degree
    return best


def _extract_years(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    matched = YEAR_PATTERN.search(str(value))
    return float(matched.group(1)) if matched else 0


def _skill_score(job_skills, resume_skills):
    if not job_skills:
        return 0, [], []

    normalized_resume = {_normalize_text(item): item for item in resume_skills}
    matched = []
    missing = []
    for skill in job_skills:
        if _normalize_text(skill) in normalized_resume:
            matched.append(skill)
        else:
            missing.append(skill)

    score = round(len(matched) / len(job_skills) * 100, 2) if job_skills else 0
    return score, matched, missing


def _experience_score(job_requirement, profile_raw):
    target_years = _extract_years(job_requirement)
    experience_summary = profile_raw.get("experience_summary", {})
    experience_years = max(
        _extract_years(profile_raw.get("experience_years")),
        _extract_years(experience_summary.get("work_years")),
    )
    evidence = []
    work_texts = experience_summary.get("work_texts", [])
    internship_texts = experience_summary.get("internship_texts", [])
    project_texts = experience_summary.get("project_texts", [])

    if experience_years:
        evidence.append(f"识别到相关经验约 {experience_years:g} 年")

    experience_text = "\n".join(
        work_texts + internship_texts + project_texts
    )
    if experience_text:
        evidence.append("已将工作经历、实习经历和项目经历纳入经验维度参考")

    if target_years <= 0:
        return 70 if experience_text else 30, evidence
    if experience_years >= target_years:
        return 100, evidence
    if experience_years > 0:
        return round(experience_years / target_years * 100, 2), evidence
    if work_texts or internship_texts:
        evidence.append("未识别到明确年限，基于工作/实习内容给予经验基础分")
        return 60, evidence
    if project_texts:
        evidence.append("未识别到明确年限，基于项目经历给予经验参考分")
        return 40, evidence
    return 0, evidence


def _degree_score(job_degree, degrees):
    if not job_degree:
        return 100, ["岗位未设置学历硬性门槛"]

    highest = _highest_degree(degrees)
    if not highest:
        return 0, ["未识别到明确学历信息"]

    highest_order = DEGREE_ORDER.get(_normalize_text(highest), DEGREE_ORDER.get(highest, -1))
    job_order = DEGREE_ORDER.get(_normalize_text(job_degree), DEGREE_ORDER.get(job_degree, -1))
    score = 100 if highest_order >= job_order else 0
    return score, [f"识别到最高学历为 {highest}"]


def _major_score(job_major, majors):
    if not job_major:
        return 100, ["岗位未设置专业硬性门槛"]
    if not majors:
        return 0, ["未识别到明确专业信息"]

    primary_major = majors[0]
    if primary_major == job_major:
        return 100, [f"专业与岗位要求完全一致：{primary_major}"]

    if job_major in RELATED_MAJOR_GROUPS:
        if primary_major in RELATED_MAJOR_GROUPS[job_major]:
            return 100, [f"专业属于岗位要求类别：{job_major}"]

    for group_name, majors_in_group in RELATED_MAJOR_GROUPS.items():
        if job_major in majors_in_group and primary_major in majors_in_group:
            return 80, [f"专业属于同一相关学科方向：{group_name}"]

    return 0, [f"识别专业为 {primary_major}，与岗位要求相关度较低"]


def _collect_resume_skills(profile_raw):
    skills = set(profile_raw.get("skills") or [])
    text_blocks = "\n".join(
        profile_raw.get("experience_summary", {}).get("work_texts", [])
        + profile_raw.get("experience_summary", {}).get("internship_texts", [])
        + profile_raw.get("experience_summary", {}).get("project_texts", [])
    )
    for match in SKILL_PATTERN.findall(text_blocks):
        token = match.strip()
        if len(token) >= 2:
            skills.add(token)
    return sorted(skills, key=lambda item: item.lower())


def _build_fairness_notes():
    return [
        "姓名、性别、年龄、籍贯已在评分前脱敏，不参与总分计算。",
        "院校信息仅用于展示，不纳入总分，以减少标签偏置。",
    ]


def calculate_match_result(job, profile_raw, profile_masked):
    job_skills = _split_keywords(job.skill_requirement or "")
    resume_skills = _collect_resume_skills(profile_raw)
    raw_skill_score, matched_skills, missing_skills = _skill_score(job_skills, resume_skills)
    raw_experience_score, experience_evidence = _experience_score(job.experience_requirement, profile_raw)
    raw_degree_score, degree_evidence = _degree_score(job.degree_requirement, profile_raw.get("degrees") or [])
    raw_major_score, major_evidence = _major_score(job.major_requirement, profile_raw.get("majors") or [])

    dimension_scores = {
        "skills": {
            "raw_score": raw_skill_score,
            "weighted_score": round(raw_skill_score * float(job.skill_weight), 2),
            "evidence": [f"命中技能：{', '.join(matched_skills)}"] if matched_skills else ["暂无明确技能命中"],
        },
        "experience": {
            "raw_score": raw_experience_score,
            "weighted_score": round(raw_experience_score * float(job.experience_weight), 2),
            "evidence": experience_evidence,
        },
        "degree": {
            "raw_score": raw_degree_score,
            "weighted_score": round(raw_degree_score * float(job.degree_weight), 2),
            "evidence": degree_evidence,
        },
        "major": {
            "raw_score": raw_major_score,
            "weighted_score": round(raw_major_score * float(job.major_weight), 2),
            "evidence": major_evidence,
        },
    }

    total_score = round(sum(item["weighted_score"] for item in dimension_scores.values()), 2)
    explanations = [
        f"技能匹配得分 {dimension_scores['skills']['raw_score']}，经验匹配得分 {dimension_scores['experience']['raw_score']}。",
        f"学历匹配得分 {dimension_scores['degree']['raw_score']}，专业匹配得分 {dimension_scores['major']['raw_score']}。",
    ]
    if missing_skills:
        explanations.append(f"仍缺少部分目标技能：{', '.join(missing_skills[:6])}")

    return {
        "total_score": total_score,
        "dimension_scores": dimension_scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "final_explanations": explanations,
        "fairness_notes": _build_fairness_notes(),
        "profile_masked": profile_masked,
    }
