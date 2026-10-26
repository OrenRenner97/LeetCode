import random

import pytest

from algos.arithmetic import add_digits, from_digits, to_digits


@pytest.fixture(params=add_digits.backends)
def backend(request):
    return request.param


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ([2, 4, 3], [5, 6, 4], [7, 0, 8]),
        ([0], [0], [0]),
        ([9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9], [8, 9, 9, 9, 0, 0, 0, 1]),
        ([1], [9, 9, 9], [0, 0, 0, 1]),
        ([], [], [0]),            # пустой вход = 0
        ([], [4, 2], [4, 2]),
        ([3, 0, 0], [1], [4]),    # ведущие нули на входе → нормализованный выход
        ([0, 0], [0], [0]),
    ],
)
def test_contract(backend, a, b, expected):
    assert add_digits(a, b, backend=backend) == expected


@pytest.mark.parametrize("base", [2, 3, 10, 16, 256, 2**32])
def test_random_against_int(backend, base):
    rng = random.Random(base)
    for _ in range(200):
        x, y = rng.getrandbits(rng.randint(0, 600)), rng.getrandbits(rng.randint(0, 600))
        got = add_digits(to_digits(x, base), to_digits(y, base), base=base, backend=backend)
        assert got == to_digits(x + y, base)
        assert from_digits(got, base) == x + y


def test_inputs_not_mutated(backend):
    a, b = [9, 9], [1]
    add_digits(a, b, backend=backend)
    assert (a, b) == ([9, 9], [1])


def test_accepts_tuples(backend):
    assert add_digits((5,), (5,), backend=backend) == [0, 1]


@pytest.mark.parametrize("a, base", [([10], 10), ([-1], 10), ([2], 2), ([1], 1)])
def test_validation(backend, a, base):
    with pytest.raises(ValueError):
        add_digits(a, [0], base=base, backend=backend)


def test_to_from_digits_roundtrip():
    for n in [0, 1, 9, 10, 255, 256, 10**50]:
        for base in [2, 10, 256]:
            assert from_digits(to_digits(n, base), base) == n
    assert to_digits(0) == [0]
    with pytest.raises(ValueError):
        to_digits(-5)


# ---------- sub_digits ----------
from algos.arithmetic import sub_digits  # noqa: E402


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ([7, 0, 8], [5, 6, 4], [2, 4, 3]),
        ([0, 0, 0, 1], [1], [9, 9, 9]),   # заём бежит через нули
        ([5], [5], [0]),
        ([0, 1], [0, 1], [0]),
        ([3], [], [3]),
        ([4], [4, 0, 0], [0]),            # ведущие нули у вычитаемого
    ],
)
def test_sub_contract(a, b, expected):
    for backend in sub_digits.backends:
        assert sub_digits(a, b, backend=backend) == expected


@pytest.mark.parametrize("base", [2, 10, 2**32, 2**64])
def test_sub_random_against_int(base):
    rng = random.Random(base + 1)
    for _ in range(200):
        x, y = rng.getrandbits(rng.randint(0, 600)), rng.getrandbits(rng.randint(0, 600))
        x, y = max(x, y), min(x, y)
        for backend in sub_digits.backends:
            assert sub_digits(to_digits(x, base), to_digits(y, base), base=base, backend=backend) == to_digits(x - y, base)


def test_sub_negative_raises():
    with pytest.raises(ValueError):
        sub_digits([1], [2])
    with pytest.raises(ValueError):
        sub_digits([9, 9], [0, 0, 1])


# ---------- нативные backend'ы: большие основания, массивы, цепочки переноса ----------
np = pytest.importorskip("numpy")


@pytest.mark.parametrize("base", [2**63, 2**64, 2**70])  # 2^70: нативные откатываются на python
def test_huge_bases(backend, base):
    rng = random.Random(base % 1000)
    for _ in range(100):
        x, y = rng.getrandbits(rng.randint(0, 2000)), rng.getrandbits(rng.randint(0, 2000))
        assert add_digits(to_digits(x, base), to_digits(y, base), base=base, backend=backend) == to_digits(x + y, base)


@pytest.mark.parametrize("base", [10, 2**64])
@pytest.mark.parametrize("n", [1, 7, 1000, 300_000])  # 300k > порога, где numba режет на куски
def test_carry_chains(backend, base, n):
    # Худший случай для параллельных сумматоров: перенос бежит через весь массив и все границы кусков.
    top = base - 1
    assert add_digits([top] * n, [1], base=base, backend=backend) == [0] * n + [1]
    # Цепочки, которые обрываются в случайных местах.
    rng = random.Random(n)
    a = [top if rng.random() < 0.9 else rng.randrange(base) for _ in range(n)]
    b = [top if rng.random() < 0.9 else rng.randrange(base) for _ in range(n)]
    assert add_digits(a, b, base=base, backend=backend) == add_digits(a, b, base=base, backend="python")


def test_ndarray_in_ndarray_out(backend):
    a = np.array([2**64 - 1, 5], dtype=np.uint64)
    b = np.array([1], dtype=np.uint64)
    out = add_digits(a, b, base=2**64, backend=backend)
    assert isinstance(out, np.ndarray) and out.dtype == np.uint64
    assert out.tolist() == [0, 6]
    assert isinstance(add_digits([1], [2], backend=backend), list)  # list → list


def test_ndarray_validation():
    with pytest.raises(ValueError):
        add_digits(np.array([10], dtype=np.uint64), np.array([1], dtype=np.uint64), base=10)


# ---------- sum_limbs ----------
from algos.arithmetic import sum_limbs  # noqa: E402


@pytest.mark.parametrize("sb", sum_limbs.backends)
@pytest.mark.parametrize("base", [10, 2**32, 2**64])
def test_sum_limbs(sb, base):
    rng = random.Random(base % 997)
    for n in [1, 2, 50, 5000]:
        L = 4
        nums = [rng.randrange(base**L) for _ in range(n)]
        rows = [(to_digits(x, base) + [0] * L)[:L] for x in nums]
        assert sum_limbs(rows, base=base, backend=sb) == to_digits(sum(nums), base)
        arr = np.array(rows, dtype=np.uint64)
        assert sum_limbs(arr, base=base, backend=sb) == to_digits(sum(nums), base)


@pytest.mark.parametrize("sb", sum_limbs.backends)
def test_sum_limbs_all_max(sb):
    # 10 000 чисел 2^256 - 1: каждая половина-столбец близка к максимуму.
    rows = np.full((10_000, 4), 2**64 - 1, dtype=np.uint64)
    assert sum_limbs(rows, backend=sb) == to_digits(10_000 * (2**256 - 1), 2**64)


def test_sum_limbs_edge():
    assert sum_limbs([]) == [0]
    assert sum_limbs([[0, 0]]) == [0]
    with pytest.raises(ValueError):
        sum_limbs([[1, 2], [3]], backend="python")
