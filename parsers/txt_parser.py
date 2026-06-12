
import re


def parse_txt(text: str) -> list[dict]:
    questions = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        parsed = _parse_block(block)
        if parsed:
            questions.append(parsed)
    return questions


def _parse_block(block: str) -> dict | None:
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    print(f"БЛОК: {lines}")

    if len(lines) < 3:
        return None

    question_text = re.sub(r'^[\d]+[.)]\s*', '', lines[0]).strip()
    if not question_text:
        return None

    options = []
    correct_index = None

    for line in lines[1:]:
        # Вариант 1: OTBeT (OCR путает буквы)
        answer_match = re.match(
            r'^[OoОо][TtТт][BbВв][eeеЕ][TtТт][:\s\|]+([A-Da-dА-ДCcСс1-4])',
            line, re.IGNORECASE
        )
        if answer_match:
            correct_index = _letter_to_index(answer_match.group(1))
            continue

        # Вариант 2: Ответ / Answer
        answer_match2 = re.match(
            r'^(ответ|answer)[:\s\|]+([A-Da-dА-ДCcСс1-4])',
            line, re.IGNORECASE
        )
        if answer_match2:
            correct_index = _letter_to_index(answer_match2.group(2))
            continue

        # Варианты ответов A) B) C) D)
        if re.match(r'^[A-Da-dА-Га-г1-4][).]\s*.+', line):
            options.append(line)

    if len(options) < 2 or correct_index is None:
        return None

    return {"text": question_text, "options": options, "correct": correct_index}


def _letter_to_index(letter: str) -> int | None:
    mapping = {
        'A': 0, 'А': 0, 'a': 0, 'а': 0, '1': 0,
        'B': 1, 'В': 1, 'b': 1, 'в': 1, '2': 1,
        'C': 2, 'С': 2, 'c': 2, 'с': 2, '3': 2,
        'D': 3, 'Д': 3, 'd': 3, 'д': 3, '4': 3,
    }
    return mapping.get(letter.strip())
