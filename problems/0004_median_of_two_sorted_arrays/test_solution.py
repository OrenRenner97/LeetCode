import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    ([1, 3], [2], 2.0),
    ([1, 2], [3, 4], 2.5),
    ([], [1], 1.0),
    ([2], [], 2.0),
    ([], [2, 3], 2.5),
    ([0, 0], [0, 0], 0.0),
    ([1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11], 6.0),
    ([1, 2, 3], [100, 200, 300], 51.5),     # массивы не пересекаются: разрез на краю
    ([100, 200, 300], [1, 2, 3], 51.5),     # то же, но длинный/короткий наоборот
    ([1, 100], [2, 3], 2.5),
    ([-5, -3, -1], [-2], -2.5),
    ([1], [2, 3, 4, 5, 6, 7, 8], 4.5),      # короткий массив целиком в левой половине
    ([9], [2, 3, 4, 5, 6, 7, 8], 5.5),      # ... и целиком в правой
    ([1, 1, 1], [1, 1, 1, 1], 1.0),         # одни дубли
    ([-10**6], [10**6], 0.0),               # границы значений
]


def test_examples():
    for name, cls in IMPLS.items():
        for a, b, expected in CASES:
            got = cls().findMedianSortedArrays(list(a), list(b))
            assert got == expected and isinstance(got, float), (name, a, b, got)


def test_does_not_mutate_input():
    for name, cls in IMPLS.items():
        a, b = [1, 5, 9], [2, 3]
        cls().findMedianSortedArrays(a, b)
        assert (a, b) == ([1, 5, 9], [2, 3]), name


def test_random_against_statistics():
    rng = random.Random(42)
    for _ in range(3000):
        m = rng.randint(0, 12)
        n = rng.randint(0 if m else 1, 12)
        hi = rng.choice([3, 50, 10**6])  # маленький диапазон → много дублей
        a = sorted(rng.randint(-hi, hi) for _ in range(m))
        b = sorted(rng.randint(-hi, hi) for _ in range(n))
        expected = float(statistics.median(a + b))
        for name, cls in IMPLS.items():
            assert cls().findMedianSortedArrays(a, b) == expected, (name, a, b)


def test_max_size_agree():
    # m + n = 2000 — максимум по условию, в том числе очень неравные длины.
    rng = random.Random(7)
    for m in [0, 1, 7, 1000, 1999]:
        n = 2000 - m
        a = sorted(rng.randint(-10**6, 10**6) for _ in range(m))
        b = sorted(rng.randint(-10**6, 10**6) for _ in range(n))
        expected = float(statistics.median(a + b))
        for name, cls in IMPLS.items():
            assert cls().findMedianSortedArrays(a, b) == expected, (name, m)


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
