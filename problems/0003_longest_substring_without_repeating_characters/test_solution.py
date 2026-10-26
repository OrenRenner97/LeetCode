import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    ("abcabcbb", 3),
    ("bbbbb", 1),
    ("pwwkew", 3),
    ("", 0),
    ("a", 1),
    ("mq", 2),
    (" ", 1),
    ("dvdf", 3),        # после повтора левый край не должен откатиться слишком далеко
    ("abba", 2),        # левый край не должен ехать НАЗАД (ловушка для LastIndex без max)
    ("tmmzuxt", 5),     # «t» повторяется, но прошлое вхождение уже вне окна
    (string.printable, len(set(string.printable))),
]


def _brute(s):
    best = 0
    for i in range(len(s)):
        for j in range(i, len(s) + 1):
            if len(set(s[i:j])) == j - i:
                best = max(best, j - i)
    return best


def test_examples():
    for name, cls in IMPLS.items():
        for s, expected in CASES:
            assert cls().lengthOfLongestSubstring(s) == expected, (name, s)


def test_random_against_brute():
    rng = random.Random(42)
    alphabets = ["ab", "abc", "abcd", "acgt", string.ascii_lowercase, string.printable]
    for _ in range(1500):
        alpha = rng.choice(alphabets)
        s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 30)))
        expected = _brute(s)
        for name, cls in IMPLS.items():
            assert cls().lengthOfLongestSubstring(s) == expected, (name, s)


def test_long_strings_agree():
    # 5·10^4 — максимум по условию; эталон тут — LastIndex (проверен на мелких выше).
    rng = random.Random(7)
    for alpha in ["acgt", string.printable]:
        s = "".join(rng.choice(alpha) for _ in range(50_000))
        expected = ALL["LastIndex"]().lengthOfLongestSubstring(s)
        for name, cls in IMPLS.items():
            assert cls().lengthOfLongestSubstring(s) == expected, name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
