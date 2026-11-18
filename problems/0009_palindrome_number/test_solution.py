import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}
INT_MAX, INT_MIN = 2**31 - 1, -2**31

CASES = [
    (121, True), (-121, False), (10, False),
    (0, True), (7, True), (11, True), (12, False), (1221, True), (12321, True), (123, False),
    (100, False),           # нули в конце
    (1001, True),           # нули в середине: PeelEnds не должен их потерять
    (10001, True), (1000021, False), (100021, False),
    (1000000001, True),     # 10 цифр, нули внутри
    (-1, False), (-0, True),
    (INT_MAX, False), (INT_MIN, False),
    (2147447412, True),     # палиндром у верхней границы
    (1999999991, True), (1234554321, True), (1234564321, False),
]


def _palindromes(rng, n):
    # Случайные палиндромы ≤ 2³¹ − 1: зеркалим случайную левую половину.
    out = []
    while len(out) < n:
        d = rng.randint(1, 10)
        left = str(rng.randint(10 ** ((d + 1) // 2 - 1), 10 ** ((d + 1) // 2) - 1))
        p = int(left + left[: d // 2][::-1])
        if p <= INT_MAX:
            out.append(p)
    return out


def test_examples():
    for name, cls in IMPLS.items():
        for x, expected in CASES:
            assert cls().isPalindrome(x) is expected, (name, x)


def test_all_small():
    # Все x из [−100, 100 000]: каждая длина до 5 цифр, все нули в любых позициях.
    for name, cls in IMPLS.items():
        f = cls().isPalindrome
        for x in range(-100, 100_001):
            assert f(x) == (str(x) == str(x)[::-1]), (name, x)


def test_random_against_reference():
    rng = random.Random(9)
    xs = [rng.randint(INT_MIN, INT_MAX) for _ in range(20_000)] + _palindromes(rng, 5_000)
    xs += [p + rng.choice((-1, 1, 10, -10)) for p in _palindromes(rng, 5_000)]   # почти палиндромы
    for name, cls in IMPLS.items():
        f = cls().isPalindrome
        for x in xs:
            assert f(x) == (str(x) == str(x)[::-1]), (name, x)


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
