import re
from parsers.base import (
    OPTION_RE, ANSWER_RE, OCR_ANSWER_RE, LETTER_MAP,
    strip_option_prefix, strip_question_number, normalize_ws,
)


def parse_txt(text: str) -> list[dict]:
    questions = []
    for block in re.split(r'\n\s*\n', text.strip()):
        block = block.strip()
        if block:
            q = _parse_block(block)
            if q:
                questions.append(q)
    return questions


def _parse_block(block: str) -> dict | None:
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if len(lines) < 3:
        return None

    q_lines: list[str] = []
    opts: list[tuple[str, str, str, str]] = []   # (marker, letter, body, full_raw)
    correct_idx: int | None = None

    for line in lines:
        m = ANSWER_RE.match(line) or OCR_ANSWER_RE.match(line)
        if m:
            correct_idx = LETTER_MAP.get(m.group(1))
            continue

        m = OPTION_RE.match(line)
        # Only treat as option if we've already seen question text —
        # prevents numbered question lines ("1. Вопрос?") from being
        # misread as option "1)" when digits are in the option class.
        if m and q_lines:
            opts.append((m.group(1).strip(), m.group(2), m.group(3).strip(), line))
        elif opts:
            # Continuation line (e.g., matrix rows under an option header)
            ma, le, bd, rw = opts[-1]
            opts[-1] = (ma, le, bd + ' ' + line, rw + ' ' + line)
        else:
            q_lines.append(line)

    if len(opts) < 2:
        return None

    # Inline marker as answer indicator (* + ✓ →)
    if correct_idx is None:
        for i, (marker, *_rest) in enumerate(opts):
            if marker in ('*', '+', '✓', '→'):
                correct_idx = i
                break

    if correct_idx is None or correct_idx >= len(opts):
        return None

    question_text = strip_question_number(normalize_ws(' '.join(q_lines)))
    if not question_text:
        return None

    options = [re.sub(r'^[*+✓→]\s*', '', raw).strip() for _, _, _, raw in opts]
    return {'text': question_text, 'options': options, 'correct': correct_idx}


def _parse_block_no_answer(block: str) -> dict | None:
    """Parse a question block without an answer marker.

    Returns {'text':..., 'options': [raw_lines...], 'correct': None}.
    Options keep their letter prefix so callers can match against highlights.
    """
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if len(lines) < 3:
        return None

    q_lines: list[str] = []
    opts: list[str] = []

    for line in lines:
        if ANSWER_RE.match(line) or OCR_ANSWER_RE.match(line):
            continue
        # Same guard: only start collecting options after question text exists
        if OPTION_RE.match(line) and q_lines:
            opts.append(line)
        elif opts:
            opts[-1] = opts[-1] + ' ' + line
        else:
            q_lines.append(line)

    if len(opts) < 2:
        return None

    question_text = strip_question_number(normalize_ws(' '.join(q_lines)))
    if not question_text:
        return None

    return {'text': question_text, 'options': opts, 'correct': None}
