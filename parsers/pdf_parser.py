import pdfplumber
import re
from parsers.txt_parser import parse_txt

def parse_pdf(file_path: str) -> list[dict]:
    text = _extract_text(file_path)
    if not text.strip():
        return []
    # Добавляем пустую строку перед каждым новым вопросом (1. 2. 3. и т.д.)
    text = re.sub(r'\n(\d+\.)', r'\n\n\1', text)
    return parse_txt(text)

def _extract_text(file_path: str) -> str:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n\n".join(pages)