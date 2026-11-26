import random
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}
FAST = dict(ALL)
FAST.pop("Combinations")

CASES = [
    ([-1, 0, 1, 2, -1, -4], [(-1, -1, 2), (-1, 0, 1)]),
    ([0, 1, 1], []),
    ([0, 0, 0], [(0, 0, 0)]),
    ([0, 0, 0, 0], [(0, 0, 0)]),
    ([0, 0, 1], []),
    ([-2, 0, 1, 1, 2], [(-2, 0, 2), (-2, 1, 1)]),
    ([1, 2, 3], []), ([-3, -2, -1], []),
    ([-1, -1, 2, 2], [(-1, -1, 2)]),
    ([-4, 2, 2, 2], [(-4, 2, 2)]),
    ([-2, -2, 4, 4, -2], [(-2, -2, 4)]),
    ([3, -1, -2, 0, 1, -3, 2], [(-3, 0, 3), (-3, 1, 2), (-2, -1, 3), (-2, 0, 2), (-1, 0, 1)]),
    ([-100000, 50000, 50000], [(-100000, 50000, 50000)]),
]


def norm(triplets) -> list[tuple[int, ...]]:
    return sorted(tuple(sorted(int(x) for x in t)) for t in triplets)


def reference(nums: list[int]) -> list[tuple[int, ...]]:
    return sorted({tuple(sorted(t)) for t in combinations(nums, 3) if sum(t) == 0})


def test_examples():
    for name, cls in IMPLS.items():
        for nums, expected in CASES:
            assert norm(cls().threeSum(list(nums))) == expected, (name, nums)


def test_no_duplicate_triplets():
    for name, cls in IMPLS.items():
        out = [tuple(sorted(t)) for t in cls().threeSum([-1, 0, 1, 2, -1, -4, -1, 0, 1, 0])]
        assert len(out) == len(set(out)), name


def test_random_against_reference():
    rng = random.Random(15)
    for _ in range(2000):
        n = rng.randint(3, 14)
        lim = rng.choice([1, 3, 10, 100])
        nums = [rng.randint(-lim, lim) for _ in range(n)]
        expected = reference(nums)
        for name, cls in IMPLS.items():
            assert norm(cls().threeSum(list(nums))) == expected, (name, nums)


def test_max_constraints_fast():
    rng = random.Random(3)
    inputs = [
        [rng.randint(-10**5, 10**5) for _ in range(3000)],
        [rng.randint(-50, 50) for _ in range(3000)],
        [0] * 3000,
        list(range(-300, 300)),              # много троек: ~45 тыс.
    ]
    for nums in inputs:
        expected = norm(ALL["SortTwoPointers"]().threeSum(nums))  # сверен с эталоном в test_random
        for name, cls in FAST.items():
            assert norm(cls().threeSum(list(nums))) == expected, name


def test_input_not_mutated():
    nums = [-1, 0, 1, 2, -1, -4]
    for name, cls in IMPLS.items():
        cls().threeSum(nums)
        assert nums == [-1, 0, 1, 2, -1, -4], name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
