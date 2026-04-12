import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RoleBlueprint:
    role_id: str
    category: str
    title: str
    majors: list[str]
    schools: list[str]
    companies: list[str]
    projects: list[str]
    skill_sets: list[list[str]]
    degrees: list[str]
    years: list[str]


BLUEPRINTS = [
    RoleBlueprint("backend", "tech", "后端开发工程师", ["计算机科学与技术", "软件工程"], ["华中科技大学", "武汉理工大学", "中南大学"], ["云帆软件", "星河科技", "迅捷信息"], ["企业审批平台", "校园招聘系统", "订单履约中心"], [["Python", "FastAPI", "MySQL", "Docker"], ["Java", "Spring Boot", "Redis", "MySQL"]], ["本科", "硕士"], ["2年开发经验", "3年开发经验", "4年开发经验"]),
    RoleBlueprint("frontend", "tech", "前端开发工程师", ["软件工程", "数字媒体技术"], ["武汉大学", "电子科技大学", "重庆邮电大学"], ["灵犀科技", "云上未来", "极光互动"], ["运营看板系统", "客户门户网站", "招聘小程序"], [["Vue", "JavaScript", "TypeScript", "Element Plus"], ["React", "Vite", "ECharts", "CSS"]], ["本科"], ["1年前端经验", "2年前端经验", "3年前端经验"]),
    RoleBlueprint("qa", "tech", "测试开发工程师", ["软件工程", "信息管理与信息系统"], ["南昌大学", "山东大学", "安徽大学"], ["恒准软件", "鸣远信息", "景澄科技"], ["接口自动化平台", "回归测试平台", "支付测试项目"], [["Python", "Pytest", "Postman", "Jenkins"], ["Java", "Selenium", "SQL", "Linux"]], ["本科"], ["1年测试经验", "2年测试经验", "3年测试经验"]),
    RoleBlueprint("algorithm", "tech", "算法工程师", ["人工智能", "计算机技术"], ["北京邮电大学", "哈尔滨工业大学", "华南理工大学"], ["深蓝智能", "矩阵算法", "文心数据"], ["简历实体识别系统", "文本分类平台", "推荐排序服务"], [["PyTorch", "BERT", "CRF", "NLP"], ["Python", "Transformers", "Pandas", "CUDA"]], ["硕士"], ["1年算法实习经验", "2年算法经验", "3年算法经验"]),
    RoleBlueprint("data", "tech", "数据分析师", ["统计学", "数据科学与大数据技术"], ["暨南大学", "东北财经大学", "湖南师范大学"], ["北辰数据", "观澜科技", "增长引擎"], ["用户增长分析平台", "经营分析看板", "会员画像项目"], [["SQL", "Python", "Power BI", "Pandas"], ["Excel", "Tableau", "SQL", "数据分析"]], ["本科", "硕士"], ["1年分析经验", "2年分析经验", "3年分析经验"]),
    RoleBlueprint("product", "product", "产品经理", ["工业工程", "工商管理"], ["武汉大学", "中南大学", "厦门大学"], ["领航科技", "明日企服", "知行网络"], ["校园招聘系统", "商家工作台", "内部协同平台"], [["Axure", "PRD撰写", "需求分析", "原型设计"], ["用户研究", "流程设计", "数据分析", "Visio"]], ["本科", "硕士"], ["1年产品经验", "2年产品经验", "3年产品经验"]),
    RoleBlueprint("project", "product", "项目经理", ["项目管理", "物流管理"], ["中国地质大学", "西南大学", "武汉科技大学"], ["安达供应链", "启航软件", "恒川系统"], ["ERP实施项目", "仓储协同平台", "数字化转型项目"], [["项目排期", "需求沟通", "风险控制", "PPT汇报"], ["流程梳理", "客户培训", "SQL", "Visio"]], ["本科"], ["2年项目经验", "3年项目经验", "4年项目经验"]),
    RoleBlueprint("content_ops", "operations", "内容运营专员", ["新闻传播学", "广告学"], ["华中师范大学", "湖南大学", "福建师范大学"], ["青禾文化", "橙果传媒", "禾木品牌"], ["品牌公众号改版项目", "短视频账号项目", "社媒增长计划"], [["内容策划", "文案撰写", "数据复盘", "小红书运营"], ["公众号运营", "短视频剪辑", "Photoshop", "用户增长"]], ["本科"], ["1年运营经验", "2年运营经验", "3年运营经验"]),
    RoleBlueprint("ecommerce_ops", "operations", "电商运营专员", ["电子商务", "市场营销"], ["苏州大学", "广东财经大学", "浙江工商大学"], ["远航电商", "云图零售", "千帆商贸"], ["双十一促销项目", "店铺拉新计划", "直播转化项目"], [["店铺运营", "数据分析", "详情页策划", "客服协同"], ["活动策划", "直播运营", "Excel", "用户增长"]], ["本科"], ["1年电商经验", "2年电商经验", "3年电商经验"]),
    RoleBlueprint("design", "design", "UI设计师", ["视觉传达设计", "数字媒体艺术"], ["湖北美术学院", "广州美术学院", "江南大学"], ["象限设计", "澜图互动", "一度创意"], ["招聘官网视觉升级", "数据大屏设计", "移动端改版项目"], [["Figma", "Photoshop", "Illustrator", "原型设计"], ["Sketch", "AE", "版式设计", "用户体验"]], ["本科"], ["1年设计经验", "2年设计经验", "3年设计经验"]),
    RoleBlueprint("hr", "functional", "招聘专员", ["人力资源管理", "工商管理"], ["西南大学", "安徽大学", "江西财经大学"], ["智聘网络", "聚贤人力", "悦才咨询"], ["校招流程优化项目", "岗位画像梳理项目", "招聘数据看板"], [["招聘协调", "Excel", "沟通协作", "流程优化"], ["面试安排", "数据统计", "人才筛选", "报告撰写"]], ["本科"], ["1年招聘经验", "2年招聘经验", "3年招聘经验"]),
    RoleBlueprint("finance", "functional", "财务专员", ["会计学", "财务管理"], ["东北财经大学", "江西财经大学", "广东金融学院"], ["恒信财务", "金穗咨询", "汇智企服"], ["费用报销流程优化", "月结分析项目", "预算执行跟踪项目"], [["Excel", "财务报表", "用友", "数据核对"], ["金蝶", "预算分析", "台账整理", "沟通协作"]], ["本科"], ["1年财务经验", "2年财务经验", "3年财务经验"]),
]

