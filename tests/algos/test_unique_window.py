import random

import pytest

from algos import longest_unique_window


@pytest.fixture(params=longest_unique_window.backends)
def backend(request):
    return request.param


def _brute(seq, k):
    # Эталон по контракту: самое длинное, при равенстве — самое левое.
    best = (0, 0)
    for i in range(len(seq)):
        for j in range(i + 1, len(seq) + 1):
            w = seq[i:j]
            if all(w.count(x) <= k for x in set(w)) and j - i > best[1] - best[0]:
                best = (i, j)
    return best


@pytest.mark.parametrize(
    "seq, k, expected",
    [
        ("abcabcbb", 1, (0, 3)),
        ("bbbbb", 1, (0, 1)),
        ("pwwkew", 1, (2, 5)),
        ("", 1, (0, 0)),
        ("abba", 1, (0, 2)),         # «ab» и «ba» одной длины → самое левое
        ("aabbcc", 2, (0, 6)),
        ("aaabbb", 2, (1, 5)),       # «aabb»
        ([7, 1, 7, 2, 3], 1, (1, 5)),  # не только строки
    ],
)
def test_contract(backend, seq, k, expected):
    assert longest_unique_window(seq, max_repeats=k, backend=backend) == expected


@pytest.mark.parametrize("k", [1, 2, 3])
def test_random_against_brute(backend, k):
    rng = random.Random(k)
    for _ in range(400):
        seq = [rng.choice("abcde"[: rng.randint(1, 5)]) for _ in range(rng.randint(0, 25))]
        assert longest_unique_window(seq, max_repeats=k, backend=backend) == _brute(seq, k)


def test_any_hashable():
    # Кортежи и прочие хэшируемые — только python (нативные принимают int/str, см. docstring).
    events = [("login", 1), ("view", 1), ("login", 1), ("buy", 2)]
    assert longest_unique_window(events) == (1, 4)
    if "numba" in longest_unique_window.backends:
        with pytest.raises(TypeError):
            longest_unique_window(events, backend="numba")


def test_validation():
    with pytest.raises(ValueError):
        longest_unique_window("abc", max_repeats=0)


# ---------- нативные backend'ы на массивах + batch ----------
np = pytest.importorskip("numpy")
from algos.sliding_window import longest_unique_window_batch  # noqa: E402


@pytest.mark.parametrize("k", [1, 2, 3])
def test_ndarray_large_vs_python(backend, k):
    rng = np.random.default_rng(k)
    for alpha, n in [(4, 5000), (100, 20_000), (10**12, 3000)]:  # 10^12: разреженные id → сжатие через сортировку
        seq = rng.integers(0, alpha, size=n)
        assert longest_unique_window(seq, max_repeats=k, backend=backend) == longest_unique_window(seq.tolist(), max_repeats=k, backend="python")


@pytest.fixture(params=longest_unique_window_batch.backends)
def batch_backend(request):
    return request.param


def _batch_case(rng, nq, max_len, alpha):
    lens = rng.integers(0, max_len + 1, size=nq)
    off = np.concatenate([[0], np.cumsum(lens)])
    return rng.integers(0, alpha, size=int(off[-1])), off


@pytest.mark.parametrize("k", [1, 2])
@pytest.mark.parametrize("nq, max_len", [(1, 50), (50, 30), (3000, 20)])  # 3000 > 1024: параллельный путь numba
def test_batch_matches_single(batch_backend, k, nq, max_len):
    rng = np.random.default_rng(nq + k)
    values, off = _batch_case(rng, nq, max_len, alpha=6)
    s, e = longest_unique_window_batch(values, off, max_repeats=k, backend=batch_backend)
    for q in range(nq):
        seg = values[off[q]:off[q + 1]].tolist()
        assert (s[q], e[q]) == longest_unique_window(seg, max_repeats=k, backend="python"), q


def test_batch_strings_and_isolation(batch_backend):
    # Одинаковые карты в разных источниках не мешают друг другу; пустой источник → (0, 0).
    values = ["c1", "c2", "c3", "c1", "c2", "c3"]
    s, e = longest_unique_window_batch(values, [0, 3, 3, 6], backend=batch_backend)
    assert s.tolist() == [0, 0, 0] and e.tolist() == [3, 0, 3]


def test_batch_validation():
    with pytest.raises(ValueError):
        longest_unique_window_batch([1, 2], [0, 1])
    with pytest.raises(ValueError):
        longest_unique_window_batch([1, 2], [0, 2], max_repeats=0)
