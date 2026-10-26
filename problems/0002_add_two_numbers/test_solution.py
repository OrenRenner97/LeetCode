import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution, build, to_list  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}
NON_MUTATING = [name for name in IMPLS if name != "InPlace"]

CASES = [
    ([2, 4, 3], [5, 6, 4], [7, 0, 8]),
    ([0], [0], [0]),
    ([9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9], [8, 9, 9, 9, 0, 0, 0, 1]),
    ([1], [9, 9, 9], [0, 0, 0, 1]),  # перенос бежит по хвосту второго списка
    ([5], [5], [0, 1]),               # перенос создаёт новый разряд
    ([0], [1, 2, 3], [1, 2, 3]),
    ([1, 2, 3], [0], [1, 2, 3]),
]


def _num(digits):
    return int("".join(map(str, reversed(digits))))


def _digits(n):
    return [int(c) for c in reversed(str(n))]


def _random_number(rng, max_len):
    k = rng.randint(1, max_len)
    digits = [rng.randint(0, 9) for _ in range(k)]
    if k > 1 and digits[-1] == 0:  # без ведущих нулей
        digits[-1] = rng.randint(1, 9)
    return digits


def test_examples():
    for name, cls in IMPLS.items():
        for a, b, expected in CASES:
            assert to_list(cls().addTwoNumbers(build(a), build(b))) == expected, (name, a, b)


def test_random_against_int_arithmetic():
    rng = random.Random(42)
    for _ in range(500):
        a, b = _random_number(rng, 100), _random_number(rng, 100)  # ограничения LeetCode
        expected = _digits(_num(a) + _num(b))
        for name, cls in IMPLS.items():
            assert to_list(cls().addTwoNumbers(build(a), build(b))) == expected, (name, a, b)


def test_inputs_not_mutated():
    a, b = [9, 9, 1], [3, 4]
    for name in NON_MUTATING:
        l1, l2 = build(a), build(b)
        IMPLS[name]().addTwoNumbers(l1, l2)
        assert (to_list(l1), to_list(l2)) == (a, b), name


def test_long_numbers_iterative_only():
    # 10^4 цифр: Recursive упадёт по лимиту рекурсии, ViaInt по лимиту int↔str (4300 цифр).
    rng = random.Random(7)
    a, b = _random_number(rng, 10_000), _random_number(rng, 10_000)
    expected = to_list(Solution().addTwoNumbers(build(a), build(b)))
    for name in ("Compact", "InPlace"):
        assert to_list(IMPLS[name]().addTwoNumbers(build(a), build(b))) == expected, name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
