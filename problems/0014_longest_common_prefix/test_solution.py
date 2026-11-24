import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    (["flower", "flow", "flight"], "fl"),
    (["dog", "racecar", "car"], ""),
    (["ab", "a"], "a"), (["a"], "a"), ([""], ""), (["", "abc"], ""), (["abc", ""], ""),
    (["abc", "abc", "abc"], "abc"), (["abc", "abcd", "ab"], "ab"),
    (["interspecies", "interstellar", "interstate"], "inters"),
    (["throne", "throne"], "throne"), (["a", "b"], ""), (["aa", "ab", "b"], ""),
    (["prefix", "pre", "prefixes", "prepare"], "pre"),
]


def reference(strs: list[str]) -> str:
    k = 0
    while all(k < len(s) and s[k] == strs[0][k] for s in strs):
        k += 1
    return strs[0][:k]


def test_examples():
    for name, cls in IMPLS.items():
        for strs, expected in CASES:
            assert cls().longestCommonPrefix(list(strs)) == expected, (name, strs)


def test_random_against_reference():
    rng = random.Random(14)
    for _ in range(3000):
        n = rng.randint(1, 8)
        base = "".join(rng.choice("ab") for _ in range(rng.randint(0, 6)))
        strs = [base[:rng.randint(0, len(base))] + "".join(rng.choice("abc") for _ in range(rng.randint(0, 4)))
                for _ in range(n)]
        expected = reference(strs)
        for name, cls in IMPLS.items():
            assert cls().longestCommonPrefix(list(strs)) == expected, (name, strs)


def test_max_constraints():
    rng = random.Random(1)
    common = "".join(rng.choice("xyz") for _ in range(150))
    inputs = [
        ["a" * 200] * 200,
        [common + "".join(rng.choice("ab") for _ in range(50)) for _ in range(200)],
        ["q" * 200] * 199 + ["z" + "q" * 199],
    ]
    for strs in inputs:
        expected = reference(strs)
        for name, cls in IMPLS.items():
            assert cls().longestCommonPrefix(strs) == expected, name


def test_input_not_mutated():
    strs = ["flower", "flow", "flight"]
    for name, cls in IMPLS.items():
        cls().longestCommonPrefix(strs)
        assert strs == ["flower", "flow", "flight"], name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
