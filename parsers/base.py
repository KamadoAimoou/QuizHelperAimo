"""
Shared regex patterns and utilities for all parsers.

The option letter character class lists Cyrillic letters EXPLICITLY because they do
not form a contiguous Unicode range:
  А=U+0410  В=U+0412  С=U+0421  Д=U+0414  Е=U+0415  (non-contiguous!)
Using [А-Д] would miss С and any letter outside that narrow range.
"""
import re

_OL = r'[AaBbCcDdEeFfАаВвСсДдЕе1-6]'

OPTION_RE = re.compile(
    rf'^([*+✓→]?\s*)({_OL})[).]\s*(.+)',
    re.UNICODE,
)

ANSWER_RE = re.compile(
    rf'^(?:ответ|answer|правильный\s*ответ|correct(?:\s+answer)?|верный\s*ответ)'
    rf'[:\s|]+({_OL})',
    re.IGNORECASE | re.UNICODE,
)

OCR_ANSWER_RE = re.compile(
    rf'^[OoОо][TtТт][BbВв][EeЕе][TtТт][:\s|]+({_OL})',
    re.IGNORECASE,
)

LETTER_MAP: dict[str, int] = {
    'A': 0, 'А': 0, 'a': 0, 'а': 0, '1': 0,
    'B': 1, 'В': 1, 'b': 1, 'в': 1, '2': 1,
    'C': 2, 'С': 2, 'c': 2, 'с': 2, '3': 2,
    'D': 3, 'Д': 3, 'd': 3, 'д': 3, '4': 3,
    'E': 4, 'Е': 4, 'e': 4, 'е': 4, '5': 4,
    'F': 5, 'f': 5,                  '6': 5,
}

_PREFIX_RE = re.compile(rf'^[*+✓→]?\s*{_OL}[).]\s*', re.UNICODE)
_Q_NUM_RE  = re.compile(r'^\d+[.)]\s*')

# Cyrillic visually-identical homogl­yphs → Latin (used in similarity checks only)
_HOMOGLYPH_TABLE = str.maketrans('АаВЕеОоРрСсТХх', 'AaBEeOoPpCcTXx')


def strip_option_prefix(text: str) -> str:
    return _PREFIX_RE.sub('', text).strip()


def strip_question_number(text: str) -> str:
    return _Q_NUM_RE.sub('', text).strip()


def normalize_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def homoglyph_fold(text: str) -> str:
    return text.lower().translate(_HOMOGLYPH_TABLE)


def texts_similar(a: str, b: str) -> bool:
    """Return True when two option strings likely refer to the same content."""
    a = homoglyph_fold(normalize_ws(a))
    b = homoglyph_fold(normalize_ws(b))
    if not a or not b:
        return False
    # Very short tokens: require exact equality to avoid false positives
    if len(a) < 4 or len(b) < 4:
        return a == b
    if a in b or b in a:
        return True
    wa = set(a.split())
    wb = set(b.split())
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.6
