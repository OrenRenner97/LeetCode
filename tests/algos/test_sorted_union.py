import random
import statistics
from decimal import Decimal

import pytest

from algos import kth_of_many_sorted, kth_of_sorted, kth_of_two_sorted, median_of_sorted


def _merged(*arrays):
    return sorted(x for arr in arrays for x in arr)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ([1, 3], [2], 2.0),
        ([1, 2], [3, 4], 2.5),
        ([], [1], 1.0),
        ([2], [], 2.0),
        ([1, 2, 3], [100, 200, 300], 51.5),
        ([-5, -3, -1], [-2], -2.5),
        ([1, 1, 1], [1, 1, 1, 1], 1.0),
    ],
)
def test_median_leetcode_cases(a, b, expected):
    got = median_of_sorted(a, b)
    assert got == expected and isinstance(got, float)


def test_median_empty_is_none():
    assert median_of_sorted() is None
    assert median_of_sorted([], []) is None
    assert median_of_sorted([], [], []) is None


def test_median_type_follows_input():
    assert median_of_sorted([Decimal("1.10")], [Decimal("2.25")]) == Decimal("1.675")
    assert isinstance(median_of_sorted([Decimal("1.10")], [Decimal("2.25")]), Decimal)
    assert isinstance(median_of_sorted([Decimal("3")]), Decimal)  # нечётная длина — тот же тип
    assert median_of_sorted([0.5], [1.5, 2.5]) == 1.5


def test_median_one_and_many_arrays():
    assert median_of_sorted([1, 2, 3, 4]) == 2.5
    assert median_of_sorted([1, 9], [2, 8], [3, 7], [5]) == 5.0
    assert median_of_sorted([1, 9], [], [2, 8], []) == 5.0  # пустые не мешают; 2 непустых → разрез


def test_kth_of_two_contract():
    a, b = [1, 4, 4, 9], [2, 4, 10]
    merged = _merged(a, b)
    assert [kth_of_two_sorted(a, b, k) for k in range(len(merged))] == merged
    assert kth_of_two_sorted(a, b, -1) is None
    assert kth_of_two_sorted(a, b, len(merged)) is None
    assert kth_of_two_sorted([], [], 0) is None


def test_kth_of_two_any_comparable():
    # Нет ±inf внутри — поэтому строки и кортежи тоже работают.
    assert kth_of_two_sorted(["apple", "kiwi"], ["banana", "fig"], 2) == "fig"
    assert kth_of_two_sorted([(1, "b"), (2, "a")], [(1, "c")], 1) == (1, "c")


def test_random_against_sort():
    rng = random.Random(42)
    for _ in range(2000):
        hi = rng.choice([2, 30, 10**6])
        arrays = [sorted(rng.randint(-hi, hi) for _ in range(rng.randint(0, 10))) for _ in range(rng.randint(1, 5))]
        merged = _merged(*arrays)
        if merged:
            assert median_of_sorted(*arrays) == float(statistics.median(merged)), arrays
        else:
            assert median_of_sorted(*arrays) is None
        for k in range(-1, len(merged) + 1):
            expected = merged[k] if 0 <= k < len(merged) else None
            assert kth_of_many_sorted(arrays, k) == expected, (arrays, k)
            assert kth_of_sorted(*arrays, k=k) == expected, (arrays, k)
            if len(arrays) >= 2:
                assert kth_of_two_sorted(arrays[0], arrays[1], k) == (
                    _merged(arrays[0], arrays[1])[k] if 0 <= k < len(arrays[0]) + len(arrays[1]) else None
                )


def test_numpy_input():
    np = pytest.importorskip("numpy")
    a = np.array([1, 5, 9], dtype=np.int64)
    b = np.array([2, 3], dtype=np.int64)
    c = np.array([2**62, 2**62 + 1], dtype=np.int64)  # (lo + hi) переполнил бы int64
    assert median_of_sorted(a, b) == 3.0
    assert kth_of_two_sorted(a, b, 4) == 9
    assert kth_of_many_sorted([a, b, c], 6) == 2**62 + 1
    assert median_of_sorted(a, b, c) == 5.0


def test_many_requires_integers():
    with pytest.raises(TypeError):
        kth_of_many_sorted([[0.5, 1.5], [1.0]], 0)
    with pytest.raises(TypeError):
        median_of_sorted([0.5], [1.5], [2.5])
    with pytest.raises(TypeError):
        kth_of_many_sorted([[False, True]], 0)


def test_check_sorted():
    with pytest.raises(ValueError, match="№1"):
        median_of_sorted([1, 2], [5, 3], check_sorted=True)
    with pytest.raises(ValueError):
        kth_of_two_sorted([3, 1], [2], 0, check_sorted=True)
    with pytest.raises(ValueError):
        kth_of_many_sorted([[1], [3, 2]], 0, check_sorted=True)
    assert median_of_sorted([1, 2], [3], check_sorted=True) == 2.0


