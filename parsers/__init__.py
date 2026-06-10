import os
from parsers.txt_parser import parse_txt

def parse_file(file_path: str) -> list[dict]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return parse_txt(f.read())
    return []  # остальные форматы добавим позже

def supported_extensions():
    return [".txt"]