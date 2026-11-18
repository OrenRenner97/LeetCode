"""Палиндромы по цифрам целого числа. LeetCode: 9. Palindrome Number (+ задел на 564. Find the Closest Palindrome).

Отличия от LeetCode-версии:
- любое основание 2…36: is_digit_palindrome(0b1001, base=2);
- `width` — палиндром в фиксированной ширине с ведущими нулями: 110 при width=4 → «0110» — палиндром.
  Так проверяют битовые маски и коды фиксированной длины, где ведущие нули значимы;
- next_digit_palindrome / prev_digit_palindrome — ближайший палиндром сверху / снизу за O(d),
  а не перебором (между соседними 10-значными палиндромами бывает до 10⁵ чисел).

Реализация — через строку для основания 10 (по замерам задачи 9 в 2–5 раз быстрее divmod),
divmod для остальных оснований и для чисел длиннее ~3 600 цифр.
"""
from .reverse import _STR_MAX_BITS, _check_int, reverse_digits


def is_digit_palindrome(x: int, *, base: int = 10, width: int | None = None) -> bool:
    """Читается ли x одинаково с обеих сторон (LeetCode 9). Отрицательные — нет: «−121» ≠ «121−».

    width: дополнить x ведущими нулями до width цифр: is_digit_palindrome(110, width=4) is True («0110»).
    O(d) для d цифр.

    TypeError: x или параметры не int (bool тоже). ValueError: base вне 2…36; width < 1 или x длиннее width.
    """
    _check_int("x", x)
    if x < 0:
        _check_base(base)
        if width is not None:
            reverse_digits(-x, base=base, width=width)  # та же валидация width, что и для x ≥ 0
        return False
    if width is None and base == 10 and x.bit_length() <= _STR_MAX_BITS:
        s = str(x)  # быстрый путь: одна строка, без reverse_digits и проверок параметров
        return s == s[::-1]
    return reverse_digits(x, base=base, width=width) == x


def next_digit_palindrome(x: int, *, base: int = 10) -> int:
    """Наименьший палиндром ≥ x (в основании base). Для x ≤ 0 — 0. O(d).

    Идея: отражаем левую половину x на правую. Если вышло меньше x — увеличиваем левую половину на 1
    (вместе со средней цифрой) и отражаем снова. Переноса в новый разряд не бывает: если левая половина —
    одни старшие цифры (99…), её отражение 99…9 уже ≥ x, и до увеличения дело не доходит.
    """
    _check_int("x", x)
    _check_base(base)
    if x <= 0:
        return 0
    digits = _to_digits(x, base)
    n = len(digits)
    half = (n + 1) // 2                     # левая половина вместе со средней цифрой
    p = _mirror(digits[:half], n)
    if _from_digits(p, base) >= x:
        return _from_digits(p, base)
    left = _from_digits(digits[:half], base) + 1   # длина та же (см. docstring)
    return _from_digits(_mirror(_to_digits(left, base), n), base)


def prev_digit_palindrome(x: int, *, base: int = 10) -> int | None:
    """Наибольший палиндром ≤ x (в основании base). Для x < 0 — None (неотрицательных палиндромов ≤ x нет). O(d).

    Зеркально next_digit_palindrome: отражаем левую половину; вышло больше x — уменьшаем её на 1.
    Левая половина 10…0 → 09…9 теряет длину: ответ 99…9 на одну цифру короче.
    """
    _check_int("x", x)
    _check_base(base)
    if x < 0:
        return None
    if x < base:
        return x                            # одна цифра — уже палиндром
    digits = _to_digits(x, base)
    n = len(digits)
    half = (n + 1) // 2
    p = _mirror(digits[:half], n)
    if _from_digits(p, base) <= x:
        return _from_digits(p, base)
    left = _from_digits(digits[:half], base) - 1
    if left < base ** (half - 1):           # 10…0 → 9…9: на одну цифру короче
        return base ** (n - 1) - 1
    return _from_digits(_mirror(_to_digits(left, base), n), base)


def _mirror(left: list[int], n: int) -> list[int]:
    """Палиндром длины n из левой половины (ceil(n/2) цифр, старшие первыми)."""
    return left + left[: n // 2][::-1]


def _to_digits(n: int, base: int) -> list[int]:
    """Цифры n ≥ 0, старшие первыми."""
    if base == 10 and n.bit_length() <= _STR_MAX_BITS:
        return [ord(c) - 48 for c in str(n)]
    out = []
    while True:
        n, d = divmod(n, base)
        out.append(d)
        if not n:
            return out[::-1]


def _from_digits(digits: list[int], base: int) -> int:
    if base == 10 and len(digits) <= 3_600:
        return int("".join(map(str, digits)))
    r = 0
    for d in digits:
        r = r * base + d
    return r


def _check_base(base) -> None:
    _check_int("base", base)
    if not 2 <= base <= 36:
        raise ValueError(f"base: ожидается 2…36, получено {base}")
