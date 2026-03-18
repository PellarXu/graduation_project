import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\u3000", " ")
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.replace("：", ":")
    return text.strip()