def test_kth_of_sorted_picks_algorithm():
    # 1–2 непустые → разрез, поэтому подходят и не целые; 3+ → только целые.
    assert kth_of_sorted([Decimal("1.5")], [], [Decimal("0.5")], k=1) == Decimal("1.5")
    assert kth_of_sorted(k=0) is None
    with pytest.raises(TypeError):
        kth_of_sorted([0.5], [1.5], [2.5], k=0)


# ---------- все backend'ы (шаг 3): нативные получают int64-массивы, остальное — python ----------
BACKENDS = sorted(set(kth_of_two_sorted.backends) | set(kth_of_many_sorted.backends))


@pytest.fixture(params=BACKENDS)
def backend(request):
    return request.param


def test_backends_against_sort(backend):
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(3)
    for _ in range(500):
        hi = int(rng.choice([2, 30, 10**6, 2**62]))
        arrays = [np.sort(rng.integers(-hi, hi, size=int(rng.integers(0, 12)))) for _ in range(int(rng.integers(1, 6)))]
        merged = _merged(*(a.tolist() for a in arrays))
        if not merged:
            assert median_of_sorted(*arrays, backend=backend) is None
            continue
        assert median_of_sorted(*arrays, backend=backend) == float(statistics.median(merged))
        for k in range(len(merged)):
            assert kth_of_many_sorted(arrays, k, backend=backend) == merged[k]
            assert kth_of_sorted(*arrays, k=k, backend=backend) == merged[k]
        if len(arrays) >= 2:
            two = _merged(arrays[0].tolist(), arrays[1].tolist())
            for k in range(len(two)):
                assert kth_of_two_sorted(arrays[0], arrays[1], k, backend=backend) == two[k]


def test_backends_int64_extremes(backend):
    np = pytest.importorskip("numpy")
    lo, hi = np.iinfo(np.int64).min, np.iinfo(np.int64).max
    a = np.array([lo, lo + 1, 0], dtype=np.int64)
    b = np.array([hi - 1, hi], dtype=np.int64)
    c = np.array([-1, 1], dtype=np.int64)
    merged = sorted([int(x) for x in (*a, *b, *c)])
    for k in range(len(merged)):
        assert kth_of_many_sorted([a, b, c], k, backend=backend) == merged[k]  # (lo + hi) переполнил бы int64
    assert kth_of_two_sorted(a, b, 4, backend=backend) == hi


def test_backends_small_int_dtypes(backend):
    np = pytest.importorskip("numpy")
    a, b, c = (np.array(x, dtype=np.int16) for x in ([1, 5, 9], [2, 3], [4]))
    assert median_of_sorted(a, b, backend=backend) == 3.0
    assert kth_of_many_sorted([a, b, c], 3, backend=backend) == 4


def test_unsorted_input_never_raises_and_backends_agree(backend):
    # Разрез существует для любого входа (доказательство в _cut): ответ бессмысленный, но не исключение,
    # и все backend'ы обязаны выдать одно и то же — иначе разошлись реализации.
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(11)
    for _ in range(2000):
        a = rng.integers(0, 10, size=int(rng.integers(0, 8)))
        b = rng.integers(0, 10, size=int(rng.integers(1, 8)))
        for k in range(len(a) + len(b)):
            got = kth_of_two_sorted(a, b, k, backend=backend)
            assert got == kth_of_two_sorted(a.tolist(), b.tolist(), k, backend="python"), (a, b, k)


def test_backends_fall_back_to_python_for_other_inputs(backend):
    # Списки, Decimal, float-массивы, срезы с шагом: нативный backend не подходит → python, без ошибки.
    assert median_of_sorted([1, 2], [3], backend=backend) == 2.0
    assert kth_of_two_sorted([Decimal("1.5")], [Decimal("0.5")], 0, backend=backend) == Decimal("0.5")
    np = pytest.importorskip("numpy")
    assert median_of_sorted(np.array([0.5, 1.5]), np.array([1.0]), backend=backend) == 1.0
    strided = np.arange(20)[::2]
    assert kth_of_many_sorted([strided, np.arange(3), np.arange(5)], 4, backend=backend) == 1


def test_unknown_backend():
    from algos import BackendUnavailable

    with pytest.raises(BackendUnavailable):
        median_of_sorted([1], [2], backend="quantum")  # даже для списков, которые ушли бы в python
    with pytest.raises(BackendUnavailable):
        kth_of_many_sorted([[1], [2], [3]], 0, backend="quantum")
