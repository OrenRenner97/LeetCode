import itertools
import random

import pytest

from algos import BackendUnavailable, find_pair_with_sum

BACKENDS = find_pair_with_sum.backends


def _brute(values, target):
    # Эталон по контракту: минимальный j, затем минимальный i.
    for j in range(len(values)):
        for i in range(j):
            if values[i] + values[j] == target:
                return i, j
    return None


@pytest.fixture(params=BACKENDS)
def backend(request):
    return request.param


@pytest.mark.parametrize(
    "values, target, expected",
    [
        ([2, 7, 11, 15], 9, (0, 1)),
        ([3, 2, 4], 6, (1, 2)),
        ([3, 3], 6, (0, 1)),
        ([1, 2, 3], 100, None),
        ([], 0, None),
        ([5], 10, None),
        ([5, 5, 5], 10, (0, 1)),   # первое вхождение
        ([1, 9, 2, 8], 10, (0, 1)),  # минимальный j, а не «первая найденная»
        ([4, 1, 9, 6], 10, (1, 2)),  # (0, 3) тоже пара, но завершается позже
    ],
)
def test_contract(backend, values, target, expected):
    assert find_pair_with_sum(values, target, backend=backend) == expected


def test_matches_brute_on_random(backend):
    rng = random.Random(0)
    for _ in range(500):
        values = [rng.randint(-20, 20) for _ in range(rng.randint(0, 30))]
        target = rng.randint(-40, 40)
        assert find_pair_with_sum(values, target, backend=backend) == _brute(values, target)


def test_accepts_any_sequence(backend):
    assert find_pair_with_sum((1, 2, 3), 5, backend=backend) == (1, 2)
    assert find_pair_with_sum(range(10), 17, backend=backend) == (8, 9)


def test_unknown_backend():
    with pytest.raises(BackendUnavailable):
        find_pair_with_sum([1, 2], 3, backend="quantum")


def test_env_backend(monkeypatch):
    monkeypatch.setenv("ALGOS_BACKEND", "quantum")
    with pytest.raises(BackendUnavailable):
        find_pair_with_sum([1, 2], 3)
    monkeypatch.setenv("ALGOS_BACKEND", "python")
    assert find_pair_with_sum([1, 2], 3) == (0, 1)


def test_all_backends_agree():
    for a, b in itertools.combinations(BACKENDS, 2):
        rng = random.Random(1)
        for _ in range(100):
            values = [rng.randint(-50, 50) for _ in range(40)]
            t = rng.randint(-100, 100)
            assert find_pair_with_sum(values, t, backend=a) == find_pair_with_sum(values, t, backend=b)


def test_large_values_and_collisions(backend):
    # Большие и отрицательные числа (проверка хэша uint64), много коллизий, n до 3000.
    rng = random.Random(2)
    big = 2**61
    for _ in range(20):
        values = [rng.choice([rng.randint(-big, big), rng.randint(-5, 5)]) for _ in range(rng.randint(2, 3000))]
        a, b = rng.sample(range(len(values)), 2)
        target = values[a] + values[b]
        assert find_pair_with_sum(values, target, backend=backend) == _brute_fast(values, target)


def test_numpy_input(backend):
    np = pytest.importorskip("numpy")
    values = np.array([10, 20, 30, 40], dtype=np.int64)
    assert find_pair_with_sum(values, 70, backend=backend) == (2, 3)


def _brute_fast(values, target):
    # Эталон по контракту за O(n): минимальный j, для него самое раннее вхождение дополнения.
    first = {}
    for j, x in enumerate(values):
        if target - x in first:
            return first[target - x], j
        first.setdefault(x, j)
    return None


def test_auto_respects_min_n():
    from algos._dispatch import Dispatcher

    d = Dispatcher("t", priority=("cuda", "numba", "python"))
    d.register("python")(lambda: "python")
    d.register("cuda", min_n=1000)(lambda: "cuda")
    assert d.resolve(None, 10)() == "python"
    assert d.resolve(None, 1000)() == "cuda"
    assert d.resolve("python", 10**6)() == "python"  # явный выбор важнее порогов
