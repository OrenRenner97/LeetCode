"""Целое → римская запись. LeetCode: 12. Integer to Roman.

Отличия от LeetCode-версии:
- вне диапазона [ROMAN_MIN, ROMAN_MAX] = [1, 3999] → `None`, а не мусор. Почему граница именно 3999:
  у классических римских цифр нет символа для 5000, а больше трёх M подряд (MMMM) — уже не каноническая
  запись. Нуля и отрицательных чисел у римлян не было вовсе. Расширения (черта над символом = ×1000,
  «апострофус» CIↃ) не стандартизованы, поэтому не поддерживаются;
- `lowercase=True` — строчные (i, iv, xii): нумерация страниц предисловия, пунктов в документах;
- принимает любой целый тип (`int`, numpy-целые — через `operator.index`), `bool` и `float` — TypeError.

Реализация — FullLookup из задачи 12: все 3999 ответов строятся один раз при импорте (~2 ms, ~250 КБ)
по таблицам разрядов (DigitTables), дальше — один индекс. ×57 к жадному решению, ×6 к таблицам разрядов.
"""
import operator

ROMAN_MIN = 1
ROMAN_MAX = 3999

_THOUSANDS = ("", "M", "MM", "MMM")
_HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
_TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
_ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")

_UPPER = [""] + [_THOUSANDS[n // 1000] + _HUNDREDS[n // 100 % 10] + _TENS[n // 10 % 10] + _ONES[n % 10]
                 for n in range(ROMAN_MIN, ROMAN_MAX + 1)]
_LOWER: list[str] | None = None       # строится при первом запросе: нужен редко


def to_roman(n: int, *, lowercase: bool = False) -> str | None:
    """Каноническая римская запись числа n: 1994 → "MCMXCIV".

    n вне [1, 3999] → None (римскими цифрами без расширений это не записать).
    lowercase=True → строчные: 14 → "xiv". O(1).

    TypeError: n не целое (bool и float тоже не принимаются).
    """
    global _LOWER
    if isinstance(n, bool):
        raise TypeError("n должен быть целым, получен bool")
    n = operator.index(n)                 # TypeError для float, str и т.п.; numpy-целые → int
    if not ROMAN_MIN <= n <= ROMAN_MAX:
        return None
    if lowercase:
        if _LOWER is None:
            _LOWER = [s.lower() for s in _UPPER]
        return _LOWER[n]
    return _UPPER[n]
