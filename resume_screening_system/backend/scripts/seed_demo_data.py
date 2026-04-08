from pathlib import Path
import json
import urllib.request

import httpx
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


API = "http://127.0.0.1:8000"
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "demo_seed" / "resumes"
DATA_DIR.mkdir(parents=True, exist_ok=True)


JOBS = [
    {
        "job_name": "前端开发工程师",
        "job_type": "技术岗",
        "degree_requirement": "本科",
        "major_requirement": "计算机类",
        "skill_requirement": "Vue,JavaScript,Element Plus,CSS",
        "experience_requirement": "1年",
        "city": "武汉",
        "description": "负责前端页面开发、交互实现与组件维护。",
        "skill_weight": 0.35,
        "experience_weight": 0.25,
        "degree_weight": 0.2,
        "major_weight": 0.2,
    },
    {
        "job_name": "新媒体运营专员",
        "job_type": "运营岗",
        "degree_requirement": "本科",
        "major_requirement": "传媒类",
        "skill_requirement": "文案,短视频,公众号运营,数据复盘",
        "experience_requirement": "1年",
        "city": "武汉",
        "description": "负责内容策划、短视频运营、公众号维护和数据复盘。",
        "skill_weight": 0.35,
        "experience_weight": 0.3,
        "degree_weight": 0.15,
        "major_weight": 0.2,
    },
    {
        "job_name": "产品助理",
        "job_type": "产品岗",
        "degree_requirement": "本科",
        "major_requirement": "产品设计",
        "skill_requirement": "Axure,XMind,原型设计,需求分析",
        "experience_requirement": "1年",
        "city": "武汉",
        "description": "协助进行需求分析、原型设计、文档撰写和项目跟进。",
        "skill_weight": 0.3,
        "experience_weight": 0.3,
        "degree_weight": 0.15,
        "major_weight": 0.25,
    },
    {
        "job_name": "数据分析助理",
        "job_type": "技术岗",
        "degree_requirement": "本科",
        "major_requirement": "Data Science",
        "skill_requirement": "Python,SQL,Tableau,Excel",
        "experience_requirement": "1年",
        "city": "武汉",
        "description": "负责业务数据分析、报表整理与可视化仪表盘维护。",
        "skill_weight": 0.4,
        "experience_weight": 0.25,
        "degree_weight": 0.15,
        "major_weight": 0.2,
    },
    {
        "job_name": "测试开发工程师",
        "job_type": "技术岗",
        "degree_requirement": "本科",
        "major_requirement": "Computer Science",
        "skill_requirement": "Python,Pytest,SQL,Linux,API Testing",
        "experience_requirement": "1年",
        "city": "武汉",
        "description": "负责接口测试、自动化测试脚本编写与缺陷跟踪。",
        "skill_weight": 0.35,
        "experience_weight": 0.25,
        "degree_weight": 0.15,
        "major_weight": 0.25,
    },
]


RESUMES = [
    {
        "file_name": "zhouhang_frontend.txt",
        "type": "txt",
        "lines": [
            "姓名：周航",
            "电话：13700001234",
            "邮箱：zhouhang@example.com",
            "学历：本科",
            "专业：软件工程",
            "技能：Vue、JavaScript、TypeScript、Element Plus、CSS",
            "",
            "项目经历：",
            "负责企业后台管理系统前端页面开发与组件封装。",
            "使用 Vue3、Element Plus 完成表单、图表和数据看板页面搭建。",
            "与后端联调接口并处理页面性能优化问题。",
        ],
    },
    {
        "file_name": "zhaoting_media.txt",
        "type": "txt",
        "lines": [
            "姓名：赵婷",
            "电话：13700005678",
            "邮箱：zhaoting@example.com",
            "学历：本科",
            "专业：网络与新媒体",
            "技能：文案、短视频、公众号运营、数据复盘、剪映",
            "",
            "实习经历：",
            "在校园媒体中心负责公众号选题策划和内容排版。",
            "参与短视频拍摄剪辑和账号日常运营。",
            "根据阅读量和完播率完成每周数据复盘。",
        ],
    },
    {
        "file_name": "wangmin_product.docx",
        "type": "docx",
        "lines": [
            "姓名：王敏",
            "电话：13811112222",
            "邮箱：wangmin@example.com",
            "学历：本科",
            "专业：产品设计",
            "技能：Axure、XMind、原型设计、需求分析、Visio",
            "",
            "项目经历：",
            "参与校园服务平台需求调研、竞品分析与原型设计。",
            "使用 Axure 绘制高保真原型并输出需求文档。",
            "协助项目经理推进评审会议和开发跟进。",
        ],
    },
    {
        "file_name": "chenjie_data.docx",
        "type": "docx",
        "lines": [
            "姓名：陈杰",
            "电话：13833334444",
            "邮箱：chenjie@example.com",
            "学历：本科",
            "专业：数据科学与大数据技术",
            "技能：Python、SQL、Excel、Tableau、统计分析",
            "",
            "项目经历：",
            "参与电商销售数据分析项目，清洗订单和用户行为数据。",
            "使用 Python 和 SQL 构建分析脚本并输出可视化报表。",
            "利用 Tableau 搭建经营分析仪表盘并进行周报汇总。",
        ],
    },
    {
        "file_name": "alicechen_dataanalyst.pdf",
        "type": "pdf",
        "lines": [
            "Name: Alice Chen",
            "Phone: 13688880001",
            "Email: alice.chen@example.com",
            "Degree: Bachelor",
            "Major: Data Science",
            "Skills: Python, SQL, Tableau, Excel, Statistics",
            "Years of Experience: 1.5 years",
            "",
            "Work Experience:",
            "Maintained weekly dashboards and business analysis reports.",
            "Project Experience:",
            "Built KPI monitoring dashboards and automated sales reports.",
        ],
    },
    {
        "file_name": "kevinliu_testengineer.pdf",
        "type": "pdf",
        "lines": [
            "Name: Kevin Liu",
            "Phone: 13688880002",
            "Email: kevin.liu@example.com",
            "Degree: Bachelor",
            "Major: Computer Science",
            "Skills: Python, Pytest, SQL, Linux, API Testing",
            "Years of Experience: 2 years",
            "",
            "Work Experience:",
            "Executed regression testing and API validation for backend services.",
            "Project Experience:",
            "Designed automated API test suites and defect tracking workflows.",
        ],
    },
]


