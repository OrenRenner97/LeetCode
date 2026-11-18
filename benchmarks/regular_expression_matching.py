"""uv run benchmarks/regular_expression_matching.py

Вход задачи маленький (|s|, |p| ≤ 20), поэтому меряем пачку вызовов [f(s, p) for s, p in pairs].
Виды входа:
  random:      случайные s над {a, b} и шаблоны из a, b, '.', 'x*' длиной ≤ 20 — почти все не совпадают, и быстро
  matching:    s построена по шаблону — совпадает, приходится дойти до конца
  adversarial: "a"·2k + "b" против "a*"·k + "c" — экспонента у перебора; Backtrack сюда не пускаем
  growth:      один adversarial-вызов при k = 6, 8, 10, 12 — как растёт время (все, кроме Backtrack)
"""
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0010_regular_expression_matching"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}


def _pattern(rng, n):
    out = ""
    while len(out) < n:
        c = rng.choice("ab.")
        out += c + "*" if rng.random() < 0.4 else c
    return out[:n].rstrip("*") or "a"


def _matching(rng, p):
    s = []
    i = 0
    while i < len(p):
        c, star = p[i], i + 1 < len(p) and p[i + 1] == "*"
        for _ in range(rng.randint(0, 3) if star else 1):
            s.append(rng.choice("ab") if c == "." else c)
        i += 2 if star else 1
    return "".join(s)[:20]


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random":
            pairs = [("".join(rng.choice("ab") for _ in range(rng.randint(1, 20))), _pattern(rng, rng.randint(1, 20)))
                     for _ in range(n)]
        elif kind == "matching":
            pairs = []
            for _ in range(n):
                p = _pattern(rng, rng.randint(1, 20))
                pairs.append((_matching(rng, p), p))
        else:
            k = 9                                          # |s| = 19, |p| = 19 — в пределах LeetCode
            pairs = [("a" * (2 * k) + "b", "a*" * k + "c")] * n
        return (pairs,)
    return make


def batch(cls):
    f = cls().isMatch
    return lambda pairs: [f(s, p) for s, p in pairs]


def growth():
    print("\n################ growth: один вызов, 'a'·2k + 'b' против 'a*'·k + 'c' ################")
    names = [name for name in CLASSES if name != "Backtrack"]
    print("   k " + "".join(f"{name:>12}" for name in names))
    for k in (6, 8, 10, 12):
        s, p = "a" * (2 * k) + "b", "a*" * k + "c"
        row = []
        for name in names:
            t = time.perf_counter()
            CLASSES[name]().isMatch(s, p)
            row.append(f"{(time.perf_counter() - t) * 1000:10.2f}ms")
        print(f"{k:4d} " + "".join(f"{r:>12}" for r in row))


if __name__ == "__main__":
    for kind, sizes in [("random", [10_000]), ("matching", [10_000]), ("adversarial", [100])]:
        impls = {name: batch(cls) for name, cls in CLASSES.items() if not (kind == "adversarial" and name == "Backtrack")}
        print(f"\n################ {kind} ################")
        bench(impls, gen(kind), sizes, repeat=5, warmup=1)
    growth()
