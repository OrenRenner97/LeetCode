"""uv run benchmarks/longest_common_prefix.py

Вход — n строк длины 200 (максимум LeetCode: n = 200; и с запасом: n = 10⁴). Виды:
  same:      все строки одинаковые — префикс = вся строка, худший случай для всех
  half:      общий префикс 100 символов + случайные 100 — расхождение в середине
  lastdiff:  все одинаковые, кроме последней: она отличается в первом символе. Ответ "", но горизонтальные
             проходы узнают об этом только в конце, а вертикальный — на первом столбце
  firstdiff: вторая строка отличается в первом символе — горизонтальные с ранним выходом выходят сразу
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0014_longest_common_prefix"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}
L = 200


def rand(rng, k):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(k))


def gen(kind):
    def make(n):
        rng = random.Random(n)
        base = rand(rng, L)
        if kind == "same":
            strs = ["".join(list(base)) for _ in range(n)]          # разные объекты с одним содержимым
        elif kind == "half":
            strs = [base[:100] + rand(rng, 100) for _ in range(n)]
        elif kind == "lastdiff":
            strs = ["".join(list(base)) for _ in range(n - 1)] + ["#" + base[1:]]
        else:
            strs = [base, "#" + base[1:]] + ["".join(list(base)) for _ in range(n - 2)]
        return (strs,)
    return make


if __name__ == "__main__":
    for kind in ["same", "half", "lastdiff", "firstdiff"]:
        print(f"\n################ {kind} ################")
        bench({name: cls().longestCommonPrefix for name, cls in CLASSES.items()}, gen(kind),
              [200, 10_000], repeat=7, warmup=1)
