def normalize_text(value):
    return (value or "").strip().lower()


def degree_score_raw(job_degree, resume_degree):
    if not job_degree or not resume_degree:
        return 0

    degree_order = {
        "专科": 1,
        "大专": 1,
        "本科": 2,
        "硕士": 3,
        "研究生": 3,
        "博士": 4
    }

    job_value = degree_order.get(job_degree, 0)
    resume_value = degree_order.get(resume_degree, 0)

    if resume_value >= job_value and job_value > 0:
        return 100
    return 0


def skill_score_raw(job_skills_text, resume_skills):
    if not job_skills_text:
        return 0

    job_skills = []
    for item in job_skills_text.replace("，", ",").split(","):
        skill = item.strip()
        if skill:
            job_skills.append(skill)

    if not job_skills or not resume_skills:
        return 0

    matched = 0
    resume_skills_lower = [normalize_text(s) for s in resume_skills]

    for skill in job_skills:
        if normalize_text(skill) in resume_skills_lower:
            matched += 1

    return round(matched / len(job_skills) * 100, 2)


def major_score_raw(job_major, resume_major):
    if not job_major or not resume_major:
        return 0

    job_major = job_major.strip()
    resume_major = resume_major.strip()

    if job_major == resume_major:
        return 100

    tech_related = [
        "计算机科学与技术",
        "软件工程",
        "网络工程",
        "人工智能",
        "数据科学与大数据技术",
        "电子信息工程",
        "通信工程",
        "自动化"
    ]

    management_related = [
        "工商管理",
        "行政管理",
        "项目管理",
        "信息管理与信息系统"
    ]

    if "计算机" in job_major or "软件" in job_major or job_major == "计算机类":
        if resume_major in tech_related:
            return 80

    if "管理" in job_major or job_major == "管理类":
        if resume_major in management_related:
            return 80

    return 0


def get_weight_config(job_type):
    job_type = normalize_text(job_type)

    if "技术" in job_type or "开发" in job_type or "后端" in job_type or "前端" in job_type:
        return {
            "skill_weight": 0.6,
            "degree_weight": 0.2,
            "major_weight": 0.2
        }

    if "管理" in job_type:
        return {
            "skill_weight": 0.3,
            "degree_weight": 0.4,
            "major_weight": 0.3
        }

    return {
        "skill_weight": 0.5,
        "degree_weight": 0.25,
        "major_weight": 0.25
    }


def calculate_match_score(job, extracted_resume):
    raw_skill_score = skill_score_raw(job.skill_requirement, extracted_resume.get("skills", []))
    raw_degree_score = degree_score_raw(job.degree_requirement, extracted_resume.get("degree"))
    raw_major_score = major_score_raw(job.major_requirement, extracted_resume.get("major"))

    weights = get_weight_config(job.job_type)

    weighted_skill_score = round(raw_skill_score * weights["skill_weight"], 2)
    weighted_degree_score = round(raw_degree_score * weights["degree_weight"], 2)
    weighted_major_score = round(raw_major_score * weights["major_weight"], 2)

    total_score = round(
        weighted_skill_score + weighted_degree_score + weighted_major_score,
        2
    )

    return {
        "raw_skill_score": raw_skill_score,
        "raw_degree_score": raw_degree_score,
        "raw_major_score": raw_major_score,
        "skill_score": weighted_skill_score,
        "degree_score": weighted_degree_score,
        "major_score": weighted_major_score,
        "total_score": total_score,
        "skill_weight": weights["skill_weight"],
        "degree_weight": weights["degree_weight"],
        "major_weight": weights["major_weight"]
    }