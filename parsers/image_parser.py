import re
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from parsers.txt_parser import parse_txt

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def parse_image(file_path: str) -> list[dict]:
    text = _extract_text(file_path)
    if not text.strip():
        return []
    lines = [l for l in text.split('\n') if l.strip()]
    clean = re.sub(r'\n(\d+[.)]\s)', r'\n\n\1', '\n'.join(lines))
    return parse_txt(clean)


def _extract_text(file_path: str) -> str:
    img  = Image.open(file_path)
    gray = img.convert('L')
    avg  = sum(gray.getdata()) / len(gray.getdata())
    if avg < 128:
        gray = ImageOps.invert(gray)
    w, h = gray.size
    gray = gray.resize((w * 2, h * 2), Image.LANCZOS)
    gray = gray.filter(ImageFilter.SHARPEN)
    try:
        return pytesseract.image_to_string(gray, lang='rus+eng')
    except Exception:
        return pytesseract.image_to_string(gray, lang='eng')
