from pathlib import Path

import pdfplumber

from algorithm.parser.txt_parser import parse_txt


def _looks_garbled(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return True
    marker_count = normalized.count("?") + normalized.count("\ufffd")
    return marker_count >= max(5, len(normalized) // 5)


def parse_pdf(file_path: str) -> str:
    texts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)

    combined = "\n".join(texts).strip()
    if not _looks_garbled(combined):
        return combined

    sidecar_path = Path(f"{file_path}.txt")
    if sidecar_path.exists():
        return parse_txt(str(sidecar_path)).strip()
    return combined
