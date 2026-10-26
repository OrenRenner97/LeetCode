"""uv run benchmarks/longest_substring.py

Входы:
  random-4:   случайная ДНК-подобная строка (ответ маленький, ~5–10)
  random-95:  случайные печатные символы (ответ ~15–20)
  cyclic-95:  printable, повторённый по кругу: ответ = 95 (худший случай для O(n·L))
"""
import random
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0003_longest_substring_without_repeating_characters"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

ALPHA = string.printable[:95]  # 95 «печатных» символов, как в условии


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random-4":
            return ("".join(rng.choice("acgt") for _ in range(n)),)
        if kind == "random-95":
            return ("".join(rng.choice(ALPHA) for _ in range(n)),)
        return ((ALPHA * (n // len(ALPHA) + 1))[:n],)
    return make


if __name__ == "__main__":
    impls = {name: cls().lengthOfLongestSubstring for name, cls in {"Solution": Solution, **ALL}.items()}
    for kind in ["random-4", "random-95", "cyclic-95"]:
        print(f"\n################ {kind} ################", end="")
        bench(impls, gen(kind), [1_000, 50_000, 1_000_000], repeat=3, warmup=1)
