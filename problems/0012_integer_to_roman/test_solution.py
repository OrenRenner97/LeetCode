import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    (3749, "MMMDCCXLIX"), (58, "LVIII"), (1994, "MCMXCIV"),
    (1, "I"), (3, "III"), (4, "IV"), (5, "V"), (9, "IX"), (10, "X"),
    (14, "XIV"), (40, "XL"), (44, "XLIV"), (49, "XLIX"), (90, "XC"), (99, "XCIX"),
    (400, "CD"), (444, "CDXLIV"), (500, "D"), (900, "CM"), (999, "CMXCIX"),
    (1000, "M"), (2024, "MMXXIV"), (3888, "MMMDCCCLXXXVIII"), (3999, "MMMCMXCIX"),
]

# Каноническая римская запись 1..3999: каждый разряд — одна из десяти форм.
CANON = re.compile(r"M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")
VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_value(s: str) -> int:
    """Обратное преобразование — независимый эталон: символ меньше следующего вычитается."""
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = VALUES[a]
        total += -v if b != " " and v < VALUES[b] else v
    return total


def test_examples():
    for name, cls in IMPLS.items():
        for num, expected in CASES:
            assert cls().intToRoman(num) == expected, (name, num)


def test_all_numbers_canonical_and_roundtrip():
    seen = set()
    for num in range(1, 4000):
        r = Solution().intToRoman(num)
        assert CANON.fullmatch(r), (num, r)
        assert roman_value(r) == num, (num, r)
        seen.add(r)
    assert len(seen) == 3999


def test_alternatives_agree_on_full_range():
    ref = [Solution().intToRoman(n) for n in range(1, 4000)]
    for name, cls in ALL.items():
        f = cls().intToRoman
        assert [f(n) for n in range(1, 4000)] == ref, name


def test_longest_answer():
    assert max(range(1, 4000), key=lambda n: len(Solution().intToRoman(n))) == 3888


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
