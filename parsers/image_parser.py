import pytesseract
import re
from PIL import Image, ImageOps, ImageFilter
from parsers.txt_parser import parse_txt

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def parse_image(file_path: str) -> list[dict]:
    text = _extract_text(file_path)
    if not text.strip():
        return []

    # Убираем лишние пустые строки которые OCR добавляет между строками
    lines = [l for l in text.split('\n') if l.strip()]
    clean_text = '\n'.join(lines)

    # Добавляем пустую строку перед новым вопросом (1. 2. 3.)
    clean_text = re.sub(r'\n(\d+[.)]\s)', r'\n\n\1', clean_text)

    print("=== ОЧИЩЕННЫЙ ТЕКСТ ===")
    print(clean_text)
    print("=======================")

    return parse_txt(clean_text)


def _extract_text(file_path: str) -> str:
    img = Image.open(file_path)
    gray = img.convert("L")
    avg_brightness = sum(gray.getdata()) / len(gray.getdata())
    if avg_brightness < 128:
        gray = ImageOps.invert(gray)
    w, h = gray.size
    gray = gray.resize((w * 2, h * 2), Image.LANCZOS)
    gray = gray.filter(ImageFilter.SHARPEN)
    try:
        text = pytesseract.image_to_string(gray, lang="rus+eng")
    except Exception:
        text = pytesseract.image_to_string(gray, lang="eng")

    print("=== OCR РЕЗУЛЬТАТ ===")
    print(text)
    print("====================")
    return text