from __future__ import annotations

import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

from docx import Document
import httpx
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
DEMO_DIR = PROJECT_DIR / "demo_seed" / "resumes"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal, bootstrap_schema
from app.models.resume import Resume
from app.services.analysis_service import analyze_resume_by_id
from app.services.parse_service import parse_resume_by_id
from app.services.resume_service import create_resume_record

DATASET_API = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=OhMyKing%2FFairCV&config=default&split=train&offset={offset}&length=1"
)

SAMPLE_SPECS = [
    {"offset": 100000, "format": "txt"},
    {"offset": 120000, "format": "txt"},
    {"offset": 200000, "format": "docx"},
    {"offset": 320000, "format": "docx"},
    {"offset": 440000, "format": "pdf"},
    {"offset": 560000, "format": "pdf"},
]

NAME_PATTERNS = [
    re.compile(r"\u59d3\u540d\s*[\uff1a:]\s*([^\n]+)"),
    re.compile(r"\u59d3\u540d\s+([^\n]+)"),
]


def fetch_row(offset: int, retries: int = 5) -> dict:
    last_error: Exception | None = None
    url = DATASET_API.format(offset=offset)

    for attempt in range(1, retries + 1):
        try:
            response = httpx.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("rows") or []
            if not rows:
                raise RuntimeError(f"no rows returned for offset {offset}")
            return rows[0]["row"]
        except Exception as exc:  # pragma: no cover - network retries
            last_error = exc
            time.sleep(min(attempt, 2))

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            rows = payload.get("rows") or []
            if not rows:
                raise RuntimeError(f"no rows returned for offset {offset}")
            return rows[0]["row"]
        except Exception as exc:  # pragma: no cover - network retries
            last_error = exc
            time.sleep(min(attempt, 2))

    raise RuntimeError(f"failed to fetch offset {offset}: {last_error}")


def normalize_text(markdown_text: str) -> str:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            lines.append("")
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^\-\s*", "", line)
        line = line.replace("**", "").replace("`", "")
        line = re.sub(r"\s{2,}", " ", line).strip()
        lines.append(line)

    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return normalized


def extract_name(text: str) -> str:
    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""


def sanitize_filename_part(value: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]+', "_", value)
    safe = re.sub(r"\s+", "", safe)
    safe = re.sub(r"_+", "_", safe).strip("._")
    return safe or "简历样本"


def build_file_stem(name: str, position: str, row_idx: int) -> str:
    stem = f"{sanitize_filename_part(name)}_{sanitize_filename_part(position)}"
    return stem.strip("_") or f"简历样本_{row_idx}"


def ensure_unique_name(filename: str, seen: set[str], row_idx: int) -> str:
    if filename not in seen:
        seen.add(filename)
        return filename

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = f"{stem}_{row_idx}{suffix}"
    seen.add(candidate)
    return candidate


def get_pdf_font_name() -> str:
    candidates = [
        ("SimHei", Path(r"C:\Windows\Fonts\simhei.ttf")),
        ("MicrosoftYaHei", Path(r"C:\Windows\Fonts\msyh.ttc")),
        ("SimSun", Path(r"C:\Windows\Fonts\simsun.ttc")),
    ]
    for font_name, font_path in candidates:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            return font_name
        except Exception:
            continue
    return "Helvetica"


def wrap_pdf_line(pdf: canvas.Canvas, text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if not text:
        return [""]

    rows: list[str] = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        if current:
            rows.append(current)
        current = char

    if current:
        rows.append(current)
    return rows


def write_txt(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8-sig")


def write_docx(path: Path, text: str) -> None:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(path)


def write_pdf(path: Path, text: str) -> None:
    font_name = get_pdf_font_name()
    font_size = 11
    line_height = 18
    left = 48
    top = 800
    bottom = 60
    max_width = A4[0] - left * 2

    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setFont(font_name, font_size)
    y = top

    for line in text.splitlines():
        wrapped_lines = wrap_pdf_line(pdf, line, font_name, font_size, max_width)
        for row in wrapped_lines:
            if y < bottom:
                pdf.showPage()
                pdf.setFont(font_name, font_size)
                y = top
            if row:
                pdf.drawString(left, y, row)
            y -= line_height if row else line_height // 2

    pdf.save()


def write_pdf_sidecar(pdf_path: Path, text: str) -> None:
    Path(f"{pdf_path}.txt").write_text(text, encoding="utf-8-sig")


def clear_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def save_resume_files(filename: str, file_format: str, text: str) -> tuple[Path, Path]:
    upload_path = UPLOAD_DIR / filename
    demo_path = DEMO_DIR / filename

    if file_format == "txt":
        write_txt(upload_path, text)
        shutil.copy2(upload_path, demo_path)
    elif file_format == "docx":
        write_docx(upload_path, text)
        shutil.copy2(upload_path, demo_path)
    elif file_format == "pdf":
        write_pdf(upload_path, text)
        write_pdf_sidecar(upload_path, text)
        shutil.copy2(upload_path, demo_path)
        shutil.copy2(Path(f"{upload_path}.txt"), Path(f"{demo_path}.txt"))
    else:
        raise ValueError(f"unsupported format: {file_format}")

    return upload_path, demo_path


def rebuild_samples() -> list[dict]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    clear_directory(UPLOAD_DIR)
    clear_directory(DEMO_DIR)

    seen_names: set[str] = set()
    samples: list[dict] = []

    for spec in SAMPLE_SPECS:
        row = fetch_row(spec["offset"])
        metadata = row.get("metadata") or {}
        content = normalize_text(row.get("content") or "")
        name = extract_name(content) or "候选人"
        position = metadata.get("position") or "岗位"
        row_idx = int(spec["offset"])
        stem = build_file_stem(name, position, row_idx)
        filename = ensure_unique_name(f"{stem}.{spec['format']}", seen_names, row_idx)
        upload_path, _ = save_resume_files(filename, spec["format"], content)
        samples.append(
            {
                "filename": filename,
                "file_type": spec["format"],
                "file_path": str(upload_path),
                "position": position,
                "name": name,
                "source_offset": spec["offset"],
            }
        )

    return samples


def rebuild_database(samples: list[dict]) -> list[dict]:
    bootstrap_schema()
    db = SessionLocal()
    try:
        db.query(Resume).delete()
        db.commit()

        results: list[dict] = []
        for sample in samples:
            resume = create_resume_record(
                db=db,
                file_name=sample["filename"],
                file_path=sample["file_path"],
                file_type=sample["file_type"],
            )
            parsed = parse_resume_by_id(db, resume.id)
            analyzed = analyze_resume_by_id(db, resume.id)
            results.append(
                {
                    "id": resume.id,
                    "file_name": sample["filename"],
                    "parse_status": getattr(parsed, "parse_status", None),
                    "extract_status": getattr(analyzed, "extract_status", None),
                }
            )
        return results
    finally:
        db.close()


def main() -> None:
    samples = rebuild_samples()
    results = rebuild_database(samples)
    print(json.dumps({"samples": samples, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
