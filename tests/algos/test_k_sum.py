import importlib.util
import random
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from algos import k_sum

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    path = ROOT / "problems" / "0015_3sum" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"p15_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _brute(values, target=0, k=3):
    return sorted({tuple(sorted(c)) for c in combinations(values, k) if sum(c) == target})


def test_leetcode():
    assert k_sum([-1, 0, 1, 2, -1, -4]) == [(-1, -1, 2), (-1, 0, 1)]
    assert k_sum([0, 1, 1]) == []
    assert k_sum([0, 0, 0]) == [(0, 0, 0)]


def test_4sum_leetcode_18():
    assert k_sum([1, 0, -1, 0, -2, 2], k=4) == [(-2, -1, 1, 2), (-2, 0, 0, 2), (-1, 0, 0, 1)]
    assert k_sum([2, 2, 2, 2, 2], 8, k=4) == [(2, 2, 2, 2)]


def test_small_k():
    assert k_sum([3, 1, 3, 2], 3, k=1) == [(3,)]
    assert k_sum([3, 1, 3, 2], 5, k=1) == []
    assert k_sum([1, 2, 3, 4, 2], 4, k=2) == [(1, 3), (2, 2)]
    assert k_sum([2, 1], 4, k=2) == []                  # 2 + 2, но двойка одна


def test_multiplicity():
    assert k_sum([0, 0]) == []                          # k > n
    assert k_sum([0, 0, 0, 0]) == [(0, 0, 0)]
    assert k_sum([-4, 2, 2]) == [(-4, 2, 2)]
    assert k_sum([-4, 2]) == []
    assert k_sum([5, 5, 5], 15) == [(5, 5, 5)]
    assert k_sum([5, 5], 15) == []
    assert k_sum([5] * 10, 15) == [(5, 5, 5)]


def test_target_and_order():
    vals = [7, -3, 4, 0, 4, 1, 2, -1, 3]
    for t in range(-6, 16):
        assert k_sum(vals, t) == _brute(vals, t)


def test_random_against_brute():
    rng = random.Random(15)
    for _ in range(3000):
        n = rng.randint(0, 11)
        lim = rng.choice([1, 2, 5, 20])
        vals = [rng.randint(-lim, lim) for _ in range(n)]
        k = rng.randint(1, 5)
        t = rng.randint(-2 * lim, 2 * lim)
        assert k_sum(vals, t, k=k) == _brute(vals, t, k), (vals, t, k)


def test_against_leetcode_solution():
    solution = _load("solution").Solution()
    rng = random.Random(1)
    for _ in range(200):
        vals = [rng.randint(-30, 30) for _ in range(rng.randint(3, 40))]
        assert k_sum(vals) == sorted(tuple(sorted(t)) for t in solution.threeSum(vals))


def test_max_leetcode_size():
    sort_two_pointers = _load("alternatives").SortTwoPointers()
    rng = random.Random(2)
    for vals in ([rng.randint(-10**5, 10**5) for _ in range(3000)], [rng.randint(-50, 50) for _ in range(3000)],
                 [0] * 3000, list(range(-200, 200))):
        assert k_sum(vals) == sorted(map(tuple, sort_two_pointers.threeSum(vals)))


def test_big_ints():
    big = 10**30
    assert k_sum([big, -big, 0, 1]) == [(-big, 0, big)]


def test_inputs():
    assert k_sum(np.array([-1, 0, 1, 2, -1, -4])) == [(-1, -1, 2), (-1, 0, 1)]
    assert k_sum([np.int64(-1), 0, 1]) == [(-1, 0, 1)]
    assert k_sum((x for x in [-1, 0, 1])) == [(-1, 0, 1)]
    assert k_sum([1, 2, 3], np.int32(6)) == [(1, 2, 3)]
    out = k_sum([-1, 0, 1, np.int64(0)], k=np.int64(2))
    assert out == [(-1, 1), (0, 0)] and all(type(x) is int for t in out for x in t)
    vals = [3, -1, -2]
    k_sum(vals)
    assert vals == [3, -1, -2]


def test_errors():
    with pytest.raises(TypeError):
        k_sum([0.5, -0.5, 0])
    with pytest.raises(TypeError):
        k_sum([True, False, 0])
    with pytest.raises(TypeError):
        k_sum("012")
    with pytest.raises(TypeError):
        k_sum([1, 2, 3], 1.0)
    with pytest.raises(TypeError):
        k_sum([1, 2, 3], k=3.0)
    with pytest.raises(ValueError):
        k_sum([1, 2, 3], k=0)