SURNAME_POOL = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜戚谢邹喻")
GIVEN_LEFT = list("子文书明宇安泽景浩若思嘉俊晨沐钰知可亦星雨清承语天乐欣奕")
GIVEN_RIGHT = list("轩涵宁彤玥言辰阳帆然婷昕悦琳萱琪楠睿航瑶瑜磊锋毅珊雅萌")
HOME_POOL = ["湖北武汉", "湖南长沙", "河南郑州", "江西南昌", "安徽合肥", "广东深圳", "江苏苏州", "浙江杭州", "四川成都", "福建厦门", "山东济南", "河北石家庄"]
EMAIL_DOMAINS = ["example.com", "mail.com", "resume.cn", "jobmail.cn"]


def _build_names(total: int) -> list[str]:
    names = []
    for surname in SURNAME_POOL:
        for left in GIVEN_LEFT:
            for right in GIVEN_RIGHT:
                if left == right:
                    continue
                names.append(f"{surname}{left}{right}")
                if len(names) >= total:
                    return names
    return names[:total]


def _make_phone(index: int) -> str:
    return f"13{(800000000 + index):09d}"


def _make_email(name: str, index: int) -> str:
    stem = f"{name.encode('utf-8').hex()[:8]}{index:03d}"
    return f"{stem}@{EMAIL_DOMAINS[index % len(EMAIL_DOMAINS)]}"


def _estimate_age(year_text: str, degree: str, index: int) -> str:
    years_value = next((int(char) for char in year_text if char.isdigit()), 1)
    base_age = 21 if degree == "本科" else 23
    return str(base_age + years_value + (index % 3))


