import random

import pytest

np = pytest.importorskip("numpy")

from algos import find_pair_with_sum  # noqa: E402
from algos.hashing import find_pairs_batch  # noqa: E402


@pytest.fixture(params=find_pairs_batch.backends)
def backend(request):
    return request.param


def _random_batch(rng, q, max_len, lo=-30, hi=30):
    segs = [[rng.randint(lo, hi) for _ in range(rng.randint(0, max_len))] for _ in range(q)]
    targets = [rng.randint(2 * lo, 2 * hi) for _ in range(q)]
    offsets = [0]
    for s in segs:
        offsets.append(offsets[-1] + len(s))
    return segs, [x for s in segs for x in s], offsets, targets


def _expected(segs, targets):
    res = [find_pair_with_sum(s, t, backend="python") for s, t in zip(segs, targets)]
    return [r[0] if r else -1 for r in res], [r[1] if r else -1 for r in res]


def test_matches_single_query(backend):
    rng = random.Random(3)
    for _ in range(30):
        segs, flat, off, targets = _random_batch(rng, rng.randint(1, 50), 25)
        i, j = find_pairs_batch(flat, off, targets, backend=backend)
        assert (i.tolist(), j.tolist()) == _expected(segs, targets)


def test_segments_do_not_leak(backend):
    # 5 + 5 = 10, но пятёрки в разных задачах → пары нет.
    i, j = find_pairs_batch([5, 5], [0, 1, 2], [10, 10], backend=backend)
    assert i.tolist() == [-1, -1] and j.tolist() == [-1, -1]


def test_big_kopecks(backend):
    rng = random.Random(4)
    segs, flat, off, targets = _random_batch(rng, 40, 30, lo=-(2**38), hi=2**38)
    for q, s in enumerate(segs):  # гарантируем пару в половине задач
        if len(s) >= 2 and q % 2:
            targets[q] = s[0] + s[-1]
    i, j = find_pairs_batch(flat, off, targets, backend=backend)
    assert (i.tolist(), j.tolist()) == _expected(segs, targets)


def test_empty_and_bad_offsets(backend):
    i, j = find_pairs_batch([], [0, 0, 0], [1, 2], backend=backend)
    assert i.tolist() == [-1, -1]
    with pytest.raises(ValueError):
        find_pairs_batch([1, 2], [0, 1], [3], backend=backend)
