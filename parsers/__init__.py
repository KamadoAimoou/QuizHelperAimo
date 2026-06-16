import os
from parsers.txt_parser   import parse_txt
from parsers.pdf_parser   import parse_pdf
from parsers.docx_parser  import parse_docx
from parsers.image_parser import parse_image


def _parse_txt_file(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        return parse_txt(f.read())


_EXT_MAP = {
    '.txt':  _parse_txt_file,
    '.pdf':  parse_pdf,
    '.docx': parse_docx,
    '.jpg':  parse_image,
    '.jpeg': parse_image,
    '.png':  parse_image,
}


def parse_file(file_path: str) -> list[dict]:
    ext = os.path.splitext(file_path)[1].lower()
    handler = _EXT_MAP.get(ext)
    if handler is None:
        return []
    return handler(file_path)


def supported_extensions() -> list[str]:
    return list(_EXT_MAP.keys())
