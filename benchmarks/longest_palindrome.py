"""uv run benchmarks/longest_palindrome.py

Входы (n = длина строки):
  random: 62 символа (буквы + цифры), ответ длины 1–3 — типичный случай
  binary: алфавит "ab", много коротких палиндромов, ответ ~ 2 log n
  same:   "aaa...a", ответ — вся строка (худший для расширения от центра)

Сверяется длина ответа (сами палиндромы могут отличаться при равной длине).
Кубические решения меряются только до лимита LeetCode (n = 1000),
DPTable тоже (память O(n²)), расширение от центра — до 10⁴, линейные и n log n — до 10⁵.
"""
import random
import string
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0005_longest_palindromic_substring"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}
TIERS = [
    (["Solution", "LongestFirst"], [100, 1_000]),
    (["DPTable"], [100, 1_000]),  # 10⁴ — это 10⁸ клеток dp, ~800 МБ указателей
    (["ExpandAroundCenter"], [100, 1_000, 10_000]),
    (["GrowByTwo", "HashBinarySearch", "Manacher"], [100, 1_000, 10_000, 100_000]),
]


def _answer_len(fn, s):  # сверяем длину: равные по длине палиндромы могут различаться
    return len(fn(s))


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random":
            s = "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(n))
        elif kind == "binary":
            s = "".join(rng.choice("ab") for _ in range(n))
        else:
            s = "a" * n
        return (s,)
    return make


if __name__ == "__main__":
    for kind in ["random", "binary", "same"]:
        print(f"\n################ {kind} ################")
        for size in [100, 1_000, 10_000, 100_000]:
            names = [name for group, sizes in TIERS if size in sizes for name in group]
            impls = {name: partial(_answer_len, CLASSES[name]().longestPalindrome) for name in names}
            bench(impls, gen(kind), [size], repeat=3, warmup=1)
