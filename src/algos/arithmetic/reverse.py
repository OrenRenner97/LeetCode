"""Разворот цифр целого числа. LeetCode: 7. Reverse Integer (обобщённо) + 9. Palindrome Number.

Отличия от LeetCode-версии:
- результат, который не помещается в целое на `bits` бит, — `None`, а не 0: у LeetCode 0 — и «переполнение»,
  и законный ответ reverse(0), их не различить;
- `width` — разворот в фиксированной ширине с ведущими нулями: 120 при width=4 → «0120» → «0210» = 210.
  Без ширины разворот не обратим (12 и 120 оба дают 21), с шириной — взаимно однозначен;
- любое основание 2…36, ширина целого `bits` (8, 32, 64, …), знаковое или беззнаковое.

Python-int неограничен, поэтому промежуточные значения не обязаны помещаться в `bits` бит: проверяется
результат. Строгая 32-битная арифметика нужна только в C/Java (см. problems/0007_reverse_integer).
"""

_STR_MAX_BITS = 12_000  # ~3 600 цифр: str()/int() в CPython 3.12 ограничены 4 300 цифрами (sys.int_info)


def int_range(bits: int, *, signed: bool = True) -> tuple[int, int]:
    """[min, max] целого на bits бит: int_range(32) == (−2³¹, 2³¹ − 1), int_range(8, signed=False) == (0, 255)."""
    _check_bits(bits)
    return (-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if signed else (0, (1 << bits) - 1)


def reverse_digits(x: int, *, base: int = 10, width: int | None = None, bits: int | None = None,
                   signed: bool = True) -> int | None:
    """Цифры |x| в обратном порядке, знак сохраняется: 123 → 321, −120 → −21.

    width: дополнить |x| ведущими нулями до width цифр перед разворотом (120, width=5 → «00120» → 2100).
        Тогда разворот обратим: reverse_digits(reverse_digits(x, width=w), width=w) == x.
    bits: результат должен помещаться в целое на bits бит (signed или нет); не помещается → None.
        reverse_digits(x, bits=32) or 0 — ровно LeetCode 7.
    O(d) для d цифр (O(d²) для чисел длиннее ~3 600 цифр).

    TypeError: x или параметры не int (bool тоже не принимается).
    ValueError: base вне 2…36; width < 1 или |x| длиннее width; bits < 1;
        x сам не помещается в bits бит (в том числе x < 0 при signed=False).
    """
    _check_int("x", x)
    _check_int("base", base)
    if not 2 <= base <= 36:
        raise ValueError(f"base: ожидается 2…36, получено {base}")
    if width is not None:
        _check_int("width", width)
        if width < 1:
            raise ValueError(f"width должен быть >= 1, получено {width}")
    lo = hi = None
    if bits is not None:
        lo, hi = int_range(bits, signed=signed)
        if not lo <= x <= hi:
            kind = "знаковое" if signed else "беззнаковое"
            raise ValueError(f"x = {x} не помещается в {kind} целое на {bits} бит: [{lo}, {hi}]")

    r, count = _reverse_abs(abs(x), base)
    if width is not None:
        if count > width:
            raise ValueError(f"|x| = {abs(x)} длиннее width = {width} цифр в основании {base}")
        r *= base ** (width - count)  # ведущие нули |x| стали хвостовыми нулями разворота
    if x < 0:
        r = -r
    if bits is not None and not lo <= r <= hi:
        return None
    return r


def is_digit_palindrome(x: int, *, base: int = 10) -> bool:
    """Читается ли x одинаково с обеих сторон (LeetCode 9). Отрицательные — нет: «−121» ≠ «121−»."""
    _check_int("x", x)
    return x >= 0 and reverse_digits(x, base=base) == x


def _reverse_abs(n: int, base: int) -> tuple[int, int]:
    """(разворот n, число цифр n); у нуля одна цифра."""
    if base == 10 and n.bit_length() <= _STR_MAX_BITS:
        s = str(n)  # str, срез и int — C-циклы: в 2–5 раз быстрее divmod в Python (README задачи 7)
        return int(s[::-1]), len(s)
    if n == 0:
        return 0, 1
    r = count = 0
    while n:
        n, d = divmod(n, base)
        r = r * base + d
        count += 1
    return r, count


def _check_int(name: str, v) -> None:
    if not isinstance(v, int) or isinstance(v, bool):
        raise TypeError(f"{name}: ожидается int, получено {type(v).__name__}")


def _check_bits(bits) -> None:
    _check_int("bits", bits)
    if bits < 1:
        raise ValueError(f"bits должен быть >= 1, получено {bits}")
