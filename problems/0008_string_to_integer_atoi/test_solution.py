import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL, INT_MAX, INT_MIN  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    ("42", 42), (" -042", -42), ("1337c0d3", 1337), ("0-1", 0), ("words and 987", 0),
    ("", 0), ("   ", 0), ("+", 0), ("-", 0), ("+-12", 0), ("-+12", 0), ("++1", 0),
    ("  +0 123", 0), ("  +  413", 0), ("- 1", 0), ("3.14159", 3), (".1", 0),
    ("00000-42a1234", 0), ("\t42", 0), ("\n42", 0), ("-0", 0), ("+007", 7),
    ("2147483647", INT_MAX), ("2147483648", INT_MAX), ("-2147483648", INT_MIN),
    ("-2147483649", INT_MIN), ("-91283472332", INT_MIN), ("2147483646", 2147483646),
    ("-2147483647", -2147483647), ("21474836460", INT_MAX), ("-21474836480", INT_MIN),
    ("0" * 30 + "1", 1), ("-" + "0" * 195 + "1234", -1234), ("1" + "0" * 199, INT_MAX),
    ("-" + "9" * 199, INT_MIN), ("A1", 0), ("1e5", 1),
]

# Вне ограничений LeetCode: Unicode-цифры. str.isdigit() их принимает, поэтому Solution
# даёт мусор (1² → 140, ٣ → 1587) — известное замечание из README, тест только для альтернатив.
UNICODE_CASES = [("1²", 1), ("٣", 0), ("-١٢", 0), ("12٣4", 12), ("⁵", 0)]


def _ref(s: str) -> int:
    # Эталон по определению, без общих с решениями приёмов: явный разбор + неограниченный int.
    i = 0
    while i < len(s) and s[i] == " ":
        i += 1
    j = i + (i < len(s) and s[i] in "+-")
    k = j
    while k < len(s) and s[k] in "0123456789":
        k += 1
    if k == j:
        return 0
    v = int(s[j:k]) * (-1 if s[i] == "-" else 1)
    return min(INT_MAX, max(INT_MIN, v))


def _random_strings(rng, count):
    alphabet = " +-.0123456789aZ"
    out = []
    for _ in range(count):
        n = rng.randint(0, 14)
        out.append("".join(rng.choice(alphabet) for _ in range(n)))
    return out


def _near_bounds():
    # Числа в ±1000 от границ, со знаками, нулями и пробелами: здесь живут ошибки на единицу.
    out = []
    for v in range(INT_MAX - 1000, INT_MAX + 1001):
        for prefix in ("", "+", "-", "  ", "  -", "00", "-000"):
            out.append(prefix + str(v))
    return out


def test_examples():
    for name, cls in IMPLS.items():
        for s, expected in CASES:
            assert cls().myAtoi(s) == expected, (name, s)


def test_reference_on_cases():
    for s, expected in CASES + UNICODE_CASES:
        assert _ref(s) == expected, s


def test_unicode_digits_rejected():
    for name, cls in ALL.items():
        for s, expected in UNICODE_CASES:
            assert cls().myAtoi(s) == expected, (name, s)


def test_near_bounds():
    xs = _near_bounds()
    for name, cls in IMPLS.items():
        f = cls().myAtoi
        for s in xs:
            assert f(s) == _ref(s), (name, s)


def test_random_against_reference():
    rng = random.Random(8)
    xs = _random_strings(rng, 30_000)
    xs += [" " * rng.randint(0, 3) + rng.choice(("", "+", "-")) + str(rng.randint(0, 10**rng.randint(0, 25)))
           + rng.choice(("", "a", " 1", ".5", "-")) for _ in range(10_000)]
    for name, cls in IMPLS.items():
        f = cls().myAtoi
        for s in xs:
            assert f(s) == _ref(s), (name, s)


def test_results_fit_int32():
    rng = random.Random(1)
    xs = _random_strings(rng, 5000)
    for name, cls in IMPLS.items():
        f = cls().myAtoi
        for s in xs:
            assert INT_MIN <= f(s) <= INT_MAX, name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
