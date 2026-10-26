import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {name: cls().twoSum for name, cls in {"Solution": Solution, **ALL}.items()}

CASES = [
    ([2, 7, 11, 15], 9),
    ([3, 2, 4], 6),           # nums[0] * 2 == target, но один элемент дважды нельзя
    ([3, 3], 6),              # дубликаты
    ([-1, -2, -3, -4, -5], -8),
    ([0, 4, 3, 0], 0),        # нули
    ([10**9, -10**9, 5], 0),  # границы
    ([1, 5, 1, 5], 10),
]


def _valid(nums, target, ans):
    i, j = ans
    return i != j and 0 <= i < len(nums) and 0 <= j < len(nums) and nums[i] + nums[j] == target


def _random_case(rng, n):
    # Генерируем ровно одну пару: значения уникальны, при этом a + b == target
    # и никакая другая пара в сумме target не даёт.
    target = rng.randint(-10**6, 10**6)
    a = rng.randint(-10**6, 10**6)
    b = target - a
    nums, used = [a, b], {a, b}
    while len(nums) < n:
        x = rng.randint(-10**6, 10**6)
        if x not in used and target - x not in used:
            nums.append(x)
            used.add(x)
    rng.shuffle(nums)
    return nums, target


def test_examples():
    for name, fn in IMPLS.items():
        for nums, target in CASES:
            ans = fn(list(nums), target)
            assert _valid(nums, target, ans), (name, nums, target, ans)


def test_random_against_each_other():
    rng = random.Random(42)
    for _ in range(300):
        nums, target = _random_case(rng, rng.randint(2, 60))
        expected = sorted(Solution().twoSum(nums, target))
        for name, fn in IMPLS.items():
            assert sorted(fn(list(nums), target)) == expected, (name, nums, target)


if __name__ == "__main__":  # можно запустить и без pytest
    test_examples()
    test_random_against_each_other()
    print("all tests passed")
