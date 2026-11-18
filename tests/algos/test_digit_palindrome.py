import random

import pytest

from algos.arithmetic import is_digit_palindrome, next_digit_palindrome, prev_digit_palindrome

DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def _repr(x: int, base: int) -> str:
    s = ""
    while True:
        x, d = divmod(x, base)
        s = DIGITS[d] + s
        if not x:
            return s


def _is_pal(x: int, base: int = 10, width: int | None = None) -> bool:
    if x < 0:
        return False
    s = _repr(x, base)
    if width is not None:
        s = s.rjust(width, "0")
    return s == s[::-1]


def test_leetcode_examples():
    assert is_digit_palindrome(121) is True
    assert is_digit_palindrome(-121) is False
    assert is_digit_palindrome(10) is False
    assert is_digit_palindrome(0) and is_digit_palindrome(7) and is_digit_palindrome(1001)
    assert not is_digit_palindrome(100) and not is_digit_palindrome(2**31 - 1) and not is_digit_palindrome(-2**31)


def test_against_reference_all_bases():
    for base in (2, 3, 8, 10, 16, 36):
        for x in range(-50, 3000):
            assert is_digit_palindrome(x, base=base) == _is_pal(x, base), (x, base)


def test_width():
    assert is_digit_palindrome(110, width=4)                 # «0110»
    assert not is_digit_palindrome(110, width=3)
    assert is_digit_palindrome(0b0110, base=2, width=4)
    assert not is_digit_palindrome(0b1001, base=2, width=5)  # «01001»
    for base in (2, 10):
        for width in (1, 2, 3, 4, 5):
            for x in range(min(base ** width, 2000)):
                assert is_digit_palindrome(x, base=base, width=width) == _is_pal(x, base, width), (x, base, width)


def test_huge_numbers():
    # 10 000 цифр — длиннее лимита str()/int() в 3.12, поэтому строим арифметикой: «2111…1112» и «…3…»
    p = (10**10000 - 1) // 9 + 10**9999 + 1 + 2 * 10**4999 + 2 * 10**5000
    assert is_digit_palindrome(p) and not is_digit_palindrome(p + 10)
    assert next_digit_palindrome(p) == p and prev_digit_palindrome(p) == p
    assert next_digit_palindrome(10**5000) == 10**5000 + 1


def test_next_prev_exhaustive():
    for base in (2, 3, 10, 16):
        pals = [x for x in range(0, 5000) if _is_pal(x, base)]
        for x in range(-20, 4000):
            nxt = next((p for p in pals if p >= x), None)
            prv = next((p for p in reversed(pals) if p <= x), None)
            assert next_digit_palindrome(x, base=base) == nxt, (x, base)
            assert prev_digit_palindrome(x, base=base) == prv, (x, base)


def test_next_prev_random_large():
    rng = random.Random(9)
    for _ in range(2000):
        x = rng.randint(0, 10**18)
        n, p = next_digit_palindrome(x), prev_digit_palindrome(x)
        assert p <= x <= n and _is_pal(n) and _is_pal(p)
        # между p и n других палиндромов нет: соседние вызовы возвращают друг друга
        if n > x:
            assert prev_digit_palindrome(n - 1) == p
        if p < x:
            assert next_digit_palindrome(p + 1) == n


def test_boundaries():
    assert next_digit_palindrome(999) == 999 and next_digit_palindrome(1000) == 1001
    assert prev_digit_palindrome(1000) == 999 and prev_digit_palindrome(10) == 9
    assert next_digit_palindrome(2**31 - 1) == 2147557412   # отражение 2147447412 < x → левая половина + 1
    assert prev_digit_palindrome(2**31 - 1) == 2147447412   # наибольший палиндром в int32
    assert next_digit_palindrome(-5) == 0 and prev_digit_palindrome(-1) is None


def test_validation():
    for bad in (1.0, "12", True, None):
        with pytest.raises(TypeError):
            is_digit_palindrome(bad)
        with pytest.raises(TypeError):
            next_digit_palindrome(bad)
        with pytest.raises(TypeError):
            prev_digit_palindrome(bad)
    for f in (is_digit_palindrome, next_digit_palindrome, prev_digit_palindrome):
        for base in (1, 37):
            with pytest.raises(ValueError):
                f(5, base=base)
        with pytest.raises(ValueError):
            f(-5, base=1)
    with pytest.raises(ValueError):
        is_digit_palindrome(12345, width=3)
    with pytest.raises(ValueError):
        is_digit_palindrome(-12345, width=3)
    with pytest.raises(ValueError):
        is_digit_palindrome(1, width=0)
    with pytest.raises(TypeError):
        is_digit_palindrome(1, width=True)
