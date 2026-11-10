"""Взлом «изгороди» без ключа: перебор всех (rails, offset) и оценка по частотам биграмм языка.

Перестановка не меняет состав букв, поэтому частоты отдельных букв у всех кандидатов одинаковы.
Различает их только порядок: в настоящем тексте часто встречаются пары TH, HE, IN… (СТ, НО, ТО…)
и почти не встречаются стыки вроде DN или ЪЫ, а в неправильной расшифровке пары почти случайны.
"""
import math
from functools import cache
from pathlib import Path

from .cipher import decrypt, letters_only
from .models import Candidate, CrackResult, Key

# Модель языка — частоты пар букв по небольшому корпусу (corpus_<язык>.txt, ~4 КБ авторского текста).
# Вклад пары ab: log P(ab) − log P(a) − log P(b): сколько раз пара встречается чаще, чем при случайном
# порядке тех же букв. У частых пар (TH, СТ) он положительный, у невозможных стыков (DN, ЪЫ) — сильно
# отрицательный. Поэтому средний вклад < 0 у перемешанного текста и > 0 у настоящего.
_ALPHABETS = {"en": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "ru": "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"}
LANGUAGES = tuple(_ALPHABETS)
_SMOOTHING = 0.5  # добавка к счётчикам: пара, которой не было в корпусе, редкая, но не невозможная

_SAMPLE = 400            # для оценки хватает первых букв: длиннее — только дольше
_MIN_LETTERS = 40        # короче — статистики мало: на 30 символах были уверенные ошибки (README модуля)
_CONFIDENT_MARGIN = 0.1  # лучший минус лучший не-поворот, в единицах score; калибровка — README модуля


@cache
def _weights(language: str) -> dict[str, float]:
    alphabet = _ALPHABETS[language]
    text = letters_only((Path(__file__).parent / f"corpus_{language}.txt").read_text(encoding="utf-8"))
    text = "".join(ch for ch in text if ch in alphabet)
    a = len(alphabet)
    uni = {ch: _SMOOTHING for ch in alphabet}
    for ch in text:
        uni[ch] += 1
    pairs = {x + y: _SMOOTHING for x in alphabet for y in alphabet}
    for x, y in zip(text, text[1:]):
        pairs[x + y] += 1
    n1, n2 = sum(uni.values()), len(text) - 1 + _SMOOTHING * a * a
    return {xy: math.log(c / n2) - math.log(uni[xy[0]] / n1) - math.log(uni[xy[1]] / n1)
            for xy, c in pairs.items()}


def score(text: str, language: str) -> float:
    """Средний вклад пары соседних букв text (не-буквы выбрасываются; пары с буквами не из алфавита
    языка дают 0). У настоящего текста > 0 (~0.2–0.5), у перемешанных букв < 0 (~−0.5…−0.7):
    случайный порядок рождает невозможные стыки, а они штрафуются сильнее, чем частые пары награждаются."""
    weights = _weights(language)
    s = letters_only(text)[:_SAMPLE]
    if len(s) < 2:
        return 0.0
    get = weights.get
    return sum(get(a + b, 0.0) for a, b in zip(s, s[1:])) / (len(s) - 1)


def detect_language(text: str) -> str:
    """'ru', если кириллицы больше, чем латиницы, иначе 'en'."""
    cyr = sum("А" <= ch <= "Я" for ch in letters_only(text))
    return "ru" if 2 * cyr > len(letters_only(text)) else "en"


def crack(ciphertext: str, *, language: str = "auto", max_rails: int = 40, top: int = 5,
          backend: str | None = None) -> CrackResult:
    """Перебирает все ключи с 2 <= rails <= max_rails и все сдвиги, возвращает top лучших расшифровок.

    Ключей ~max_rails² (сдвигов у rails строк — 2·(rails - 1)), каждый — расшифровка O(n) на algos.
    Одинаковые расшифровки (на коротком тексте разные ключи часто дают одно и то же) схлопываются.
    ValueError: неизвестный язык, max_rails < 2, top < 1.
    """
    if language == "auto":
        language = detect_language(ciphertext)
    if language not in _ALPHABETS:
        raise ValueError(f"language: ожидается 'auto' или одно из {LANGUAGES}, получено {language!r}")
    if max_rails < 2:
        raise ValueError(f"max_rails должен быть >= 2, получено {max_rails}")
    if top < 1:
        raise ValueError(f"top должен быть >= 1, получено {top}")

    n = len(ciphertext)
    best: dict[str, Candidate] = {}
    tried = 0
    # Больше n строк смысла нет: с любым сдвигом зигзаг длины n уже укладывается в n строк.
    for rails in range(2, min(max_rails, max(n, 2)) + 1):
        for offset in range(2 * (rails - 1)):
            key = Key(rails, offset)
            tried += 1
            text = decrypt(ciphertext, key, backend=backend)
            if text not in best:  # ключи идут по возрастанию: остаётся наименьший
                best[text] = Candidate(key, text, score(text, language))
    ranked = sorted(best.values(), key=lambda c: -c.score)  # стабильно: при равенстве — меньший ключ
    if not ranked:
        return CrackResult(language, (), tried, False)
    leader = ranked[0].plaintext
    doubled = leader + leader
    rotations = tuple(c for c in ranked[1:] if c.plaintext in doubled)  # повороты leader и только они
    others = [c for c in ranked[1:] if c.plaintext not in doubled]
    letters = len(letters_only(ciphertext))
    confident = letters >= _MIN_LETTERS and (not others or ranked[0].score - others[0].score >= _CONFIDENT_MARGIN)
    return CrackResult(language, tuple(ranked[:top]), tried, confident, rotations)
