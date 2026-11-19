import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL, BruteForce  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}
FAST = {name: cls for name, cls in IMPLS.items() if name != "BruteForce"}

CASES = [
    ([1, 8, 6, 2, 5, 4, 8, 3, 7], 49), ([1, 1], 1), ([0, 0], 0), ([0, 5], 0),
    ([4, 3, 2, 1, 4], 16), ([1, 2, 1], 2), ([1, 2, 4, 3], 4),
    ([2, 3, 4, 5, 18, 17, 6], 17),        # две высокие соседние
    ([1, 3, 2, 5, 25, 24, 5], 24),
    ([5, 5, 5, 5, 5], 20), (list(range(1, 11)), 25), (list(range(10, 0, -1)), 25),
    ([1, 10000, 1, 1, 10000, 1], 30000),  # высокие внутри, низкие по краям
    ([0, 0, 0, 7, 0, 0, 7], 21),
]


def test_examples():
    for name, cls in IMPLS.items():
        for height, expected in CASES:
            assert cls().maxArea(list(height)) == expected, (name, height)


def test_random_small_against_brute():
    rng = random.Random(11)
    ref = BruteForce().maxArea
    for _ in range(3000):
        n = rng.randint(2, 40)
        top = rng.choice([1, 3, 10, 10_000])          # маленький top — много равных высот
        height = [rng.randint(0, top) for _ in range(n)]
        expected = ref(height)
        for name, cls in FAST.items():
            assert cls().maxArea(list(height)) == expected, (name, height)


def test_large_inputs_agree():
    rng = random.Random(1)
    n = 100_000
    inputs = [
        [rng.randint(0, 10_000) for _ in range(n)],
        [10_000] * n,
        list(range(n)),
        [min(i, n - 1 - i) % 10_001 for i in range(n)],   # горка
        [0] * n,
    ]
    for height in inputs:
        expected = Solution().maxArea(height)
        for name, cls in FAST.items():
            assert cls().maxArea(height) == expected, name
    assert Solution().maxArea([10_000] * n) == 10_000 * (n - 1)


def test_input_not_mutated():
    height = [3, 1, 4, 1, 5, 9, 2, 6]
    for name, cls in IMPLS.items():
        cls().maxArea(height)
        assert height == [3, 1, 4, 1, 5, 9, 2, 6], name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
