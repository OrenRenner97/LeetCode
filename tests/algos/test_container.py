import importlib.util
import random
from pathlib import Path

import numpy as np
import pytest

from algos import max_container
from algos.two_pointers import Container

ROOT = Path(__file__).resolve().parents[2]


def _load_solution():
    path = ROOT / "problems" / "0011_container_with_most_water" / "solution.py"
    spec = importlib.util.spec_from_file_location("p11_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Solution()


def _brute(h, xs=None, min_width=0):
    xs = list(range(len(h))) if xs is None else xs
    areas = [(xs[j] - xs[i]) * min(h[i], h[j]) for i in range(len(h)) for j in range(i + 1, len(h))
             if xs[j] - xs[i] >= min_width]
    return max(areas) if areas else None


def _check(res, h, xs=None, min_width=0):
    expected = _brute(h, xs, min_width)
    if expected is None:
        assert res is None
        return
    xs = list(range(len(h))) if xs is None else xs
    i, j, area = res
    assert i < j and xs[j] - xs[i] >= min_width
    assert area == expected == (xs[j] - xs[i]) * min(h[i], h[j])   # пара действительно даёт свою площадь


def test_leetcode():
    assert max_container([1, 8, 6, 2, 5, 4, 8, 3, 7]) == Container(1, 8, 49)
    assert max_container([1, 1]).area == 1
    sol = _load_solution()
    rng = random.Random(11)
    for _ in range(500):
        h = [rng.randint(0, 10_000) for _ in range(rng.randint(2, 300))]
        assert max_container(h).area == sol.maxArea(h)


def test_random_against_brute():
    rng = random.Random(1)
    for _ in range(3000):
        n = rng.randint(0, 25)
        h = [rng.randint(0, rng.choice([2, 10, 1000])) for _ in range(n)]
        xs = sorted(rng.sample(range(100), n)) if rng.random() < 0.5 else None
        min_width = rng.choice([0, 0, 1, 5, 20, 60])
        _check(max_container(h, xs, min_width=min_width), h, xs, min_width)


def test_floats():
    h = [1.5, 0.5, 2.5, 2.0]
    xs = [0.0, 0.7, 1.1, 3.6]
    res = max_container(h, xs)
    _check(res, h, xs)
    assert res == Container(0, 3, 3.6 * 1.5)


def test_none_cases():
    assert max_container([]) is None and max_container([5]) is None
    assert max_container([5, 5, 5], min_width=3) is None            # ширина максимум 2
    assert max_container([0, 0]) == Container(0, 1, 0)              # пара есть, площадь 0 — это не None
    assert max_container([3, 4], [0, 10], min_width=10) == Container(0, 1, 30)


def test_numpy_and_large():
    rng = np.random.default_rng(0)
    h = rng.integers(0, 10_000, 100_000)
    res = max_container(h)
    assert isinstance(res.area, int) and res.area == _load_solution().maxArea(h.tolist())
    assert max_container([10_000] * 100_000) == Container(0, 99_999, 10_000 * 99_999)


def test_validation():
    for bad in ("abc", [1, "2"], [1, True], [1, None]):
        with pytest.raises(TypeError):
            max_container(bad)
    for bad in ([1, -1], [1, float("nan")], [1, float("inf")]):
        with pytest.raises(ValueError):
            max_container(bad)
    with pytest.raises(ValueError):
        max_container([1, 2, 3], [0, 1])
    for xs in ([0, 0, 1], [0, 2, 1], [0, 1, float("inf")]):
        with pytest.raises(ValueError):
            max_container([1, 2, 3], xs)
    with pytest.raises(ValueError):
        max_container([1, 2], min_width=-1)
    with pytest.raises(TypeError):
        max_container([1, 2], min_width=True)
