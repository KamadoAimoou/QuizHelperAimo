import re
import os

def parse_file(file_path: str) -> list[dict]:
    """
    Основная функция, которую вызывает хэндлер.
    Она открывает файл по пути, читает текст и передает его в парсер.
    """
    if not os.path.exists(file_path):
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    return parse_txt(text)


def parse_txt(text: str) -> list[dict]:
    """
    Парсит текст и возвращает список вопросов.
    Формат каждого вопроса:
    {"text": "Вопрос?", "options": ["A) ...", "B) ..."], "correct": 1}
    """
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
    if len(lines) < 3:
        return None

    question_text = re.sub(r'^[\d]+[.)]\s*', '', lines[0]).strip()
    if not question_text:
        return None

    options = []
    correct_index = None

    for line in lines[1:]:
        
        answer_match = re.match(
            r'^(ответ|answer|правильный)[:\s]+([A-Da-dА-Га-г1-4])',
            line, re.IGNORECASE
        )
        if answer_match:
            correct_letter = answer_match.group(2).upper()
            correct_index = _letter_to_index(correct_letter)
            continue

        # Ищем варианты ответов A) B) C) D) или 1) 2) 3) 4)
        if re.match(r'^[A-Da-dА-Га-г1-4][).]\s*.+', line):
            options.append(line)

    if len(options) < 2 or correct_index is None:
        return None

    return {"text": question_text, "options": options, "correct": correct_index}


def _letter_to_index(letter: str) -> int | None:
    mapping = {'A': 0, 'А': 0, '1': 0,
               'B': 1, 'Б': 1, '2': 1,
               'C': 2, 'В': 2, '3': 2,
               'D': 3, 'Г': 3, '4': 3}
    return mapping.get(letter.upper())