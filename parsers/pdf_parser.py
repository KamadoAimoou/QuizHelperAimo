import re
import pdfplumber
from parsers.base import texts_similar, strip_option_prefix
from parsers.txt_parser import parse_txt, _parse_block_no_answer


def parse_pdf(file_path: str) -> list[dict]:
    questions = _parse_with_highlights(file_path)
    if questions:
        return questions
    return _parse_plain(file_path)


# ── Highlight pipeline ────────────────────────────────────────────────────────

def _parse_with_highlights(file_path: str) -> list[dict]:
    try:
        highlights = _collect_highlights(file_path)
        if not highlights:
            return []

        raw = _parse_plain_no_answer(file_path)
        if not raw:
            return []

        for q in raw:
            for i, opt in enumerate(q['options']):
                opt_body = strip_option_prefix(opt)
                if any(texts_similar(opt_body, hl) for hl in highlights):
                    q['correct'] = i
                    break

        return [q for q in raw if q.get('correct') is not None]

    except Exception:
        return []


def _collect_highlights(file_path: str) -> list[str]:
    """
    Three independent methods to find highlighted (yellow) text:

    A  — /Highlight annotation objects  (Acrobat / PDF reader highlights)
    B  — yellow-fill rectangles in the content stream  (Word/LibreOffice PDF export)
    C  — characters whose glyph fill colour is yellow  (some PDF generators)
    """
    found: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:

            # ── A: Highlight annotations ──────────────────────────────────
            for annot in (page.annots or []):
                if 'Highlight' not in str(annot.get('data', {}).get('Subtype', '')):
                    continue
                text = _text_from_annot(page, annot)
                if text:
                    found.append(text)

            # ── B: Yellow fill rectangles (Word-exported PDFs) ────────────
            for rect in (page.rects or []):
                if not _is_yellow(rect.get('non_stroking_color')):
                    continue
                text = _safe_crop_text(
                    page,
                    rect['x0'], rect['top'], rect['x1'], rect['bottom'],
                    pad=1.0,
                )
                if text:
                    found.append(text)

            # ── C: Characters with yellow glyph fill ─────────────────────
            run: list[str] = []
            for ch in (page.chars or []):
                if _is_yellow(ch.get('non_stroking_color')):
                    run.append(ch.get('text', ''))
                elif run:
                    t = ''.join(run).strip()
                    if t:
                        found.append(t)
                    run = []
            if run:
                t = ''.join(run).strip()
                if t:
                    found.append(t)

    return _deduplicate(found)


def _text_from_annot(page, annot: dict) -> str | None:
    """Crop page to annotation bbox and extract text."""
    x0  = annot.get('x0')
    top = annot.get('top')
    x1  = annot.get('x1')
    bot = annot.get('bottom')

    if None not in (x0, top, x1, bot):
        return _safe_crop_text(page, x0, top, x1, bot)

    # Fallback: raw PDF Rect uses bottom-left origin; convert to pdfplumber space
    rect = annot.get('data', {}).get('Rect')
    if rect and len(rect) == 4:
        rx0, ry0, rx1, ry1 = rect
        return _safe_crop_text(page, rx0, page.height - ry1, rx1, page.height - ry0)

    return None


def _safe_crop_text(page, x0, top, x1, bot, pad: float = 3.0) -> str | None:
    try:
        crop = page.crop((
            max(0.0, x0 - pad),
            max(0.0, top - pad),
            min(float(page.width),  x1 + pad),
            min(float(page.height), bot + pad),
        ))
        text = (crop.extract_text() or '').strip()
        return text or None
    except Exception:
        return None


def _is_yellow(color) -> bool:
    if not isinstance(color, (list, tuple)):
        return False
    if len(color) == 3:        # RGB  (1, 1, 0) ≈ yellow
        r, g, b = color
        return r > 0.65 and g > 0.65 and b < 0.35
    if len(color) == 4:        # CMYK (0, 0, 1, 0) ≈ yellow
        c, m, y, k = color
        return c < 0.25 and m < 0.25 and y > 0.65 and k < 0.25
    return False


def _deduplicate(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out:  list[str] = []
    for t in items:
        key = ' '.join(t.lower().split())
        if key and key not in seen:
            seen.add(key)
            out.append(t)
    return out


# ── Plain-text pipeline ───────────────────────────────────────────────────────

def _extract_text(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        pages = [page.extract_text() or '' for page in pdf.pages]
    return '\n\n'.join(pages)


def _prepare_text(raw: str) -> str:
    """Insert blank lines before numbered questions so blocks split correctly."""
    return re.sub(r'\n(\d+[.)]\s)', r'\n\n\1', raw)


def _parse_plain(file_path: str) -> list[dict]:
    return parse_txt(_prepare_text(_extract_text(file_path)))


def _parse_plain_no_answer(file_path: str) -> list[dict]:
    text = _prepare_text(_extract_text(file_path))
    return [
        q
        for block in re.split(r'\n\s*\n', text.strip())
        for q in [_parse_block_no_answer(block.strip())]
        if q
    ]
