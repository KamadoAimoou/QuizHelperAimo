import os
from parsers.txt_parser import parse_txt
from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx

def parse_file(file_path: str) -> list[dict]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return parse_txt(f.read())
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    return []

def supported_extensions():
    return [".txt", ".pdf", ".docx"]