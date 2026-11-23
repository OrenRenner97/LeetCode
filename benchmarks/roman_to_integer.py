"""uv run benchmarks/roman_to_integer.py

Один вызов — наносекунды, поэтому меряем пакет: n строк подряд через list(map(f, strs)).
Строки собираются заново ("".join), чтобы хэш не был закэширован, как у повторно используемого объекта.
Виды входа:
  all:    случайные числа 1..3999
  long:   только MMMDCCCLXXXVIII (3888, 15 символов) — худший случай для циклов по символам
  short:  только M (1000) — один символ
  subtr:  MCMXCIV-подобные: каждый разряд — 4 или 9 (вычитательные пары везде)
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0013_roman_to_integer"))

from alternatives import ALL, _to_roman  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "all":
            nums = [rng.randint(1, 3999) for _ in range(n)]
        elif kind == "long":
            nums = [3888] * n
        elif kind == "short":
            nums = [1000] * n
        else:
            nums = [rng.choice((1, 2, 3)) * 1000 + rng.choice((4, 9)) * 100 + rng.choice((4, 9)) * 10
                    + rng.choice((4, 9)) for _ in range(n)]
        return ([("".join(list(_to_roman(x)))) for x in nums],)
    return make


def batch(cls):
    f = cls().romanToInt
    return lambda strs: list(map(f, strs))


if __name__ == "__main__":
    for kind in ["all", "long", "short", "subtr"]:
        print(f"\n################ {kind} ################")
        bench({name: batch(cls) for name, cls in CLASSES.items()}, gen(kind), [100_000], repeat=5, warmup=1)
