"""Целое ↔ римская запись. LeetCode: 12. Integer to Roman (`to_roman`), 13. Roman to Integer (`from_roman`).

Отличия от LeetCode-версии:
- вне диапазона [ROMAN_MIN, ROMAN_MAX] = [1, 3999] → `None`, а не мусор. Почему граница именно 3999:
  у классических римских цифр нет символа для 5000, а больше трёх M подряд (MMMM) — уже не каноническая
  запись. Нуля и отрицательных чисел у римлян не было вовсе. Расширения (черта над символом = ×1000,
  «апострофус» CIↃ) не стандартизованы, поэтому не поддерживаются;
- `lowercase=True` — строчные (i, iv, xii): нумерация страниц предисловия, пунктов в документах;
- принимает любой целый тип (`int`, numpy-целые — через `operator.index`), `bool` и `float` — TypeError.

`from_roman` — строгий разбор: только каноническая запись (та, что выдаёт `to_roman`), иначе `None`.
LeetCode обещает корректный вход, поэтому там IIII → 4 и IM → 1001 проходят молча; здесь — `None`.

Реализация — FullLookup из задач 12 и 13: все 3999 записей (верхний и нижний регистр) и обратный словарь
строятся один раз при импорте (~5 ms, <1 МБ) по таблицам разрядов (DigitTables), дальше — индекс или один `dict.get`.
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
_LOWER = [r.lower() for r in _UPPER]

# Обратная таблица: все 3999 канонических записей в верхнем и нижнем регистре (~8000 ключей)
# — так строчные бесплатны и в from_roman, а смешанный регистр отсекается сам.
# Проверка корректности бесплатна: чего нет в словаре — то не каноническая запись.
_PARSE = {r: n for table in (_UPPER, _LOWER) for n, r in enumerate(table) if r}


def to_roman(n: int, *, lowercase: bool = False) -> str | None:
    """Каноническая римская запись числа n: 1994 → "MCMXCIV".

    n вне [1, 3999] → None (римскими цифрами без расширений это не записать).
    lowercase=True → строчные: 14 → "xiv". O(1).

    TypeError: n не целое (bool и float тоже не принимаются).
    """
    if isinstance(n, bool):
        raise TypeError("n должен быть целым, получен bool")
    n = operator.index(n)                 # TypeError для float, str и т.п.; numpy-целые → int
    if not ROMAN_MIN <= n <= ROMAN_MAX:
        return None
    return _LOWER[n] if lowercase else _UPPER[n]


def from_roman(s: str) -> int | None:
    """Число по канонической римской записи: "MCMXCIV" → 1994.

    Принимает только каноническую запись [1, 3999] — ровно то, что возвращает `to_roman`:
    IIII, VV, IC, IM, MMMM, "" → None. Регистр — весь верхний или весь нижний ("xiv" → 14);
    смешанный ("XiV") и пробелы по краям → None. O(len(s)) — хэш строки.

    TypeError: s не str.
    """
    if not isinstance(s, str):
        raise TypeError(f"s должна быть str, получено {type(s).__name__}")
    return _PARSE.get(s)
