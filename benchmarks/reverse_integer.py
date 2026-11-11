"""uv run benchmarks/reverse_integer.py

Вход задачи ограничен (≤ 10 цифр), поэтому меряем пачку из n вызовов: [f(x) for x in xs].
Виды входа:
  random:   равномерно по [−2³¹, 2³¹ − 1] — почти все 10-значные, ~половина переполняется
  small:    |x| < 1000 — 1–3 цифры, переполнений нет
  overflow: только 10-значные x, у которых разворот не влезает — ранний выход у «32-битных»
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0007_reverse_integer"))

from alternatives import ALL, INT_MAX, INT_MIN  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}


def _fits(x):
    r = int(str(abs(x))[::-1])
    return r <= INT_MAX


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random":
            xs = [rng.randint(INT_MIN, INT_MAX) for _ in range(n)]
        elif kind == "small":
            xs = [rng.randint(-999, 999) for _ in range(n)]
        else:
            xs = []
            while len(xs) < n:
                x = rng.choice((1, -1)) * rng.randint(10**9, INT_MAX)
                if not _fits(x):
                    xs.append(x)
        return (xs,)
    return make


def batch(cls):
    f = cls().reverse
    return lambda xs: [f(x) for x in xs]


if __name__ == "__main__":
    impls = {name: batch(cls) for name, cls in CLASSES.items()}
    for kind in ["random", "small", "overflow"]:
        print(f"\n################ {kind} ################")
        bench(impls, gen(kind), [100_000], repeat=5, warmup=1)
