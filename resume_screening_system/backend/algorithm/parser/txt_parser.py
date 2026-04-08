import chardet


def parse_txt(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read()
        for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
    return raw.decode(encoding, errors="ignore")
