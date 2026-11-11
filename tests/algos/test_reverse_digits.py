import importlib.util
import random
from pathlib import Path

import pytest

from algos import reverse_digits
from algos.arithmetic import int_range, is_digit_palindrome
from algos.arithmetic import reverse as reverse_module

ROOT = Path(__file__).resolve().parents[2]


def _ref(x, base=10, width=None):
    # Эталон по определению: список цифр.
    digits, n = [], abs(x)
    while True:
        n, d = divmod(n, base)
        digits.append(d)
        if not n:
            break
    if width is not None:
        digits = [0] * (width - len(digits)) + digits[::-1]
        digits = digits[::-1]
    r = 0
    for d in digits:
        r = r * base + d
    return -r if x < 0 else r


def test_basic():
    assert reverse_digits(123) == 321
    assert reverse_digits(-123) == -321
    assert reverse_digits(120) == 21
    assert reverse_digits(0) == 0
    assert reverse_digits(1534236469) == 9646324351          # без bits — неограниченно
    assert reverse_digits(1534236469, bits=32) is None
    assert reverse_digits(1463847412, bits=32) == 2147483641
    assert reverse_digits(-2**31, bits=32) is None


def test_leetcode_equivalence():
    # reverse_digits(x, bits=32) or 0 — ровно LeetCode 7; сверяем с учебными альтернативами.
    spec = importlib.util.spec_from_file_location("alt7", ROOT / "problems/0007_reverse_integer/alternatives.py")
    alt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alt)
    ref = alt.PopPushGuard()
    rng = random.Random(7)
    lo, hi = int_range(32)
    xs = [rng.randint(lo, hi) for _ in range(20_000)] + [lo, hi, 0, 1, -1, 1463847412, -1563847412]
    for x in xs:
        assert (reverse_digits(x, bits=32) or 0) == ref.reverse(x), x


def test_none_is_not_zero():
    # Ради этого и None: у LeetCode 0 означает и «переполнение», и reverse(0).
    assert reverse_digits(0, bits=32) == 0
    assert reverse_digits(1534236469, bits=32) is None


def test_width_is_bijection():
    for width in (1, 2, 3, 4):
        values = range(10 ** width)
        images = [reverse_digits(v, width=width) for v in values]
        assert sorted(images) == list(values)
        assert all(reverse_digits(r, width=width) == v for v, r in zip(values, images))
    assert reverse_digits(120, width=5) == 2100
    assert reverse_digits(-7, width=3) == -700
    # Без ширины — коллизии: 12 и 120 → 21.
    assert reverse_digits(12) == reverse_digits(120) == 21


def test_bases_against_reference():
    rng = random.Random(1)
    for _ in range(3000):
        base = rng.randint(2, 36)
        x = rng.randint(-10**12, 10**12)
        assert reverse_digits(x, base=base) == _ref(x, base), (x, base)
        width = len(_digits(abs(x), base)) + rng.randint(0, 3)
        assert reverse_digits(x, base=base, width=width) == _ref(x, base, width), (x, base, width)
    assert reverse_digits(0b1101, base=2) == 0b1011
    assert reverse_digits(0b1101, base=2, width=8) == 0b10110000


def _digits(n, base):
    out = []
    while True:
        n, d = divmod(n, base)
        out.append(d)
        if not n:
            return out


def test_bits_unsigned_and_small():
    assert int_range(8) == (-128, 127) and int_range(8, signed=False) == (0, 255)
    assert reverse_digits(52, bits=8, signed=False) == 25
    assert reverse_digits(250, bits=8, signed=False) == 52
    assert reverse_digits(95, bits=8, signed=False) == 59
    assert reverse_digits(126, bits=8) is None                  # 621 > 127
    assert reverse_digits(-128, bits=8) is None                 # −821
    assert reverse_digits(-21, bits=8) == -12
    assert reverse_digits(0b011, bits=3, base=2, width=3) is None    # «011» → «110» = 6 > 3 (max 3-битного знакового)
    assert reverse_digits(0b011, bits=3, base=2, width=3, signed=False) == 0b110


def test_huge_numbers_use_generic_path():
    x = 12 * (10**6000 - 1) // 99            # «1212…12», 6000 цифр — длиннее лимита str()/int() в 3.12
    assert x.bit_length() > reverse_module._STR_MAX_BITS
    assert reverse_digits(x) == _ref(x)
    assert reverse_digits(x, width=6001) == _ref(x) * 10


def test_palindrome():
    assert is_digit_palindrome(121) and is_digit_palindrome(0) and is_digit_palindrome(7)
    assert not is_digit_palindrome(-121) and not is_digit_palindrome(10) and not is_digit_palindrome(123)
    assert is_digit_palindrome(0b1001, base=2) and not is_digit_palindrome(0b1000, base=2)


def test_validation():
    for bad in (1.0, "12", True, None):
        with pytest.raises(TypeError):
            reverse_digits(bad)
    with pytest.raises(TypeError):
        reverse_digits(1, width=2.0)
    with pytest.raises(TypeError):
        reverse_digits(1, bits=True)
    for kwargs in (dict(base=1), dict(base=37), dict(width=0), dict(bits=0)):
        with pytest.raises(ValueError):
            reverse_digits(1, **kwargs)
    with pytest.raises(ValueError):
        reverse_digits(1234, width=3)                # длиннее ширины
    with pytest.raises(ValueError):
        reverse_digits(2**31, bits=32)               # вход вне int32
    with pytest.raises(ValueError):
        reverse_digits(-1, bits=8, signed=False)
    with pytest.raises(ValueError):
        reverse_digits(8, bits=4, base=2)            # 4-битное знаковое: max 7
