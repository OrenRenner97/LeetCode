"""Целое из начала строки, как atoi/strtol в C. LeetCode: 8. String to Integer (atoi).

Отличия от LeetCode-версии:
- нет цифр → `None`, а не 0: у LeetCode 0 — и «мусор», и законное «0»;
- возвращается не только значение, но и `end` (как `endptr` у strtol: где кончился разбор) и `clamped`
  (значение прижато к границе) — по ним вызывающий решает, строгий это ввод или нет;
- любое основание 2…36, ширина `bits` (или без ограничения), знаковое / беззнаковое;
- цифры — только ASCII: str.isdigit() и `\\d` принимают '²', '٣' и т. п. (README задачи 8).

Реализация — регулярное выражение: по замерам шага 1 оно в 2–3 раза быстрее Python-цикла (Regex),
а большой int не строится: если значащих цифр больше, чем у границы, ответ — сама граница (StripPrefix).
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from ..arithmetic import int_range

_ALNUM = "0123456789abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True, slots=True)
class IntPrefix:
    value: int      # прочитанное число, прижатое к диапазону
    end: int        # индекс первого непрочитанного символа: s[end:] — «хвост», который atoi молча отбросил
    clamped: bool   # число было вне диапазона и прижато к границе


@lru_cache(maxsize=64)
def _pattern(base: int, whitespace: str) -> re.Pattern:
    digits = _ALNUM[:base]
    cls = re.escape(digits + digits[10:].upper())
    ws = f"[{re.escape(whitespace)}]*" if whitespace else ""
    return re.compile(f"{ws}([+-]?)0*([{cls}]*)")


def parse_int_prefix(s: str, *, base: int = 10, bits: int | None = 32, signed: bool = True,
                     whitespace: str = " ") -> IntPrefix | None:
    """Читает целое с начала `s`: пробелы → знак → цифры до первой не-цифры. Нет цифр → None.

    bits: результат прижимается к [min, max] целого на bits бит (int_range); None — без ограничения
        (до ~4 300 значащих цифр в основании 10: лимит int() в CPython).
    signed=False: «-5» прижимается к 0 (clamped=True), а «-0» — просто 0.
    whitespace: какие символы пропускать в начале; у LeetCode только ' ', у C — ещё \\t\\n\\v\\f\\r.
    LeetCode 8: `r.value if (r := parse_int_prefix(s)) else 0`. O(n).

    TypeError: s не str или параметры не int. ValueError: base вне 2…36, bits < 1.
    """
    if not isinstance(s, str):
        raise TypeError(f"s: ожидается str, получено {type(s).__name__}")
    for name, v in (("base", base), ("bits", bits)):
        if v is not None and (not isinstance(v, int) or isinstance(v, bool)):
            raise TypeError(f"{name}: ожидается int, получено {type(v).__name__}")
    if not 2 <= base <= 36:
        raise ValueError(f"base: ожидается 2…36, получено {base}")

    m = _pattern(base, whitespace).match(s)
    sign, digits = m.group(1), m.group(2)
    if not digits and m.end(2) == m.end(1):   # после знака ни одной цифры, даже нуля
        return None
    neg = sign == "-"
    if bits is None:
        v = int(digits, base) if digits else 0
        return IntPrefix(-v if neg else v, m.end(), False)

    lo, hi = int_range(bits, signed=signed)
    limit = -lo if neg else hi
    if neg and limit == 0:                    # беззнаковое и минус: только «-0» не прижимается
        return IntPrefix(0, m.end(), bool(digits))
    if len(digits) > _width(limit, base):     # заведомо больше границы: большой int не строим
        return IntPrefix(-limit if neg else limit, m.end(), True)
    v = int(digits, base) if digits else 0
    if v > limit:
        return IntPrefix(-limit if neg else limit, m.end(), True)
    return IntPrefix(-v if neg else v, m.end(), False)


@lru_cache(maxsize=256)
def _width(n: int, base: int) -> int:
    """Число цифр n в основании base."""
    w = 1
    while n >= base:
        n //= base
        w += 1
    return w
