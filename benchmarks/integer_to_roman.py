"""uv run benchmarks/integer_to_roman.py

Один вызов — наносекунды, поэтому меряем пакет: n чисел подряд через list(map(f, nums)).
Виды входа:
  all:    1..3999 по кругу — весь диапазон равномерно
  long:   только 3888 (15 символов) — худший случай для жадных по символам
  short:  только 1000 (M) — ответ из одного символа: жадный по Solution выходит сразу
  small:  1..99 — тысяч и сотен нет; UnaryReplace здесь на своём поле
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0012_integer_to_roman"))

from alternatives import ALL  # noqa: E402
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
            nums = [rng.randint(1, 99) for _ in range(n)]
        return (nums,)
    return make


def batch(cls):
    f = cls().intToRoman
    return lambda nums: list(map(f, nums))


if __name__ == "__main__":
    for kind in ["all", "long", "short", "small"]:
        print(f"\n################ {kind} ################")
        bench({name: batch(cls) for name, cls in CLASSES.items()}, gen(kind), [100_000], repeat=5, warmup=1)
