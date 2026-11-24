import importlib.util
import os.path
import random
from pathlib import Path

import pytest

from algos import common_prefix


def _solution():
    path = Path(__file__).resolve().parents[2] / "problems" / "0014_longest_common_prefix" / "solution.py"
    spec = importlib.util.spec_from_file_location("p14_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Solution()


def _ref(seqs):
    k = 0
    while all(k < len(s) and s[k] == seqs[0][k] for s in seqs):
        k += 1
    return seqs[0][:k]


def _ref_sep(seqs, sep):
    """Эталон: разбить на компоненты, взять общий префикс компонент, склеить обратно."""
    p = _ref(seqs)
    k = len(p)
    while k > 0:
        if all(len(s) == k or s[k:k + len(sep)] == sep for s in seqs) or p[k - len(sep):k] == sep:
            break
        k -= 1
    return p[:k]


def test_leetcode_examples():
    assert common_prefix(["flower", "flow", "flight"]) == "fl"
    assert common_prefix(["dog", "racecar", "car"]) == ""


def test_random_against_solution_and_reference():
    sol = _solution()
    rng = random.Random(14)
    for _ in range(5000):
        base = "".join(rng.choice("ab") for _ in range(rng.randint(0, 8)))
        strs = [base[:rng.randint(0, len(base))] + "".join(rng.choice("abc") for _ in range(rng.randint(0, 4)))
                for _ in range(rng.randint(1, 8))]
        expected = _ref(strs)
        assert common_prefix(strs) == expected == sol.longestCommonPrefix(strs), strs
        assert common_prefix(s.encode() for s in strs) == expected.encode(), strs
        assert common_prefix([list(s) for s in strs]) == list(expected), strs
        assert common_prefix(tuple(s) for s in strs) == tuple(expected), strs


def test_long_strings():
    rng = random.Random(1)
    base = "".join(rng.choice("xyz") for _ in range(100_000))
    strs = [base + "".join(rng.choice("ab") for _ in range(10)) for _ in range(100)]
    assert common_prefix(strs) == _ref(strs)
    assert common_prefix([base] * 50) == base
    assert common_prefix([base, base[:-1] + "#"]) == base[:-1]


def test_empty_and_trivial():
    assert common_prefix([]) is None
    assert common_prefix(iter([])) is None
    assert common_prefix(["abc"]) == "abc"
    assert common_prefix([""]) == ""
    assert common_prefix(["abc", ""]) == ""
    assert common_prefix([b"ab", b"ac"]) == b"a"
    assert common_prefix([[1, 2], [1, 3]]) == [1]
    assert common_prefix([(), (1,)]) == ()


def test_unorderable_list_elements():
    a = [{"k": 1}, {"k": 2}, "x"]
    b = [{"k": 1}, {"k": 2}, 5]
    assert common_prefix([a, b]) == [{"k": 1}, {"k": 2}]


def test_result_type_matches_input():
    assert type(common_prefix(["a", "b"])) is str
    assert type(common_prefix([b"a", b"b"])) is bytes
    assert type(common_prefix([[1], [2]])) is list
    assert type(common_prefix([(1,), (2,)])) is tuple


def test_sep_paths():
    assert os.path.commonprefix(["/usr/lib", "/usr/local"]) == "/usr/l"      # проблема, которую решает sep
    assert common_prefix(["/usr/lib", "/usr/local"], sep="/") == "/usr/"
    assert common_prefix(["/usr/lib", "/usr/lib/x"], sep="/") == "/usr/lib"
    assert common_prefix(["/usr/lib", "/usr/lib"], sep="/") == "/usr/lib"
    assert common_prefix(["/usr/lib/", "/usr/lib/x"], sep="/") == "/usr/lib/"
    assert common_prefix(["abc", "abd"], sep="/") == ""
    assert common_prefix(["a.b.c", "a.b.cd"], sep=".") == "a.b."
    assert common_prefix(["a::b:c", "a::b:d"], sep="::") == "a::"
    assert common_prefix(["logs/2026/11/a.gz", "logs/2026/12/b.gz", "logs/2026/1x"], sep="/") == "logs/2026/"
    assert common_prefix([b"s3://bkt/a/1", b"s3://bkt/a/2"], sep=b"/") == b"s3://bkt/a/"
    assert common_prefix([["a", "/", "bc"], ["a", "/", "bd"]], sep="/") == ["a", "/"]     # sep — элемент списка
    assert common_prefix([["usr", "lib", "x"], ["usr", "lib", "y"]]) == ["usr", "lib"]   # сегменты: sep не нужен


def test_sep_random_against_reference():
    rng = random.Random(7)
    for _ in range(5000):
        base = "".join(rng.choice("a/b") for _ in range(rng.randint(0, 8)))
        strs = [base[:rng.randint(0, len(base))] + "".join(rng.choice("ab/") for _ in range(rng.randint(0, 4)))
                for _ in range(rng.randint(1, 6))]
        assert common_prefix(strs, sep="/") == _ref_sep(strs, "/"), strs


@pytest.mark.parametrize("bad", [[1, 2], ["a", b"a"], [["a"], ("a",)], ["a", None], [bytearray(b"a")]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        common_prefix(bad)


def test_sep_errors():
    with pytest.raises(TypeError):
        common_prefix(["a/b"], sep=b"/")
    with pytest.raises(ValueError):
        common_prefix(["a/b"], sep="")
