"""uv run benchmarks/zigzag.py

Входы (n = длина строки, r = numRows):
  r = 2:    две длинные строки — худший случай для `+=` в Solution (каждая ~n/2)
  r = 3:    как в примере LeetCode
  r = √n:   много средних строк
  r = n/2:  почти каждая строка из 1–2 символов, период ~n

Matrix (Θ(n·r) памяти) меряется только до n = 10⁴ и не на r = n/2 при 10⁴ (5·10⁷ клеток).
"""
import random
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0006_zigzag_conversion"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}
ALPHABET = string.ascii_letters + ",."


def rows_for(kind, n):
    return {"r=2": 2, "r=3": 3, "r=sqrt": max(2, int(n ** 0.5)), "r=n/2": n // 2}[kind]


def gen(kind):
    def make(n):
        rng = random.Random(n)
        return ("".join(rng.choice(ALPHABET) for _ in range(n)), rows_for(kind, n))
    return make


if __name__ == "__main__":
    for kind in ["r=2", "r=3", "r=sqrt", "r=n/2"]:
        print(f"\n################ {kind} ################")
        for size in [1_000, 10_000, 100_000, 1_000_000]:
            names = [
                name for name in CLASSES
                if name != "Matrix" or size <= 1_000 or (size <= 10_000 and kind != "r=n/2")
            ]
            impls = {name: CLASSES[name]().convert for name in names}
            bench(impls, gen(kind), [size], repeat=3, warmup=1)
