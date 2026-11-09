import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

# Ответ может быть не единственным: перечисляем все допустимые.
CASES = [
    ("babad", {"bab", "aba"}),
    ("cbbd", {"bb"}),
    ("a", {"a"}),
    ("ac", {"a", "c"}),
    ("racecar", {"racecar"}),
    ("forgeeksskeegfor", {"geeksskeeg"}),
    ("aaaa", {"aaaa"}),
    ("aaa", {"aaa"}),
    ("abb", {"bb"}),                  # чётный палиндром в конце
    ("bba", {"bb"}),                  # ... и в начале
    ("abcba", {"abcba"}),             # вся строка
    ("abacdfgdcaba", {"aba"}),        # ловушка «LCS с разворотом»: abacd...dcaba
    ("aaabaaaa", {"aaabaaa"}),
    ("123321x", {"123321"}),          # цифры по условию тоже бывают
    ("Aa", {"A", "a"}),               # регистр важен
]


def _is_pal(x: str) -> bool:
    return x == x[::-1]


def _best_len(s: str) -> int:
    n = len(s)
    return max(j - i for i in range(n) for j in range(i + 1, n + 1) if _is_pal(s[i:j]))


def test_examples():
    for name, cls in IMPLS.items():
        for s, expected in CASES:
            got = cls().longestPalindrome(s)
            assert got in expected, (name, s, got)


def test_random_against_brute_force():
    rng = random.Random(42)
    for _ in range(2000):
        alphabet = rng.choice(["a", "ab", "abc", "abcdefghij0123456789"])
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 25)))
        best = _best_len(s)
        for name, cls in IMPLS.items():
            got = cls().longestPalindrome(s)
            assert len(got) == best and _is_pal(got) and got in s, (name, s, got)


def test_max_size_agree():
    # n = 1000 — максимум по условию: худшие случаи для разных подходов.
    rng = random.Random(7)
    inputs = [
        "a" * 1000,                                              # ответ — вся строка
        "ab" * 500,                                              # длинный нечётный
        "".join(rng.choice("ab") for _ in range(1000)),          # много коротких
        "".join(rng.choice("abcdefghij") for _ in range(1000)),  # ответ короткий
    ]
    for s in inputs:
        ref = len(ALL["Manacher"]().longestPalindrome(s))
        for name, cls in IMPLS.items():
            got = cls().longestPalindrome(s)
            assert len(got) == ref and _is_pal(got) and got in s, (name, s[:20], len(got), ref)


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
