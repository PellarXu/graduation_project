import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\u3000", " ")
    cleaned = cleaned.replace("\r", "")
    cleaned = cleaned.replace("\t", " ")
    cleaned = cleaned.replace("：", ":")
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
    return cleaned.strip()
