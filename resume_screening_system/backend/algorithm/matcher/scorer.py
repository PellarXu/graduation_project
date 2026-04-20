from __future__ import annotations

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
    "计算机类": {
        "计算机科学与技术",
        "软件工程",
        "网络工程",
        "信息安全",
        "人工智能",
        "数据科学与大数据技术",
        "物联网工程",
        "电子信息工程",
        "通信工程",
        "自动化",
    },
    "数据类": {"数据科学与大数据技术", "统计学", "数学与应用数学", "应用数学", "商业分析"},
    "传媒类": {"新闻学", "传播学", "广告学", "广播电视编导", "网络与新媒体"},
    "设计类": {"视觉传达设计", "数字媒体艺术", "艺术设计", "产品设计"},
    "管理类": {"工商管理", "行政管理", "市场营销", "人力资源管理"},
}

SKILL_SPLIT_PATTERN = re.compile(r"[、,，;；/|｜\s]+")
EXPERIENCE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*年")


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_skill(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fa5+#.]+", "", _normalize_text(value))


def _split_keywords(value: str):
    return [item.strip() for item in SKILL_SPLIT_PATTERN.split(value or "") if item.strip()]


def _highest_degree(degrees):
    best = None
    best_order = -1
    for degree in degrees or []:
        normalized = _normalize_text(degree)
        order = DEGREE_ORDER.get(normalized, DEGREE_ORDER.get(degree, -1))
        if order > best_order:
            best = degree
            best_order = order
    return best, best_order


def _parse_years(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    matched = EXPERIENCE_PATTERN.search(str(value))
    return float(matched.group(1)) if matched else 0.0


def _collect_resume_skills(profile_raw):
    skills = []
    for item in profile_raw.get("skills") or []:
        if item:
            skills.append(item)

    for group in (profile_raw.get("experience_summary") or {}).values():
        if not isinstance(group, list):
            continue
        for line in group:
            if "技术选型" not in line:
                continue
            line = line.split(":", 1)[1] if ":" in line else line.split("：", 1)[1] if "：" in line else line
            skills.extend(_split_keywords(line))

    deduped = []
    seen = set()
    for skill in skills:
        normalized = _normalize_skill(skill)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(skill.strip())
    return deduped


def _skill_score(job_skills, resume_skills):
    if not job_skills:
        return 100.0, [], [], ["岗位未设置技能硬性要求。"]

    normalized_resume = {_normalize_skill(skill): skill for skill in resume_skills}
    matched = []
    missing = []
    for job_skill in job_skills:
        normalized_job = _normalize_skill(job_skill)
        if not normalized_job:
            continue
        if normalized_job in normalized_resume:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    score = round(len(matched) / len(job_skills) * 100, 2) if job_skills else 100.0
    evidence = [
        f"岗位要求技能 {len(job_skills)} 项，当前命中 {len(matched)} 项。",
        f"命中技能：{'、'.join(matched) if matched else '暂无明确命中'}。",
    ]
    if missing:
        evidence.append(f"仍缺少的关键技能：{'、'.join(missing[:6])}。")
    return score, matched, missing, evidence


def _experience_score(job_requirement, profile_raw):
    target_years = _parse_years(job_requirement)
    experience_summary = profile_raw.get("experience_summary", {}) or {}
    experience_years = max(
        _parse_years(profile_raw.get("experience_years")),
        _parse_years(experience_summary.get("work_years")),
    )
    evidence = []

    if experience_years:
        evidence.append(f"根据工作时间区间估算，相关工作年限约为 {experience_years:.1f} 年。")
    else:
        evidence.append("未识别到稳定的工作时间区间。")

    if target_years <= 0:
        if experience_years > 0:
            return 80.0, evidence
        return 50.0, evidence

    evidence.append(f"岗位要求工作经验约 {target_years:g} 年。")
    if experience_years >= target_years:
        evidence.append("工作年限达到或超过岗位要求。")
        return 100.0, evidence
    if experience_years > 0:
        evidence.append("工作年限低于岗位要求，因此按比例扣分。")
        return round(experience_years / target_years * 100, 2), evidence
    return 0.0, evidence


def _degree_score(job_degree, degrees):
    if not job_degree:
        return 100.0, ["岗位未设置学历硬性门槛。"]

    highest, highest_order = _highest_degree(degrees)
    _, target_order = _highest_degree([job_degree])
    if highest is None:
        return 0.0, ["未识别到明确学历信息。"]

    evidence = [f"识别到最高学历为 {highest}。", f"岗位要求学历为 {job_degree}。"]
    if highest_order >= target_order >= 0:
        evidence.append("学历满足岗位要求。")
        return 100.0, evidence
    if highest_order >= 0 and target_order >= 0:
        gap = max(target_order - highest_order, 0)
        score = max(20.0, 100.0 - gap * 35.0)
        evidence.append("学历低于岗位要求，因此进行扣分。")
        return score, evidence
    return 60.0, evidence


def _major_groups_for(major: str):
    matched_groups = set()
    for group_name, majors in RELATED_MAJOR_GROUPS.items():
        if major == group_name or major in majors:
            matched_groups.add(group_name)
    return matched_groups


def _major_score(job_major, majors):
    if not job_major:
        return 100.0, ["岗位未设置专业硬性门槛。"]
    if not majors:
        return 0.0, ["未识别到明确专业信息。"]

    evidence = [f"识别到的专业：{'、'.join(majors[:3])}。", f"岗位要求专业方向：{job_major}。"]

    if job_major in majors:
        evidence.append("专业与岗位要求完全一致。")
        return 100.0, evidence

    job_groups = _major_groups_for(job_major)
    for major in majors:
        if major in RELATED_MAJOR_GROUPS.get(job_major, set()):
            evidence.append(f"{major} 属于 {job_major} 范畴，判定为高相关。")
            return 95.0, evidence

    for major in majors:
        major_groups = _major_groups_for(major)
        if job_groups & major_groups:
            shared_group = next(iter(job_groups & major_groups))
            evidence.append(f"{major} 与岗位要求同属 {shared_group} 方向，判定为相关专业。")
            return 85.0, evidence

    evidence.append("识别到的专业与岗位要求相关性较低。")
    return 0.0, evidence


def _build_fairness_notes():
    return [
        "姓名、性别、年龄、籍贯、电话、邮箱会在评分前脱敏，不参与总分计算。",
        "院校与项目方向仅用于人工复核展示，不纳入总分，以降低标签偏置。",
        "总分仅由技能、经验、学历、专业四个维度按岗位权重加权得到。",
    ]


def _build_final_explanations(job, dimension_scores, matched_skills, missing_skills, profile_raw):
    explanations = [
        (
            f"总分由技能、经验、学历、专业四个维度组成，当前岗位权重分别为 "
            f"{float(job.skill_weight):.2f} / {float(job.experience_weight):.2f} / "
            f"{float(job.degree_weight):.2f} / {float(job.major_weight):.2f}。"
        )
    ]

    best_dimension = max(dimension_scores.items(), key=lambda item: item[1]["raw_score"])
    weakest_dimension = min(dimension_scores.items(), key=lambda item: item[1]["raw_score"])
    label_map = {"skills": "技能", "experience": "经验", "degree": "学历", "major": "专业"}
    explanations.append(
        f"当前最强维度是{label_map[best_dimension[0]]}（原始分 {best_dimension[1]['raw_score']}），"
        f"相对短板是{label_map[weakest_dimension[0]]}（原始分 {weakest_dimension[1]['raw_score']}）。"
    )

    if profile_raw.get("degrees"):
        explanations.append(f"学历判断依据为：{'、'.join(profile_raw['degrees'])}。")
    if profile_raw.get("majors"):
        explanations.append(f"专业判断依据为：{'、'.join(profile_raw['majors'])}。")
    if matched_skills:
        explanations.append(f"已明确命中的技能包括：{'、'.join(matched_skills)}。")
    if missing_skills:
        explanations.append(f"当前仍缺少的关键技能包括：{'、'.join(missing_skills[:6])}。")
    if profile_raw.get("experience_years"):
        explanations.append(f"经验判断依据为：约 {profile_raw['experience_years']} 的工作时间跨度。")
    return explanations


def calculate_match_result(job, profile_raw, profile_masked):
    job_skills = _split_keywords(job.skill_requirement or "")
    resume_skills = _collect_resume_skills(profile_raw)

    raw_skill_score, matched_skills, missing_skills, skill_evidence = _skill_score(job_skills, resume_skills)
    raw_experience_score, experience_evidence = _experience_score(job.experience_requirement, profile_raw)
    raw_degree_score, degree_evidence = _degree_score(job.degree_requirement, profile_raw.get("degrees") or [])
    raw_major_score, major_evidence = _major_score(job.major_requirement, profile_raw.get("majors") or [])

    dimension_scores = {
        "skills": {
            "raw_score": raw_skill_score,
            "weighted_score": round(raw_skill_score * float(job.skill_weight), 2),
            "evidence": skill_evidence,
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
    explanations = _build_final_explanations(job, dimension_scores, matched_skills, missing_skills, profile_raw)

    return {
        "total_score": total_score,
        "dimension_scores": dimension_scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "final_explanations": explanations,
        "fairness_notes": _build_fairness_notes(),
        "profile_masked": profile_masked,
    }