def build_profiles(total_profiles: int = 150, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    names = _build_names(total_profiles)
    blueprint_order = [BLUEPRINTS[index % len(BLUEPRINTS)] for index in range(total_profiles)]
    rng.shuffle(blueprint_order)

    profiles = []
    for index in range(total_profiles):
        blueprint = blueprint_order[index]
        degree = blueprint.degrees[index % len(blueprint.degrees)]
        year_text = blueprint.years[index % len(blueprint.years)]
        profiles.append(
            {
                "profile_id": f"profile_{index:03d}",
                "role_id": blueprint.role_id,
                "category": blueprint.category,
                "name": names[index],
                "gender": "男" if index % 2 == 0 else "女",
                "age": _estimate_age(year_text, degree, index),
                "hometown": HOME_POOL[index % len(HOME_POOL)],
                "school": blueprint.schools[index % len(blueprint.schools)],
                "degree": degree,
                "major": blueprint.majors[index % len(blueprint.majors)],
                "company": blueprint.companies[index % len(blueprint.companies)],
                "title": blueprint.title,
                "project": blueprint.projects[index % len(blueprint.projects)],
                "skills": blueprint.skill_sets[index % len(blueprint.skill_sets)],
                "experience_years": year_text,
                "phone": _make_phone(index + 1),
                "email": _make_email(names[index], index + 1),
            }
        )
    return profiles


def _sample_id(split: str, profile_id: str, template_id: int) -> str:
    return hashlib.md5(f"{split}-{profile_id}-{template_id}".encode("utf-8")).hexdigest()[:12]


def _segments_to_sample(segments: list[tuple[str, str | None]]) -> tuple[str, list[dict]]:
    text_parts = []
    entities = []
    cursor = 0
    for value, label in segments:
        text_parts.append(value)
        if label:
            entities.append({"start": cursor, "end": cursor + len(value), "label": label})
        cursor += len(value)
    return "".join(text_parts), entities


def _render_template(profile: dict, template_id: int) -> tuple[str, list[dict]]:
    s0, s1, s2, s3 = profile["skills"]
    title = profile["title"]
    templates = {
        0: [("候选人", None), (profile["name"], "NAME"), ("，", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁，来自", None), (profile["hometown"], "HOMETOWN"), ("。毕业于", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，专业为", None), (profile["major"], "MAJOR"), ("。曾在", None), (profile["company"], "COMPANY"), ("担任", None), (title, "TITLE"), ("，累计", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。主导", None), (profile["project"], "PROJECT"), ("，熟练掌握", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("和", None), (s3, "SKILL"), ("。联系电话", None), (profile["phone"], "PHONE"), ("，邮箱", None), (profile["email"], "EMAIL"), ("。", None)],
        1: [("求职意向：", None), (title, "TITLE"), ("\n基本信息：", None), (profile["name"], "NAME"), ("，", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁，", None), (profile["hometown"], "HOMETOWN"), ("。\n教育背景：", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，", None), (profile["major"], "MAJOR"), ("。\n工作经历：曾在", None), (profile["company"], "COMPANY"), ("从事", None), (title, "TITLE"), ("相关工作，拥有", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。\n项目经历：参与", None), (profile["project"], "PROJECT"), ("。\n核心技能：", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("、", None), (s3, "SKILL"), ("。\n联系方式：", None), (profile["phone"], "PHONE"), (" / ", None), (profile["email"], "EMAIL")],
        2: [(profile["name"], "NAME"), ("希望应聘", None), (title, "TITLE"), ("岗位。", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁，籍贯", None), (profile["hometown"], "HOMETOWN"), ("。", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("毕业，专业方向为", None), (profile["major"], "MAJOR"), ("。此前在", None), (profile["company"], "COMPANY"), ("担任", None), (title, "TITLE"), ("，沉淀了", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。代表项目是", None), (profile["project"], "PROJECT"), ("，日常使用", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("与", None), (s3, "SKILL"), ("。可通过", None), (profile["phone"], "PHONE"), ("或", None), (profile["email"], "EMAIL"), ("联系。", None)],
        3: [("个人简介：", None), (profile["name"], "NAME"), ("，", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁。教育背景为", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，主修", None), (profile["major"], "MAJOR"), ("，籍贯", None), (profile["hometown"], "HOMETOWN"), ("。职业方向聚焦", None), (title, "TITLE"), ("，曾在", None), (profile["company"], "COMPANY"), ("参与", None), (profile["project"], "PROJECT"), ("，积累", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。技能侧重", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("、", None), (s3, "SKILL"), ("。联系方式：", None), (profile["phone"], "PHONE"), ("，", None), (profile["email"], "EMAIL"), ("。", None)],
        4: [("简历摘要\n姓名：", None), (profile["name"], "NAME"), ("\n性别：", None), (profile["gender"], "GENDER"), ("\n年龄：", None), (profile["age"], "AGE"), ("\n籍贯：", None), (profile["hometown"], "HOMETOWN"), ("\n毕业院校：", None), (profile["school"], "SCHOOL"), ("\n学历：", None), (profile["degree"], "DEGREE"), ("\n专业：", None), (profile["major"], "MAJOR"), ("\n目标岗位：", None), (title, "TITLE"), ("\n工作经历：在", None), (profile["company"], "COMPANY"), ("完成", None), (profile["project"], "PROJECT"), ("，具备", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("\n技能标签：", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("、", None), (s3, "SKILL"), ("\n电话：", None), (profile["phone"], "PHONE"), ("\n邮箱：", None), (profile["email"], "EMAIL")],
        5: [(profile["name"], "NAME"), ("的教育背景为", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，专业", None), (profile["major"], "MAJOR"), ("。她/他来自", None), (profile["hometown"], "HOMETOWN"), ("，目前年龄", None), (profile["age"], "AGE"), ("岁，性别", None), (profile["gender"], "GENDER"), ("。在", None), (profile["company"], "COMPANY"), ("任职期间承担", None), (title, "TITLE"), ("职责，累计", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("，代表成果为", None), (profile["project"], "PROJECT"), ("。擅长", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("和", None), (s3, "SKILL"), ("。电话", None), (profile["phone"], "PHONE"), ("，邮箱", None), (profile["email"], "EMAIL"), ("。", None)],
        6: [("职业标签：", None), (title, "TITLE"), ("\n候选人", None), (profile["name"], "NAME"), ("，", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁，", None), (profile["hometown"], "HOMETOWN"), ("。\n毕业于", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，专业", None), (profile["major"], "MAJOR"), ("。\n历任单位：", None), (profile["company"], "COMPANY"), ("。\n项目亮点：", None), (profile["project"], "PROJECT"), ("。\n经验沉淀：", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。\n技能结构：", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("、", None), (s3, "SKILL"), ("。\n联系方式：", None), (profile["phone"], "PHONE"), ("；", None), (profile["email"], "EMAIL")],
        7: [("如果岗位需要", None), (title, "TITLE"), ("候选人，可以优先关注", None), (profile["name"], "NAME"), ("。其毕业于", None), (profile["school"], "SCHOOL"), (profile["degree"], "DEGREE"), ("，专业是", None), (profile["major"], "MAJOR"), ("；", None), (profile["gender"], "GENDER"), ("，", None), (profile["age"], "AGE"), ("岁，籍贯", None), (profile["hometown"], "HOMETOWN"), ("。在", None), (profile["company"], "COMPANY"), ("期间围绕", None), (profile["project"], "PROJECT"), ("展开工作，累计拥有", None), (profile["experience_years"], "EXPERIENCE_YEARS"), ("。技术或工具栈包括", None), (s0, "SKILL"), ("、", None), (s1, "SKILL"), ("、", None), (s2, "SKILL"), ("以及", None), (s3, "SKILL"), ("。联系电话", None), (profile["phone"], "PHONE"), ("，电子邮箱", None), (profile["email"], "EMAIL"), ("。", None)],
    }
    return _segments_to_sample(templates[template_id])


def split_profiles(profiles: list[dict], seed: int = 42) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    grouped = defaultdict(list)
    for profile in profiles:
        grouped[profile["role_id"]].append(profile)

    split_map = {"train": [], "dev": [], "test": []}
    for role_profiles in grouped.values():
        rng.shuffle(role_profiles)
        total = len(role_profiles)
        train_count = max(1, math.floor(total * 0.7))
        dev_count = max(1, math.floor(total * 0.15))
        if train_count + dev_count >= total:
            dev_count = 1
        test_count = total - train_count - dev_count
        if test_count <= 0:
            test_count = 1
            train_count = max(1, train_count - 1)
        split_map["train"].extend(role_profiles[:train_count])
        split_map["dev"].extend(role_profiles[train_count : train_count + dev_count])
        split_map["test"].extend(role_profiles[train_count + dev_count : train_count + dev_count + test_count])
    return split_map


def build_resume_corpus(seed: int = 42, total_profiles: int = 150, templates_per_profile: int = 8) -> dict:
    profiles = build_profiles(total_profiles=total_profiles, seed=seed)
    split_map = split_profiles(profiles, seed=seed)
    corpus = {"train": [], "dev": [], "test": []}
    source_manifest = []
    dataset_manifest = {"profiles": len(profiles), "templates_per_profile": templates_per_profile, "splits": {}}

    for split, split_profiles_list in split_map.items():
        label_counter = Counter()
        source_counter = Counter()
        lengths = []
        for profile in split_profiles_list:
            for template_id in range(templates_per_profile):
                text, entities = _render_template(profile, template_id)
                corpus[split].append({"text": text, "entities": entities})
                label_counter.update(entity["label"] for entity in entities)
                lengths.append(len(text))
                source_type = "self_written" if template_id in {0, 1} else "generated_reviewed"
                source_counter[source_type] += 1
                source_manifest.append(
                    {
                        "sample_id": _sample_id(split, profile["profile_id"], template_id),
                        "split": split,
                        "profile_id": profile["profile_id"],
                        "role_id": profile["role_id"],
                        "category": profile["category"],
                        "template_id": template_id,
                        "source_type": source_type,
                    }
                )
        dataset_manifest["splits"][split] = {
            "samples": len(corpus[split]),
            "avg_length": round(sum(lengths) / max(len(lengths), 1), 2),
            "max_length": max(lengths) if lengths else 0,
            "label_distribution": dict(sorted(label_counter.items())),
            "source_breakdown": dict(sorted(source_counter.items())),
        }
    return {"corpus": corpus, "source_manifest": source_manifest, "dataset_manifest": dataset_manifest}


def write_jsonl(path: Path, samples: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in samples) + "\n", encoding="utf-8")
