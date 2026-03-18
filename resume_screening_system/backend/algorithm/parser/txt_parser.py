import chardet


def parse_txt(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
    return raw.decode(encoding, errors="ignore")