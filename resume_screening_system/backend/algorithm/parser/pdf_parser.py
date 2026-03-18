import pdfplumber


def parse_pdf(file_path: str) -> str:
    texts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)

    return "\n".join(texts)