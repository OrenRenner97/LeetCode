import random

import pytest

from algos import longest_palindrome
from algos.palindromes import maximal_palindromes, palindrome_radii

DNA = {"A": "T", "T": "A", "C": "G", "G": "C"}


@pytest.fixture(params=palindrome_radii.backends)
def backend(request):
    return request.param


def _is_pal(w, mirror=None):
    if mirror is None:
        return list(w) == list(w)[::-1]
    return all(mirror.get(w[-1 - i]) == w[i] for i in range(len(w)))


def _brute_longest(seq, mirror=None):
    # Эталон по контракту: самый длинный, при равенстве — самый левый; нет непустого → None.
    best = None
    for i in range(len(seq)):
        for j in range(i + 1, len(seq) + 1):
            if _is_pal(seq[i:j], mirror) and (best is None or j - i > best[1] - best[0]):
                best = (i, j)
    return best


def _brute_radii(seq, mirror=None):
    n = len(seq)
    radii = []
    for c in range(2 * n + 1):
        lo = hi = c // 2  # c чётное: пустой центр перед seq[c // 2]
        if c % 2:         # нечётное: центр — сам seq[c // 2]
            hi += 1
            if not _is_pal(seq[lo:hi], mirror):
                radii.append(0)
                continue
        while lo > 0 and hi < n and _is_pal(seq[lo - 1:hi + 1], mirror):
            lo, hi = lo - 1, hi + 1
        radii.append(hi - lo)
    return radii


@pytest.mark.parametrize(
    "seq, expected",
    [
        ("babad", (0, 3)),            # «bab» и «aba» → самый левый
        ("cbbd", (1, 3)),
        ("a", (0, 1)),
        ("ac", (0, 1)),
        ("", None),
        ("aaaa", (0, 4)),
        ("abacdfgdcaba", (0, 3)),     # ловушка «LCS с разворотом»
        ([3, 1, 4, 1, 3], (0, 5)),    # не только строки
    ],
)
def test_longest_contract(backend, seq, expected):
    assert longest_palindrome(seq, backend=backend) == expected


def test_any_hashable_python_only():
    events = [(1, "x"), (2, "y"), (1, "x")]
    assert longest_palindrome(events) == (0, 3)  # auto → python
    for b in set(palindrome_radii.backends) - {"python"}:
        with pytest.raises(TypeError):
            longest_palindrome(events, backend=b)
        with pytest.raises(TypeError):
            longest_palindrome([1, 2, 1], mirror={1: 2, 2: 1}, backend=b)  # mirror — только для строк


def test_backends_agree_on_types():
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(0)
    seqs = ["", "a", "абвба€😀😀€", rng.integers(0, 3, 300), rng.integers(-2**62, 2**62, 50)]
    for seq in seqs:
        ref = palindrome_radii(seq, backend="python")
        for b in palindrome_radii.backends:
            got = palindrome_radii(seq, backend=b)
            assert type(got) is list and got == ref, (b, seq)
            assert maximal_palindromes(seq, min_length=1, backend=b) == maximal_palindromes(seq, min_length=1,
                                                                                              backend="python")


def test_radii_example(backend):
    #            центры:  |a|b|a|
    assert palindrome_radii("aba", backend=backend) == [0, 1, 0, 3, 0, 1, 0]
    assert palindrome_radii("", backend=backend) == [0]


def test_random_against_brute(backend):
    rng = random.Random(5)
    for _ in range(600):
        seq = "".join(rng.choice("abc"[: rng.randint(1, 3)]) for _ in range(rng.randint(0, 20)))
        assert palindrome_radii(seq, backend=backend) == _brute_radii(seq), seq
        assert longest_palindrome(seq, backend=backend) == _brute_longest(seq), seq


def test_dna_reverse_complement(backend):
    # EcoRI: GAATTC — палиндром относительно комплемента, а обычным палиндромом не является.
    seq = "TTGAATTCAA"
    assert longest_palindrome(seq, mirror=DNA, backend=backend) == (0, 10)  # TTGAATTCAA тоже!
    assert longest_palindrome("CCGAATTCGG"[1:-1], mirror=DNA, backend=backend) == (0, 8)
    assert longest_palindrome("AAAA", mirror=DNA, backend=backend) is None   # A ↔ T, AAAA не сайт
    assert longest_palindrome("ACGN", mirror=DNA, backend=backend) == (1, 3)  # N не совпадает ни с чем


def test_dna_random_against_brute(backend):
    rng = random.Random(11)
    for _ in range(600):
        seq = "".join(rng.choice("ACGTN") for _ in range(rng.randint(0, 20)))
        assert palindrome_radii(seq, mirror=DNA, backend=backend) == _brute_radii(seq, DNA), seq
        assert longest_palindrome(seq, mirror=DNA, backend=backend) == _brute_longest(seq, DNA), seq


def test_self_mirrored_center(backend):
    # Отображение, где «x» переходит сам в себя: нечётные палиндромы возможны только с центром x.
    mirror = {"(": ")", ")": "(", "x": "x"}
    assert longest_palindrome("((x))", mirror=mirror, backend=backend) == (0, 5)
    assert longest_palindrome("(()", mirror=mirror, backend=backend) == (1, 3)


def test_maximal_palindromes(backend):
    seq = "ccGAATTCaaGGATCCtt"
    sites = maximal_palindromes(seq.upper(), min_length=6, mirror=DNA, backend=backend)
    assert [seq.upper()[s:e] for s, e in sites] == ["GAATTC", "AAGGATCCTT"]
    assert maximal_palindromes("abcba", min_length=2, backend=backend) == [(0, 5)]
    assert maximal_palindromes("abcba", min_length=1, backend=backend) == [(0, 1), (0, 5), (1, 2), (3, 4), (4, 5)]


def test_numpy_input():
    np = pytest.importorskip("numpy")
    assert longest_palindrome(np.array([5, 1, 2, 1, 7])) == (1, 4)


def test_linear_on_worst_case(backend):
    # "aaa…a" — худший случай для расширения от центра (O(n²) → минуты). Manacher — доли секунды.
    assert longest_palindrome("a" * 200_000, backend=backend) == (0, 200_000)


def test_validation():
    with pytest.raises(ValueError):
        longest_palindrome("ab", mirror={"a": "b"})            # b → ? : не инволюция
    with pytest.raises(ValueError):
        longest_palindrome("ab", mirror={"a": "b", "b": "c", "c": "a"})
    with pytest.raises(ValueError):
        maximal_palindromes("ab", min_length=0)
