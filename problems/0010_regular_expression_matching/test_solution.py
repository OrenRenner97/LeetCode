import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}
FAST = {name: cls for name, cls in IMPLS.items() if name != "Backtrack"}   # Backtrack экспоненциален

CASES = [
    ("aa", "a", False), ("aa", "a*", True), ("ab", ".*", True),
    ("aab", "c*a*b", True),
    ("mississippi", "mis*is*p*.", False), ("mississippi", "mis*is*ip*.", True),
    ("a", "ab*", True),                  # хвостовой x* пустой
    ("a", ".*..a*", False),
    ("ab", ".*c", False),
    ("aaa", "a*a", True),                # звезда не должна съесть всё
    ("aaa", "ab*a*c*a", True),
    ("abcd", "d*", False),
    ("a", "a.", False),                  # '.' — ровно один символ
    ("bbbba", ".*a*a", True),
    ("a", ".", True), ("a", "b", False), ("ab", ".*b", True), ("abc", "a.c", True),
    ("aaaaaaaaaaaaaaaaaaaa", "a*", True),
    ("ab", "a*b*c*d*e*", True), ("", "a*b*", True), ("", "a", False), ("", ".", False),
]

ADVERSARIAL = ("aaaaaaaaaaaaaaaaaaab", "a*a*a*a*a*a*a*a*a*c")


def _random_pattern(rng, n):
    out = []
    while len("".join(out)) < n:
        c = rng.choice("ab.")
        out.append(c + "*" if rng.random() < 0.4 else c)
    return "".join(out)[:n].rstrip("*") or "a"


def test_examples():
    for name, cls in IMPLS.items():
        for s, p, expected in CASES:
            assert cls().isMatch(s, p) is expected, (name, s, p)


def test_adversarial():
    for name, cls in FAST.items():
        assert cls().isMatch(*ADVERSARIAL) is False, name


def test_random_against_re():
    rng = random.Random(10)
    pairs = []
    for _ in range(4000):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 12)))
        pairs.append((s, _random_pattern(rng, rng.randint(1, 12))))
    for _ in range(1000):                # совпадающие пары: строим s по шаблону
        p = _random_pattern(rng, rng.randint(1, 12))
        s = "".join(rng.choice("ab") * (rng.randint(0, 3) if star else 1)
                    if c == "." else c * (rng.randint(0, 3) if star else 1)
                    for c, star in re.findall(r"([ab.])(\*?)", p))
        pairs.append((s, p))
    for name, cls in IMPLS.items():
        f = cls().isMatch
        for s, p in pairs:
            assert f(s, p) == (re.fullmatch(p, s) is not None), (name, s, p)


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