def request_json(url: str, method: str = "GET", data: bytes | None = None, headers: dict | None = None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def write_txt(path: Path, lines: list[str]):
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def write_docx(path: Path, lines: list[str]):
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    doc.save(path)


def write_pdf(path: Path, lines: list[str]):
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setFont("Helvetica", 11)
    y = 800
    for line in lines:
        if not line:
            y -= 10
            continue
        pdf.drawString(48, y, line)
        y -= 22
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = 800
    pdf.save()


def ensure_resume_files():
    for spec in RESUMES:
        path = DATA_DIR / spec["file_name"]
        if spec["type"] == "txt":
            write_txt(path, spec["lines"])
        elif spec["type"] == "docx":
            write_docx(path, spec["lines"])
        elif spec["type"] == "pdf":
            write_pdf(path, spec["lines"])


def delete_bad_demo_data():
    jobs = request_json(f"{API}/api/jobs/")
    resumes = request_json(f"{API}/api/resumes/")

    expected_job_names = {job["job_name"] for job in JOBS}
    expected_resume_names = {resume["file_name"] for resume in RESUMES}

    client = httpx.Client(timeout=60.0)
    for job in jobs:
        if job["id"] >= 8 or job["job_name"] in expected_job_names or "?" in (job["job_name"] or ""):
            if job["id"] not in {5, 6}:
                client.delete(f"{API}/api/jobs/{job['id']}")

    for resume in resumes:
        if resume["id"] >= 10 or resume["file_name"] in expected_resume_names:
            client.delete(f"{API}/api/resumes/{resume['id']}")


def create_jobs():
    existing_jobs = {job["job_name"] for job in request_json(f"{API}/api/jobs/")}
    created = []
    for job in JOBS:
        if job["job_name"] in existing_jobs:
            continue
        payload = json.dumps(job, ensure_ascii=False).encode("utf-8")
        request_json(
            f"{API}/api/jobs/",
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        created.append(job["job_name"])
    return created


def upload_resumes():
    existing_resumes = {resume["file_name"] for resume in request_json(f"{API}/api/resumes/")}
    client = httpx.Client(timeout=120.0)
    uploaded = []

    for spec in RESUMES:
        path = DATA_DIR / spec["file_name"]
        if spec["file_name"] in existing_resumes:
            continue

        with path.open("rb") as file_obj:
            response = client.post(
                f"{API}/api/resumes/upload",
                files={"file": (spec["file_name"], file_obj, "application/octet-stream")},
            )
        response.raise_for_status()
        resume = response.json()
        uploaded.append({"id": resume["id"], "file_name": resume["file_name"]})
        client.post(f"{API}/api/resumes/{resume['id']}/parse").raise_for_status()
        client.post(f"{API}/api/resumes/{resume['id']}/analyze").raise_for_status()

    return uploaded


def main():
    ensure_resume_files()
    delete_bad_demo_data()
    created_jobs = create_jobs()
    uploaded_resumes = upload_resumes()
    print(
        json.dumps(
            {
                "created_jobs": created_jobs,
                "uploaded_resumes": uploaded_resumes,
                "data_dir": str(DATA_DIR),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
