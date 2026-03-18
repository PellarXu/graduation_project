from docx import Document


def parse_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            texts.append(text)

    return "\n".join(texts)