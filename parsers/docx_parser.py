from docx import Document
from parsers.txt_parser import parse_txt

def parse_docx(file_path: str) -> list[dict]:
    text = _extract_text(file_path)
    if not text.strip():
        return []
    return parse_txt(text)

def _extract_text(file_path: str) -> str:
    doc = Document(file_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(lines)